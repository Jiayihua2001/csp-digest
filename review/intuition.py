#!/usr/bin/env python3
"""
Intuition of the day — build a personal MCSP intuition handbook, one paper a day.

Each run picks ONE unprocessed corpus paper (full-text sources first), reads it
with a frontier model, and extracts durable intuition chunks: field statistics
(with numbers and scope), principles, decision rules, standard-pipeline
practices, and pitfalls. Every chunk carries supporting evidence from the paper
and a generality grade, so a single-system observation can never masquerade as
a universal law. Records accumulate in review/intuition.json and render into:

  vault wiki/syntheses/mcsp-intuition-handbook.md   (wikilinked handbook)
  site/intuition.html                                (today's paper + handbook)

Usage:
    python3 review/intuition.py --daily          # process next paper + render
    python3 review/intuition.py --slug gator-2018
    python3 review/intuition.py --render-only    # re-render, no LLM

Env: ANTHROPIC_API_KEY (required unless --render-only), VAULT_PATH,
INTUITION_MODEL (default claude-opus-4-8). Stdlib only. Never raises past main.
"""
from __future__ import annotations
import argparse
import datetime
import html as _html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digester import (_api_call, _text_of, load_document, DEFAULT_VAULT,  # noqa: E402
                      PROFILE, append_log)

REVIEW_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(REVIEW_DIR)
MANIFEST_PATH = os.path.join(REVIEW_DIR, "corpus-manifest.json")
DB_PATH = os.path.join(REVIEW_DIR, "intuition.json")
DEFAULT_MODEL = "claude-opus-4-8"

CHUNK_TYPES = ["statistic", "principle", "decision_rule", "pipeline_practice", "pitfall"]
TYPE_TITLES = {
    "statistic": "Field statistics & magic numbers",
    "principle": "Principles",
    "decision_rule": "Decision rules (when to use what)",
    "pipeline_practice": "Standard pipeline practices",
    "pitfall": "Pitfalls",
}

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "core_idea": {"type": "string"},
        "innovation": {"type": "string"},
        "chunks": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "type": {"type": "string", "enum": CHUNK_TYPES},
                "statement": {"type": "string"},   # the standalone intuition
                "scope": {"type": "string"},       # systems/conditions it applies to
                "evidence": {"type": "string"},    # supporting numbers/passage from THE paper
                "generality": {"type": "string", "enum": ["established", "suggested", "single-study"]},
            },
            "required": ["type", "statement", "scope", "evidence", "generality"],
        }},
        "synthesis": {"type": "string"},           # assistant's interpretation, labeled as such
    },
    "required": ["core_idea", "innovation", "chunks", "synthesis"],
}

PROMPT = (
    "You are building a personal INTUITION HANDBOOK for this researcher:\n" + PROFILE + "\n\n"
    "Read the provided paper material IN FULL and extract every durable intuition a practitioner "
    "should internalize - the things people forget after reading:\n"
    "  statistic: field numbers with their magnitude (e.g. 'polymorph energy differences are "
    "usually < ~7 kJ/mol, most < 2 kJ/mol')\n"
    "  principle: why-it-works truths about the physics or the search problem\n"
    "  decision_rule: when to use a method (e.g. when finite-temperature free energies change "
    "rankings, when conformer energy corrections are required)\n"
    "  pipeline_practice: what standard workflows actually do and in what order\n"
    "  pitfall: common ways results mislead\n\n"
    "Accuracy rules (this handbook informs real research decisions):\n"
    "- Every chunk must be supported by the provided material; put the supporting numbers or a "
    "tight paraphrase of the passage in 'evidence'. Never import numbers from memory.\n"
    "- 'scope' must state what systems/conditions the claim covers (e.g. 'rigid small organics, "
    "Z'=1'); never widen beyond what the paper shows.\n"
    "- 'generality': established (field-consensus statement or large-sample statistic), suggested "
    "(supported trend), single-study (one system/dataset - interesting but unproven).\n"
    "- 3-10 chunks; quality over quantity. If the material is abstract-only, extract only what it "
    "truly supports.\n"
    "- 'synthesis' is YOUR OWN interpretation - connect the paper's lesson to genetic-algorithm "
    "MCSP practice (GAtor 2.0); it will be displayed clearly labeled as assistant interpretation.\n"
    "- core_idea: 2-3 sentences; innovation: what was new vs prior work. Plain ASCII."
)


# ------------------------------- extraction -------------------------------

def load_db() -> dict:
    try:
        return json.load(open(DB_PATH))
    except Exception:  # noqa: BLE001
        return {"records": []}


