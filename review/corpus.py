#!/usr/bin/env python3
"""
M1 — Corpus builder for the MCSP knowledge network (csp-digest issue #1).

Reads review/seed_corpus.json (the ONLY place papers enter the system),
resolves every non-deferred entry against OpenAlex (bibliographic facts come
only from OpenAlex — never from a model or a hunch), downloads the best
open-access PDF into the vault's raw/ folder with an ingest-date prefix per
the vault's conventions, dedups against files already in raw/, and writes
review/corpus-manifest.json recording exactly what happened per entry.

Usage (network, no API key needed — OpenAlex is free):
    python3 review/corpus.py --dry-run          # resolve only, download nothing
    python3 review/corpus.py                    # full build
    python3 review/corpus.py --limit 5          # first 5 unprocessed entries

Env:
    VAULT_PATH        Obsidian vault root (default: ~/Documents/workspace/Code/AI_brain/Jade)
    OPENALEX_MAILTO   contact email for the OpenAlex polite pool (recommended)

Idempotent: entries already resolved+fetched in the manifest are skipped;
re-running only processes new/failed entries. Stdlib only.
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

REVIEW_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_PATH = os.path.join(REVIEW_DIR, "seed_corpus.json")
MANIFEST_PATH = os.path.join(REVIEW_DIR, "corpus-manifest.json")
DEFAULT_VAULT = os.path.expanduser("~/Documents/workspace/Code/AI_brain/Jade")
OPENALEX_WORKS = "https://api.openalex.org/works"

# ---------------------------- pure helpers (unit-tested) ----------------------------

def normalize_doi(doi: str) -> str:
    """Lowercase bare DOI: strips https://doi.org/, doi: prefixes, whitespace."""
    if not doi:
        return ""
    d = doi.strip().lower()
    for pre in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if d.startswith(pre):
            d = d[len(pre):]
    return d.strip("/ ")


def slugify(text: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:maxlen].rstrip("-") or "untitled"


_STOP = {"a", "an", "the", "of", "for", "and", "on", "in", "to", "with", "by", "using"}

def title_match_score(a: str, b: str) -> float:
    """Similarity in [0,1] between two titles: blend of Jaccard-style overlap and
    containment (overlap/min), so a seed title that is a subset of the real
    title (missing subtitle) still scores high. Tiny overlaps are floored."""
    tok = lambda t: {w for w in re.findall(r"[a-z0-9]+", (t or "").lower()) if w not in _STOP}
    ta, tb = tok(a), tok(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    if inter < 3:                       # <3 shared real words: never a confident match
        return inter / max(len(ta), len(tb)) * 0.5
    jac = inter / max(len(ta), len(tb))
    contain = inter / min(len(ta), len(tb))
    return min(1.0, max(jac, 0.92 * contain))


def sanitize_query(text: str) -> str:
    """OpenAlex `search` 400s / misbehaves on some punctuation — keep words only."""
    return re.sub(r"[^A-Za-z0-9 ]+", " ", text or "").strip()


def pick_pdf_url(work: dict) -> str | None:
    """Best OA PDF url from an OpenAlex work: best_oa_location.pdf_url, then
    any location pdf_url, then open_access.oa_url only if it ends in .pdf."""
    loc = work.get("best_oa_location") or {}
    if loc.get("pdf_url"):
        return loc["pdf_url"]
    for L in work.get("locations") or []:
        if (L or {}).get("pdf_url"):
            return L["pdf_url"]
    oa = (work.get("open_access") or {}).get("oa_url") or ""
    if oa.lower().endswith(".pdf"):
        return oa
    return None


def manifest_entry(seed: dict, work: dict | None, score: float,
                   fulltext: str, raw_file: str | None, error: str = "") -> dict:
    """One manifest record. fulltext: existing-clipping|pdf|abstract-only|none.
    Bibliographic fields come ONLY from the OpenAlex work."""
    e = {
        "slug": seed["slug"],
        "tier": seed.get("tier", "?"),
        "status": "resolved" if work else "unresolved",   # error detail lives in "error"
        # Flag for the user's audit when the seed asked for it, OR when the
        # accept was a title-search match below 0.8 (subtitle drift risk).
        "needs_confirm": bool(seed.get("confirm")) or (work is not None and not seed.get("doi") and score < 0.8),
        "match_score": round(score, 3),
        "fulltext": fulltext,
        "raw_file": raw_file,
        "error": error,
    }
    if work:
        auths = [a.get("author", {}).get("display_name", "")
                 for a in (work.get("authorships") or [])[:6]]
        e.update({
            "title": work.get("title") or "",
            "doi": normalize_doi(work.get("doi") or ""),
            "year": work.get("publication_year"),
            "venue": ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
            "citations": work.get("cited_by_count", 0),
            "authors": auths,
            "openalex_id": (work.get("id") or "").replace("https://openalex.org/", ""),
        })
    else:
        e["title"] = seed.get("title", "")
    return e


def dedup_existing(seed: dict, vault: str) -> str | None:
    """If the seed names an existing raw/ file that exists, return its path."""
    rel = seed.get("existing_raw")
    if rel and os.path.exists(os.path.join(vault, rel)):
        return rel
    return None

def _oa_auth(params: dict) -> dict:
    """OpenAlex auth: the mailto polite pool was deprecated Feb 2026 (mailto is
    now ignored); a free-account api_key gives a 10x daily budget. Keyless
    requests still work but exhaust a tiny budget fast -> 429s."""
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto        # ignored since Feb 2026; kept as harmless courtesy
    return params


# ---------------------------- network layer (injectable) ----------------------------

def _http_get(url: str, timeout: int = 60, tries: int = 3) -> bytes:
    """GET with backoff. CORPUS_PATIENT=1 turns 429 handling into a marathon:
    waits up to ~10 min between attempts and retries for a long time, so a
    single background run can sit out an IP-level OpenAlex block."""
    patient = os.environ.get("CORPUS_PATIENT") == "1"
    if patient:
        tries = max(tries, 12)
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "csp-digest-corpus/0.1 (mailto:%s)"
                                                       % os.environ.get("OPENALEX_MAILTO", "unknown")})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            if "429" in str(e):
                wait = min(600.0, 30.0 * (2 ** t)) if patient else 12.0 * (t + 1)
            else:
                wait = 1.5 * (t + 1)
            time.sleep(wait)
    raise RuntimeError(f"GET failed: {last}")


