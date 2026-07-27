#!/usr/bin/env python3
"""
Classic of the day for csp-digest.

Recommends one real, foundational CSP paper each run to build up knowledge of the
field's canon (and to give quiet days something worth reading). Mines a pool of
well-cited, established molecular-CSP papers from OpenAlex (real DOIs/metadata),
skips ones already shown (a committed state file under site/data), and has a
frontier model pick + explain the single most foundational unseen one for the
user's focus. The paper is always a real OpenAlex record: the model only picks
from the pool and explains it, so it cannot fabricate a citation. Never raises.

Runnable standalone to preview a pick:
    ANTHROPIC_API_KEY=... OPENALEX_MAILTO=you@cmu.edu python3 classic.py

Stdlib only.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

try:
    from analysis import PROFILE
except Exception:  # noqa: BLE001
    PROFILE = "Molecular crystal structure prediction with genetic-algorithm / evolutionary methods."

MODEL_DEFAULT = "claude-opus-4-8"
SEEN_PATH = os.path.join("site", "data", "classics_seen.json")

POOL_QUERIES = [
    "molecular crystal structure prediction",
    "organic crystal polymorph prediction",
    "crystal energy landscape",
    "lattice energy ranking polymorph",
    "genetic algorithm crystal structure prediction",
]
ESTABLISHED_BEFORE = "2024-01-01"     # "core/old": established, not this year's preprints
MIN_CITATIONS = 40

# Citation-sorted keyword search pulls high-cited OFF-TOPIC hits (gold nanoclusters,
# cardiology, electrophysiology that merely match a word). Keep only papers with a
# real crystal/CSP signal and no clearly-unrelated bio/medical signal.
_CSP_OK = re.compile(
    r"crystal structure prediction|polymorph|lattice energ|energy landscape|space group|"
    r"crystal engineering|molecular crystal|organic (?:crystal|solid)|cocrystal|co-crystal|"
    r"USPEX|CALYPSO|evolutionary algorithm|genetic algorithm|structure prediction", re.I)
_CSP_NEG = re.compile(
    r"coronary|heart disease|ionic current|electrophysiolog|\bneuron|receptor|clinical|patient|"
    r"protein folding|nanocluster|thiol-protected|\bAu\d", re.I)


def _relevant(title: str, abstract: str) -> bool:
    text = f"{title} {abstract}"
    return bool(_CSP_OK.search(text)) and not _CSP_NEG.search(text)


def _get(url: str, tries: int = 4) -> bytes:
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "csp-digest-classic/0.1"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (t + 1))
    raise RuntimeError(f"GET failed: {last}")


def _abstract(inv: dict) -> str:
    if not inv:
        return ""
    ws = []
    for w, ps in inv.items():
        for p in ps:
            ws.append((p, w))
    ws.sort()
    return " ".join(w for _, w in ws)[:500]


def mine_pool() -> list:
    mailto = os.environ.get("OPENALEX_MAILTO")
    pool = {}
    for q in POOL_QUERIES:
        filt = (f"title_and_abstract.search:{q},type:article,"
                f"to_publication_date:{ESTABLISHED_BEFORE},cited_by_count:>{MIN_CITATIONS}")
        params = {"filter": filt, "sort": "cited_by_count:desc", "per-page": 40,
                  "select": "title,publication_year,doi,authorships,cited_by_count,abstract_inverted_index"}
        if mailto:
            params["mailto"] = mailto
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
        try:
            data = json.loads(_get(url))
        except Exception as e:  # noqa: BLE001
            print(f"[warn] classic pool query '{q}': {e}", file=sys.stderr)
            continue
        for w in data.get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            if not doi or doi in pool:
                continue
            title = w.get("title") or ""
            abstract = _abstract(w.get("abstract_inverted_index"))
            if not _relevant(title, abstract):
                continue
            pool[doi] = {
                "doi": doi, "title": title, "year": w.get("publication_year"),
                "citations": w.get("cited_by_count", 0),
                "authors": [a["author"]["display_name"] for a in w.get("authorships", [])[:3]],
                "abstract": abstract,
            }
    return sorted(pool.values(), key=lambda x: x["citations"], reverse=True)


_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "chosen_doi": {"type": "string"},
        "why_foundational": {"type": "string"},
        "how_it_connects": {"type": "string"},
        "what_to_take_away": {"type": "string"},
    },
    "required": ["chosen_doi", "why_foundational", "how_it_connects", "what_to_take_away"],
}


def _pick(cands: list, model: str, key: str) -> dict:
    listing = "\n".join(
        f'{i + 1}. doi={c["doi"]} ({c["year"]}, {c["citations"]} cites) {c["title"]}\n   {c["abstract"][:280]}'
        for i, c in enumerate(cands[:50]))
    prompt = (
        "You help a researcher build a mental map of crystal structure prediction (CSP). Profile:\n"
        + PROFILE + "\n\nBelow are REAL, established, well-cited CSP papers from OpenAlex. Pick the SINGLE "
        "most foundational one for this researcher to read to build core knowledge — a genuine cornerstone "
        "(landmark method, benchmark/blind test, or defining review), not a narrow application. Return its "
        "exact 'chosen_doi' FROM THE LIST (never invent a DOI). Then, grounded ONLY in the title/abstract "
        "shown, write why_foundational, how_it_connects (to modern CSP, GA/evolutionary methods, current "
        "work), and what_to_take_away (the one idea to internalize). Be accurate; do not assert results the "
        "abstract doesn't state. Use plain ASCII punctuation only (no em-dashes or smart quotes)."
        "\n\nPAPERS:\n" + listing
    )
    body = {"model": model, "max_tokens": 1500,
            "output_config": {"format": {"type": "json_schema", "schema": _SCHEMA}},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    txt = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()
    return json.loads(txt)


def _load_seen(path: str) -> list:
    try:
        return json.load(open(path))
    except Exception:  # noqa: BLE001
        return []


def _save_seen(path: str, dois: set) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(sorted(dois), open(path, "w"), indent=1)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] could not write {path}: {e}", file=sys.stderr)


def classic_of_the_day(seen_path: str = SEEN_PATH, model: str | None = None) -> dict | None:
    """Pick one foundational CSP paper not shown before; returns a dict or None."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    model = model or os.environ.get("ANALYSIS_MODEL", MODEL_DEFAULT)
    try:
        seen = set(_load_seen(seen_path))
        pool = mine_pool()
        cands = [c for c in pool if c["doi"] not in seen]
        if not cands:
            return None
        sel = _pick(cands, model, key)
        chosen = {c["doi"]: c for c in cands}.get(sel.get("chosen_doi")) or cands[0]
        _save_seen(seen_path, seen | {chosen["doi"]})
        return {
            **chosen,
            "url": f"https://doi.org/{chosen['doi']}",
            "why_foundational": sel["why_foundational"],
            "how_it_connects": sel["how_it_connects"],
            "what_to_take_away": sel["what_to_take_away"],
        }
    except Exception as e:  # noqa: BLE001 - never break the digest
        print(f"[warn] classic_of_the_day: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    c = classic_of_the_day(seen_path=os.environ.get("SEEN_PATH", "classics_seen.json"))
    print(json.dumps(c, indent=2, ensure_ascii=False) if c else "no classic produced")