def pick_next(manifest: dict, db: dict) -> dict | None:
    """Next unprocessed resolved paper; full-text sources first, manifest order."""
    done = {r["slug"] for r in db.get("records", [])}
    resolved = [e for e in manifest.values() if e.get("status") == "resolved" and e["slug"] not in done]
    fulltext = [e for e in resolved if e.get("fulltext") in ("pdf", "existing-clipping")]
    return (fulltext or resolved or [None])[0]


def extract(entry: dict, vault: str, model: str, key: str, api=None) -> dict:
    doc_block, context, mode = load_document(entry, vault)
    content: list = []
    if doc_block:
        content.append(doc_block)
    content.append({"type": "text", "text": PROMPT + "\n\n" + context})
    body = {"model": model, "max_tokens": 4000,
            "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
            "messages": [{"role": "user", "content": content}]}
    data = json.loads(_text_of((api or _api_call)(body, key)))
    return {
        "slug": entry["slug"], "title": entry.get("title", ""), "doi": entry.get("doi"),
        "year": entry.get("year"), "tier": entry.get("tier"),
        "source_mode": mode, "date": datetime.date.today().isoformat(),
        **data,
    }


# ------------------------------- renderers (pure) -------------------------------

def _chunk_md(c: dict, rec: dict, page_name: str | None) -> str:
    src = f"[[{page_name}|{rec['title'][:60]}]]" if page_name else rec["title"][:60]
    doi = f" ([doi](https://doi.org/{rec['doi']}))" if rec.get("doi") else ""
    flag = "" if rec.get("source_mode") in ("pdf", "clipping") else " *(abstract-only source)*"
    return (f"- **{c['statement']}**\n"
            f"    - scope: {c['scope']}  |  generality: *{c['generality']}*{flag}\n"
            f"    - evidence: {c['evidence']}\n"
            f"    - source: {src}{doi}")


def render_vault_page(db: dict, pages: dict, today: str) -> str:
    lines = ["---", "type: synthesis", 'title: "MCSP intuition handbook"',
             "tags: [\"mcsp-corpus\", \"intuition\"]", f"created: {today}", f"updated: {today}",
             "---", "", "# MCSP intuition handbook", "",
             "> Durable statistics, principles, decision rules, pipeline practices, and pitfalls - "
             "extracted one paper a day, each chunk cited to its source. Trust 'established' most; "
             "treat 'single-study' as a hypothesis.", ""]
    recs = db.get("records", [])
    for t in CHUNK_TYPES:
        rows = []
        for rec in recs:
            pn = pages.get(rec["slug"], (None,))[0] if isinstance(pages.get(rec["slug"]), tuple) \
                 else pages.get(rec["slug"])
            for c in rec.get("chunks", []):
                if c.get("type") == t:
                    rows.append(_chunk_md(c, rec, pn))
        if rows:
            lines += [f"## {TYPE_TITLES[t]}", ""] + rows + [""]
    lines += ["## Paper syntheses (assistant interpretation)", ""]
    for rec in recs:
        lines += [f"**{rec['title'][:70]}** ({rec.get('year','')}): {rec.get('synthesis','')}", ""]
    return "\n".join(lines)