def resolve(seed: dict, fetch=None) -> tuple[dict | None, float]:
    """Resolve one seed entry to an OpenAlex work. Returns (work, match_score).
    DOI lookups are authoritative (score 1.0); title searches are scored."""
    fetch = fetch or _http_get
    sel = ("title,publication_year,doi,authorships,cited_by_count,primary_location,"
           "best_oa_location,locations,open_access,abstract_inverted_index,id")
    if seed.get("doi"):
        q = _oa_auth({"select": sel})
        url = (OPENALEX_WORKS + "/doi:" + urllib.parse.quote(normalize_doi(seed["doi"]), safe="")
               + "?" + urllib.parse.urlencode(q))
        try:
            return json.loads(fetch(url)), 1.0
        except Exception:  # noqa: BLE001 - fall through to title search
            pass
    title = seed.get("title") or ""
    want_year = seed.get("year")
    hint = sanitize_query(seed.get("authors_hint", ""))
    q_title = sanitize_query(title)

    # Three strategies, best score wins; stop early on a near-perfect hit.
    attempts = [
        {"search": f"{q_title} {hint}".strip()},
        {"search": q_title},
        {"filter": f"title.search:{q_title}"},
    ]
    best, best_score = None, 0.0
    for extra in attempts:
        params = _oa_auth({"per-page": 5, "select": sel, **extra})
        try:
            data = json.loads(fetch(OPENALEX_WORKS + "?" + urllib.parse.urlencode(params)))
        except Exception:  # noqa: BLE001 - a failing strategy just yields no candidates
            continue
        for w in data.get("results", []):
            s = title_match_score(title, w.get("title") or "")
            if want_year and w.get("publication_year"):
                s += 0.1 if abs(w["publication_year"] - want_year) <= 1 else -0.15
            if s > best_score:
                best, best_score = w, s
        if best_score >= 0.92:
            break
        time.sleep(0.25)
    return best, min(max(best_score, 0.0), 1.0)

# ---------------------------- build loop ----------------------------

MATCH_THRESHOLD = 0.55   # below this a title-search hit is too risky to accept


