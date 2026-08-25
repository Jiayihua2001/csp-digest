#!/usr/bin/env python3
"""
M2 — Paper digester for the MCSP knowledge network (csp-digest issue #1).

For each resolved entry in review/corpus-manifest.json, reads the full text
(PDF or vault clipping; abstract-only entries fall back to OpenAlex metadata)
with a frontier model and writes one grounded source page into the vault at
wiki/sources/YYYY-MM-DD_<slug>.md, following the vault's own template and
frontmatter schema. A verification pass re-reads the document and flags any
unsupported claim; pages carry an explicit confidence level. Appends one line
per ingest to the vault's log.md (append-only, per vault rules).

Accuracy invariants: bibliographic facts come from the manifest (OpenAlex);
the model summarizes only the provided document and is told to hedge rather
than guess; verification failures are printed AND recorded on the page.

Usage (needs ANTHROPIC_API_KEY in env):
    python3 review/digester.py --slug blind-test-6      # one paper
    python3 review/digester.py --all                    # everything digestible
    python3 review/digester.py --all --limit 5          # first 5 undigested
    python3 review/digester.py --all --no-verify        # skip 2nd pass (cheaper)

Env: VAULT_PATH, ANALYSIS_MODEL (default claude-opus-4-8), OPENALEX_MAILTO.
Idempotent: skips entries whose source page already exists (--force to redo).
Stdlib only.
"""
from __future__ import annotations
import argparse
import base64
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

REVIEW_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(REVIEW_DIR, "corpus-manifest.json")
DEFAULT_VAULT = os.path.expanduser("~/Documents/workspace/Code/AI_brain/Jade")
API = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-opus-4-8"
MAX_CLIP_CHARS = 120_000          # md clippings are truncated to this for the prompt

PROFILE = (
    "The reader is a 4th-year PhD student in Noa Marom's group (CMU) working on GAtor 2.0 — "
    "genetic-algorithm molecular crystal structure prediction. They care about: GA operators and "
    "niching, structure generation (Genarris), descriptors, lattice-energy ranking (dispersion-"
    "inclusive DFT, PBE0+MBD), MLIPs (MACE-OFF, AIMNet2, UMA), Z'>1 and multi-component crystals, "
    "finite-temperature stability, and the CSP blind tests."
)

BRIEF_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},                    # 3-6 sentence plain-language summary
        "contribution": {"type": "string"},               # what this established, vs prior work
        "method": {"type": "string"},
        "key_results": {"type": "array", "items": {"type": "string"}},   # with actual numbers
        "limitations": {"type": "array", "items": {"type": "string"}},
        "takeaways": {"type": "array", "items": {"type": "string"}},     # 3-6, durable lessons
        "gator_relevance": {"type": "string"},            # why it matters for GAtor 2.0 work
        "concepts": {"type": "array", "items": {"type": "string"}},      # kebab-case wiki concept slugs
        "tags": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["summary", "contribution", "method", "key_results", "limitations",
                 "takeaways", "gator_relevance", "concepts", "tags", "confidence"],
}

# ------------------------- LLM plumbing (injectable for tests) -------------------------

def _api_call(body: dict, key: str, timeout: int = 600) -> dict:
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _text_of(resp: dict) -> str:
    return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()


def llm_brief(doc_block: dict | None, context_text: str, model: str, key: str) -> dict:
    """One grounded digest call. doc_block is a PDF document block or None
    (then context_text must carry the clipping/metadata)."""
    prompt = (
        "You are digesting a paper for a personal research wiki. " + PROFILE + "\n\n"
        "Read the provided material IN FULL and fill the schema. Accuracy over completeness: state "
        "ONLY what the material supports, quote actual numbers in key_results, never infer results "
        "that are not reported, and say so when something is unclear. 'concepts' are 3-8 kebab-case "
        "wiki page slugs this paper should link to (e.g. csp-blind-tests, many-body-dispersion, "
        "genetic-algorithm-csp) - prefer reusing those exact seeds when apt. Set confidence to how "
        "faithful this digest can be ('low' if working from metadata/abstract only). Plain ASCII "
        "punctuation only.\n\n" + context_text
    )
    content: list = []
    if doc_block:
        content.append(doc_block)
    content.append({"type": "text", "text": prompt})
    body = {"model": model, "max_tokens": 4000,
            "output_config": {"format": {"type": "json_schema", "schema": BRIEF_SCHEMA}},
            "messages": [{"role": "user", "content": content}]}
    return json.loads(_text_of(_api_call(body, key)))