def render_site_page(db: dict, today: str) -> str:
    e = _html.escape
    recs = db.get("records", [])
    css = """
body{font-family:-apple-system,"Segoe UI",sans-serif;background:#FCFCFB;color:#2E2C27;margin:0;line-height:1.55}
.wrap{max-width:860px;margin:0 auto;padding:36px 26px 60px}
h1{font-size:25px;margin:0 0 4px}h2{font-size:19px;margin:26px 0 10px;border-bottom:1px solid #E4E3DC;padding-bottom:4px}
.sub{color:#6B6A63;font-size:14px;margin-bottom:20px}.top{font-size:13px;margin-bottom:18px}
a{color:#2f5d52}
.today{background:#FFF8EE;border:1px solid #EFDDC2;border-left:4px solid #C6893F;border-radius:8px;padding:14px 18px;margin:10px 0 20px}
.today .k{font-size:11.5px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:#a06a24;margin-bottom:6px}
.chunk{background:#fff;border:1px solid #E4E3DC;border-radius:8px;padding:11px 15px;margin:8px 0}
.stmt{font-weight:600;font-size:14.5px}
.meta{color:#6B6A63;font-size:12.5px;margin-top:4px}
.ev{font-size:13px;color:#3a3833;margin-top:5px}
.gen-established{color:#2f5d52;font-weight:700}.gen-suggested{color:#9c6b1f;font-weight:700}.gen-single-study{color:#B23A2E;font-weight:700}
.syn{background:#F0F4F8;border-radius:6px;padding:8px 12px;font-size:13px;margin-top:8px;color:#2E2C27}
.syn b{color:#3a5c53}
"""
    parts = [f"<h1>&#128161; MCSP intuition handbook</h1>"
             f"<div class=\"sub\">{sum(len(r.get('chunks',[])) for r in recs)} intuition chunks from "
             f"{len(recs)} papers &middot; one paper distilled per day &middot; updated {today}</div>"]
    if recs:
        r = recs[-1]
        doi = f' &middot; <a href="https://doi.org/{e(r["doi"])}" target="_blank">doi</a>' if r.get("doi") else ""
        parts.append(
            f'<div class="today"><div class="k">Today\'s paper &mdash; {e(r["date"])}</div>'
            f'<b>{e(r["title"])}</b> ({r.get("year","")}){doi}'
            f'<p><b>Core idea:</b> {e(r.get("core_idea",""))}</p>'
            f'<p><b>Innovation:</b> {e(r.get("innovation",""))}</p>'
            + "".join(
                f'<div class="chunk"><div class="stmt">{e(c["statement"])}</div>'
                f'<div class="meta">{e(c["type"])} &middot; scope: {e(c["scope"])} &middot; '
                f'<span class="gen-{e(c["generality"])}">{e(c["generality"])}</span></div>'
                f'<div class="ev">{e(c["evidence"])}</div></div>'
                for c in r.get("chunks", []))
            + f'<div class="syn"><b>Assistant synthesis (interpretation):</b> {e(r.get("synthesis",""))}</div></div>')
    for t in CHUNK_TYPES:
        rows = []
        for rec in recs:
            for c in rec.get("chunks", []):
                if c.get("type") == t:
                    doi = f' <a href="https://doi.org/{e(rec["doi"])}" target="_blank">[src]</a>' if rec.get("doi") else ""
                    flag = "" if rec.get("source_mode") in ("pdf", "clipping") else " (abstract-only)"
                    rows.append(
                        f'<div class="chunk"><div class="stmt">{e(c["statement"])}</div>'
                        f'<div class="meta">scope: {e(c["scope"])} &middot; '
                        f'<span class="gen-{e(c["generality"])}">{e(c["generality"])}</span>'
                        f' &middot; {e(rec["title"][:55])}{doi}{flag}</div>'
                        f'<div class="ev">{e(c["evidence"])}</div></div>')
        if rows:
            parts.append(f"<h2>{_html.escape(TYPE_TITLES[t])}</h2>" + "".join(rows))
    body = "".join(parts)
    return (f"<!doctype html><html><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>MCSP intuition handbook</title><style>{css}</style></head><body>"
            f"<div class=\"wrap\"><div class=\"top\"><a href=\"index.html\">&larr; CSP Reading Room</a>"
            f" &nbsp;&middot;&nbsp; <a href=\"learn.html\">Learn</a></div>{body}</div></body></html>")


def render_all(db: dict, vault: str) -> None:
    today = datetime.date.today().isoformat()
    try:
        from tree import load_source_files
        pages = {s: pn for s, (pn, _) in load_source_files(vault).items()}
    except Exception:  # noqa: BLE001
        pages = {}
    dest = os.path.join(vault, "wiki", "syntheses", "mcsp-intuition-handbook.md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w").write(render_vault_page(db, pages, today))
    open(os.path.join(REPO, "site", "intuition.html"), "w").write(render_site_page(db, today))
    print(f"[intuition] handbook -> {dest} + site/intuition.html "
          f"({sum(len(r.get('chunks', [])) for r in db.get('records', []))} chunks)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--daily", action="store_true")
    p.add_argument("--slug")
    p.add_argument("--render-only", action="store_true")
    a = p.parse_args()
    vault = os.environ.get("VAULT_PATH", DEFAULT_VAULT)
    db = load_db()
    if not a.render_only:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            sys.exit("Set ANTHROPIC_API_KEY first (or use --render-only).")
        model = os.environ.get("INTUITION_MODEL", DEFAULT_MODEL)
        manifest = json.load(open(MANIFEST_PATH))["entries"]
        if a.slug:
            entry = manifest.get(a.slug)
            if not entry:
                sys.exit(f"slug not in manifest: {a.slug}")
        else:
            entry = pick_next(manifest, db)
        if entry is None:
            print("[intuition] corpus exhausted - nothing new to distill today")
        else:
            try:
                rec = extract(entry, vault, model, key)
                db.setdefault("records", []).append(rec)
                json.dump(db, open(DB_PATH, "w"), indent=1)
                print(f"[intuition] {rec['slug']}: {len(rec.get('chunks', []))} chunks "
                      f"(source: {rec['source_mode']})")
                append_log(vault, f"- {rec['date']} intuition: [[mcsp-intuition-handbook]] += "
                                  f"{rec['slug']} ({len(rec.get('chunks', []))} chunks)")
            except Exception as e:  # noqa: BLE001 - never break the daily job
                print(f"[warn] intuition extraction failed for "
                      f"{entry.get('slug')}: {e}", file=sys.stderr)
    render_all(db, vault)


if __name__ == "__main__":
    main()