def build(dry_run: bool = False, limit: int = 0, fetch=None) -> dict:
    vault = os.environ.get("VAULT_PATH", DEFAULT_VAULT)
    raw_dir = os.path.join(vault, "raw")
    if not os.path.isdir(raw_dir):
        sys.exit(f"vault raw/ not found: {raw_dir} (set VAULT_PATH)")
    seeds = json.load(open(SEED_PATH))["entries"]
    manifest = {"built": None, "entries": {}}
    if os.path.exists(MANIFEST_PATH):
        manifest = json.load(open(MANIFEST_PATH))
    done = manifest["entries"]
    today = datetime.date.today().isoformat()
    processed = 0

    for seed in seeds:
        slug = seed["slug"]
        if seed.get("deferred"):
            done[slug] = {"slug": slug, "tier": seed.get("tier", "?"), "status": "deferred",
                          "note": seed.get("note", ""), "fulltext": "none", "raw_file": None}
            continue
        prev = done.get(slug)
        if prev and prev.get("status") == "resolved" and prev.get("fulltext") in ("pdf", "existing-clipping"):
            continue                                    # idempotent skip
        if limit and processed >= limit:
            continue
        processed += 1

        # Retry path: resolved earlier (dry-run or a failed download) — use the
        # STORED metadata + pdf_url; never re-query OpenAlex for it.
        if prev and prev.get("status") == "resolved":
            url = prev.get("pdf_url")
            if url and not dry_run:
                try:
                    blob = (fetch or _http_get)(url, timeout=120)
                    if blob[:4] == b"%PDF":
                        fname = f"{today}_{slugify(prev.get('title') or slug)}.pdf"
                        with open(os.path.join(raw_dir, fname), "wb") as f:
                            f.write(blob)
                        prev["fulltext"], prev["raw_file"] = "pdf", f"raw/{fname}"
                        print(f"  ↓ {slug}: downloaded via stored pdf_url")
                    else:
                        prev["fulltext"] = "abstract-only"
                        print(f"  - {slug}: stored url was not a PDF -> abstract-only")
                except Exception as e:  # noqa: BLE001
                    prev["fulltext"] = "abstract-only"
                    print(f"    (pdf retry failed for {slug}: {e})", file=sys.stderr)
                time.sleep(1.0)
            done[slug] = prev
            continue

        existing = dedup_existing(seed, vault)
        try:
            work, score = resolve(seed, fetch=fetch)
        except Exception as e:  # noqa: BLE001
            done[slug] = manifest_entry(seed, None, 0.0, "none", existing, error=str(e)[:200])
            print(f"  ✗ {slug}: resolve error: {e}", file=sys.stderr)
            continue
        if work is None or (not seed.get("doi") and score < MATCH_THRESHOLD):
            done[slug] = manifest_entry(seed, None, score, "none", existing,
                                        error=f"no confident OpenAlex match (score {score:.2f})")
            print(f"  ? {slug}: UNRESOLVED (best score {score:.2f})")
            continue

        if existing:
            done[slug] = manifest_entry(seed, work, score, "existing-clipping", existing)
            print(f"  = {slug}: dedup -> {existing}")
        else:
            pdf = pick_pdf_url(work)
            raw_rel = None
            fulltext = "abstract-only"
            if pdf and not dry_run:
                fname = f"{today}_{slugify(work.get('title') or slug)}.pdf"
                dest = os.path.join(raw_dir, fname)
                try:
                    blob = (fetch or _http_get)(pdf, timeout=120)
                    if blob[:4] == b"%PDF":
                        with open(dest, "wb") as f:
                            f.write(blob)
                        raw_rel, fulltext = f"raw/{fname}", "pdf"
                    else:
                        fulltext = "abstract-only"      # landing page, not a PDF
                except Exception as e:  # noqa: BLE001
                    print(f"    (pdf fetch failed for {slug}: {e})", file=sys.stderr)
            elif pdf and dry_run:
                fulltext = "pdf(pending)"
            rec = manifest_entry(seed, work, score, fulltext, raw_rel)
            rec["pdf_url"] = pdf                        # stored so retries skip OpenAlex
            done[slug] = rec
            flag = " [CONFIRM]" if seed.get("confirm") else ""
            print(f"  ✓ {slug}: {work.get('publication_year')} score={score:.2f} "
                  f"{fulltext}{flag}  {(work.get('title') or '')[:60]}")
        # Persist after EVERY entry: a killed run keeps all completed work.
        manifest["built"] = today
        manifest["entries"] = done
        json.dump(manifest, open(MANIFEST_PATH, "w"), indent=1)
        time.sleep(0.4)                                 # be polite to OpenAlex

    manifest["built"] = today
    manifest["entries"] = done
    # Persist on dry-run too: resolutions are expensive (rate limits) and a
    # later full run reuses them instead of re-querying OpenAlex.
    json.dump(manifest, open(MANIFEST_PATH, "w"), indent=1)
    # summary
    st = [e.get("status") for e in done.values()]
    ft = [e.get("fulltext") for e in done.values()]
    print(f"\n[corpus] entries: {len(done)}  resolved: {st.count('resolved')}  "
          f"unresolved: {st.count('unresolved') + st.count('error')}  deferred: {st.count('deferred')}")
    print(f"[corpus] fulltext — pdf: {ft.count('pdf')}  existing: {ft.count('existing-clipping')}  "
          f"abstract-only: {ft.count('abstract-only')}  pending: {ft.count('pdf(pending)')}")
    print(f"[corpus] manifest -> {MANIFEST_PATH}")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="resolve only; no downloads, no manifest write")
    p.add_argument("--limit", type=int, default=0, help="process at most N unfinished entries")
    a = p.parse_args()
    build(dry_run=a.dry_run, limit=a.limit)