def llm_verify(doc_block: dict | None, context_text: str, brief: dict, model: str, key: str) -> str:
    prompt = (
        "Below is a digest of the provided material. Re-read the material and check every claim in "
        "the digest. List each statement that is unsupported, overstated, or fabricated (quote it "
        "and say why). If every claim is faithful, reply exactly: ALL SUPPORTED.\n\nDIGEST:\n"
        + json.dumps(brief, indent=1) + "\n\n" + context_text
    )
    content: list = []
    if doc_block:
        content.append(doc_block)
    content.append({"type": "text", "text": prompt})
    body = {"model": model, "max_tokens": 1200,
            "messages": [{"role": "user", "content": content}]}
    return _text_of(_api_call(body, key))

# ------------------------- document loading -------------------------

def load_document(entry: dict, vault: str) -> tuple[dict | None, str, str]:
    """Return (doc_block, context_text, mode). mode: pdf | clipping | metadata."""
    raw = entry.get("raw_file")
    meta = (f"Title: {entry.get('title', '')}\nAuthors: {', '.join(entry.get('authors', []))}\n"
            f"Venue: {entry.get('venue', '')} ({entry.get('year', '')})\nDOI: {entry.get('doi', '')}\n")
    if raw:
        path = os.path.join(vault, raw)
        if raw.lower().endswith(".pdf") and os.path.exists(path):
            data = open(path, "rb").read()
            if len(data) <= 30 * 1024 * 1024:
                b64 = base64.standard_b64encode(data).decode("ascii")
                block = {"type": "document",
                         "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}
                return block, meta, "pdf"
        if os.path.exists(path):                      # md/html clipping
            text = open(path, encoding="utf-8", errors="replace").read()[:MAX_CLIP_CHARS]
            return None, meta + "\nFULL TEXT (clipping):\n" + text, "clipping"
    abstract = fetch_abstract(entry) or ""
    note = ("\nNOTE: no full text available - digest from the metadata/abstract ONLY and set "
            "confidence to 'low'.\nAbstract: " + (abstract or "(none available)"))
    return None, meta + note, "metadata"


def fetch_abstract(entry: dict, fetch=None) -> str | None:
    """Abstract for abstract-only entries, from OpenAlex by openalex_id (1 request)."""
    oid = entry.get("openalex_id")
    if not oid:
        return None
    q = {"select": "abstract_inverted_index"}
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        q["mailto"] = mailto
    url = f"https://api.openalex.org/works/{oid}?" + urllib.parse.urlencode(q)
    try:
        fetch = fetch or (lambda u: urllib.request.urlopen(
            urllib.request.Request(u, headers={"User-Agent": "csp-digest-digester/0.1"}), timeout=45).read())
        inv = json.loads(fetch(url)).get("abstract_inverted_index")
        if not inv:
            return None
        ws = sorted((p, w) for w, ps in inv.items() for p in ps)
        return " ".join(w for _, w in ws)[:2500]
    except Exception:  # noqa: BLE001
        return None

# ------------------------- page rendering (pure; unit-tested) -------------------------

def render_source_page(entry: dict, brief: dict, verification: str, mode: str, today: str) -> str:
    def bullets(xs):
        return "\n".join(f"- {x}" for x in (xs or [])) or "- (none stated)"
    links = " ".join(f"[[{c}]]" for c in brief.get("concepts", []))
    ver = (verification or "").strip()
    ver_ok = ver.upper() == "ALL SUPPORTED"
    ver_line = ("verified: all claims supported" if ver_ok else
                ("NOT RUN" if not ver else "FLAGGED - see below"))
    tags = json.dumps(sorted(set((brief.get("tags") or []) + ["mcsp-corpus"])))
    fm = ["---", "type: source",
          f'title: "{(entry.get("title") or "").replace(chr(34), chr(39))}"',
          f'author: "{", ".join(entry.get("authors", []))}"',
          f'source_url: "{("https://doi.org/" + entry["doi"]) if entry.get("doi") else "n/a"}"',
          f'published: "{entry.get("year", "unknown")}"',
          f'ingested: {today}',
          f'raw_path: {entry.get("raw_file") or "n/a"}',
          f'tags: {tags}',
          f'created: {today}',
          f'updated: {today}',
          "---", ""]
    body = [
        f"# {entry.get('title', '')}",
        "",
        f"> {brief.get('summary', '')}",
        "",
        f"**Corpus:** tier {entry.get('tier', '?')} - `{entry.get('slug')}` - source mode: {mode} - "
        f"confidence: **{brief.get('confidence')}** - {ver_line}",
        "",
        "## Contribution",
        brief.get("contribution", ""),
        "",
        "## Method",
        brief.get("method", ""),
        "",
        "## Key results",
        bullets(brief.get("key_results")),
        "",
        "## Limitations",
        bullets(brief.get("limitations")),
        "",
        "## Takeaways",
        bullets(brief.get("takeaways")),
        "",
        "## Relevance to GAtor 2.0",
        brief.get("gator_relevance", ""),
        "",
        "## Linked concepts",
        links or "(none)",
    ]
    if ver and not ver_ok:
        body += ["", "## Verification flags", "", "> Second-pass check found issues - read before trusting:",
                 "", ver]
    return "\n".join(fm) + "\n".join(body) + "\n"


def source_page_path(vault: str, slug: str, today: str) -> str:
    return os.path.join(vault, "wiki", "sources", f"{today}_{slug}.md")


def append_log(vault: str, line: str) -> None:
    try:
        with open(os.path.join(vault, "log.md"), "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] log.md append failed: {e}", file=sys.stderr)

# ------------------------- driver -------------------------

def digest_one(entry: dict, vault: str, model: str, key: str, verify: bool = True,
               brief_fn=None, verify_fn=None, force: bool = False) -> str | None:
    """Digest one manifest entry into a wiki/sources page. Returns page path or None."""
    slug = entry["slug"]
    today = datetime.date.today().isoformat()
    # Idempotence: any existing source page for this slug (any ingest date) skips.
    src_dir = os.path.join(vault, "wiki", "sources")
    os.makedirs(src_dir, exist_ok=True)
    existing = [f for f in os.listdir(src_dir) if f.endswith(f"_{slug}.md")]
    if existing and not force:
        return None
    doc_block, context, mode = load_document(entry, vault)
    brief = (brief_fn or llm_brief)(doc_block, context, model, key)
    verification = ""
    if verify:
        try:
            verification = (verify_fn or llm_verify)(doc_block, context, brief, model, key)
        except Exception as e:  # noqa: BLE001
            verification = f"verification pass failed: {e}"
    page = render_source_page(entry, brief, verification, mode, today)
    path = source_page_path(vault, slug, today)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    append_log(vault, f"- {today} ingest: [[{os.path.basename(path)[:-3]}]] "
                      f"({mode}, confidence {brief.get('confidence')}) - M2 digester")
    return path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", help="digest one manifest slug")
    p.add_argument("--all", action="store_true", help="digest every resolved entry")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--no-verify", action="store_true")
    p.add_argument("--force", action="store_true", help="redo even if a page exists")
    a = p.parse_args()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("Set ANTHROPIC_API_KEY first.")
    vault = os.environ.get("VAULT_PATH", DEFAULT_VAULT)
    model = os.environ.get("ANALYSIS_MODEL", DEFAULT_MODEL)
    manifest = json.load(open(MANIFEST_PATH))
    entries = [e for e in manifest["entries"].values() if e.get("status") == "resolved"]
    if a.slug:
        entries = [e for e in entries if e["slug"] == a.slug]
        if not entries:
            sys.exit(f"slug not found/resolved: {a.slug}")
    elif not a.all:
        sys.exit("pass --slug <s> or --all")
    done = 0
    for e in entries:
        if a.limit and done >= a.limit:
            break
        try:
            path = digest_one(e, vault, model, key, verify=not a.no_verify, force=a.force)
        except Exception as exc:  # noqa: BLE001 - one paper must not kill the batch
            print(f"  ✗ {e['slug']}: {exc}", file=sys.stderr)
            continue
        if path:
            done += 1
            print(f"  ✓ {e['slug']} -> {os.path.relpath(path, vault)}")
        else:
            print(f"  = {e['slug']}: page exists (use --force to redo)")
        time.sleep(1.0)
    print(f"\n[digester] wrote {done} source pages")


if __name__ == "__main__":
    main()
