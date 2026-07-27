#!/usr/bin/env python3
"""
Weekly editorial synthesis for csp-digest (Tier 2 #4).

Reads the digest's accumulated site/data/*.json and asks a frontier model one
question: of everything this week, what should I read first? Returns a ranked
read-first list plus real recurring themes, grounded strictly in the provided
papers (told not to invent findings). Accuracy note: this works off the digest's
abstracts, so it is a fast bird's-eye triage; the accurate per-paper verdict
comes from analysis.py, which reads the full PDF.

Run from the repo dir, key in your env (never in chat):
    ANTHROPIC_API_KEY=sk-ant-... python3 weekly.py [days]

Stdlib only. ANALYSIS_MODEL=claude-fable-5 for the most capable synthesis.
"""
import glob
import json
import os
import sys
import urllib.request

try:
    from analysis import PROFILE
except Exception:  # noqa: BLE001 - keep runnable even if imported oddly
    PROFILE = "Molecular crystal structure prediction with genetic-algorithm / evolutionary methods."

KEY = os.environ.get("ANTHROPIC_API_KEY")
if not KEY:
    sys.exit("Set ANTHROPIC_API_KEY in your environment first.")

MODEL = os.environ.get("ANALYSIS_MODEL", "claude-opus-4-8")
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 7

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "read_first": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "venue": {"type": "string"},
                    "why_it_matters_to_you": {"type": "string"},
                    "relevance_score": {"type": "integer"},
                },
                "required": ["title", "venue", "why_it_matters_to_you", "relevance_score"],
            },
        },
        "themes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "theme": {"type": "string"},
                    "papers": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["theme", "papers"],
            },
        },
        "week_note": {"type": "string"},
    },
    "required": ["read_first", "themes", "week_note"],
}


def items_from(path: str) -> list:
    try:
        d = json.load(open(path))
    except Exception:  # noqa: BLE001
        return []
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        if isinstance(d.get("items"), list):
            return d["items"]
        for v in d.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def gather() -> list:
    files = sorted(f for f in glob.glob("site/data/*.json") if not f.endswith("index.json"))[-DAYS:]
    seen, papers = set(), []
    for f in files:
        for it in items_from(f):
            k = it.get("doi") or it.get("arxiv_id") or it.get("title")
            if not k or k in seen:
                continue
            seen.add(k)
            papers.append({
                "title": it.get("title", ""),
                "venue": it.get("venue", it.get("src", "")),
                "authors": (it.get("authors") or [])[:3],
                "relevance": it.get("relevance", it.get("score", 0)),
                "tags": it.get("tags", []),
                "abstract": (it.get("abstract") or "")[:600],
            })
    papers.sort(key=lambda p: p.get("relevance", 0), reverse=True)
    return papers[:40]


def synthesize(papers: list) -> dict:
    prompt = (
        "You brief a researcher with this profile:\n" + PROFILE + "\n\n"
        "Below is JSON for the papers this digest collected. Produce a synthesis whose job is to tell "
        "the reader WHAT TO READ FIRST. Accuracy rules: use ONLY the titles/abstracts provided (do not "
        "invent results); rank 'read_first' strictly by importance to the profile, most important "
        "first, omitting clearly off-topic ones; group only real recurring themes (don't manufacture a "
        "trend from one paper); if the set is thin or off-topic, say so plainly in 'week_note'.\n\n"
        "PAPERS:\n" + json.dumps(papers, ensure_ascii=False)
    )
    body = {"model": MODEL, "max_tokens": 3000,
            "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read())
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()
    return json.loads(text)


def main() -> None:
    papers = gather()
    if not papers:
        sys.exit("No papers in site/data/*.json — run the digest first, or widen: python3 weekly.py 30")
    print(f"Synthesizing {len(papers)} papers from the last {DAYS} day-files with {MODEL} ...\n")
    out = synthesize(papers)
    print("================  READ FIRST  ================")
    for n, p in enumerate(out.get("read_first", []), 1):
        print(f"\n{n}. [{p.get('relevance_score')}] {p.get('title')}  ({p.get('venue')})")
        print(f"   {p.get('why_it_matters_to_you')}")
    print("\n================  THEMES  ================")
    for t in out.get("themes", []):
        print(f"\n- {t.get('theme')}")
        for title in t.get("papers", []):
            print(f"    · {title}")
    print("\n================  NOTE  ================")
    print(out.get("week_note", ""))


if __name__ == "__main__":
    main()
