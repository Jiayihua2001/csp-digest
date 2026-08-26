#!/usr/bin/env python3
"""
M4 — Curriculum generator (csp-digest issue #1).

Turns the M3 tree (review/tree.json) + digested sources into a staged,
backbone-first reading path: wiki/syntheses/mcsp-curriculum.md. Each stage
has a goal, papers in order with a why-this-next rationale, and a GAtor 2.0
note. Sized for roughly a week of part-time reading per stage.

Accuracy: stages may only reference paper slugs from the tree/manifest;
anything else is dropped and reported. Intermediate JSON saved to
review/curriculum.json for M5.

Usage:  ANTHROPIC_API_KEY=... python3 review/curriculum.py
"""
from __future__ import annotations
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digester import _api_call, _text_of, DEFAULT_VAULT, DEFAULT_MODEL, PROFILE, append_log  # noqa: E402
from tree import load_sources, load_source_files, extract_summary, TREE_JSON  # noqa: E402

REVIEW_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(REVIEW_DIR, "corpus-manifest.json")
CURRICULUM_JSON = os.path.join(REVIEW_DIR, "curriculum.json")

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "stages": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "goal": {"type": "string"},              # the question this stage answers
                "why_now": {"type": "string"},           # why it comes at this point in the path
                "items": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"slug": {"type": "string"}, "why": {"type": "string"}},
                    "required": ["slug", "why"],
                }},
                "gator_note": {"type": "string"},
            },
            "required": ["title", "goal", "why_now", "items", "gator_note"],
        }},
        "closing_note": {"type": "string"},
    },
    "required": ["stages", "closing_note"],
}


def generate(tree: dict, sources: dict, model: str, key: str, api=None) -> dict:
    api = api or _api_call
    ctx = json.dumps(tree, indent=1)[:20000]
    listing = "\n".join(f"- {s}" for s in sources)
    prompt = (
        "Design a staged reading curriculum from this knowledge tree. " + PROFILE + "\n\n"
        "Rules: backbone first (field overview + blind-test spine + the reader's own group line: "
        "gator/genarris), then ranking, then systems/finite-T, frontier last. 5-8 stages, each "
        "sized to about a week of part-time reading (2-5 papers). 'slug' must come from this "
        "list ONLY:\n" + listing + "\n\nEach stage: goal = the question it answers; why_now = why "
        "this point in the path; per-paper 'why' = one concrete sentence; gator_note ties the "
        "stage to GAtor 2.0 work. Ground everything in the tree below; plain ASCII.\n\nTREE:\n" + ctx
    )
    body = {"model": model, "max_tokens": 6000,
            "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
            "messages": [{"role": "user", "content": prompt}]}
    cur = json.loads(_text_of(api(body, key)))
    valid = set(sources)
    for st in cur["stages"]:
        bad = [i["slug"] for i in st["items"] if i["slug"] not in valid]
        if bad:
            print(f"[curriculum] DROPPED invented slugs from '{st['title']}': {bad}", file=sys.stderr)
        st["items"] = [i for i in st["items"] if i["slug"] in valid]
    return cur


def render_curriculum_page(cur: dict, slug_titles: dict, today: str,
                           pages: dict | None = None) -> str:
    lines = ["---", "type: synthesis", 'title: "MCSP curriculum"',
             "tags: [\"mcsp-corpus\", \"tutorial\"]", f"created: {today}", f"updated: {today}",
             "---", "", "# MCSP curriculum - backbone first", "",
             "> Work the stages in order; each answers one question and takes about a week "
             "part-time. Check papers off as you go.", ""]
    for n, st in enumerate(cur["stages"], 1):
        lines += [f"## Stage {n}: {st['title']}", "",
                  f"**Goal:** {st['goal']}", "", f"**Why now:** {st['why_now']}", ""]
        for it in st["items"]:
            t = slug_titles.get(it["slug"], it["slug"])
            page_name = (pages or {}).get(it["slug"], (it["slug"], ""))[0]
            lines.append(f"- [ ] [[{page_name}|{t}]]\n    - {it['why']}")
        lines += ["", f"**GAtor 2.0:** {st['gator_note']}", ""]
    lines += ["## After the path", "", cur.get("closing_note", ""), ""]
    return "\n".join(lines)


def main() -> None:
    render_only = "--render-only" in sys.argv
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key and not render_only:
        sys.exit("Set ANTHROPIC_API_KEY first (or use --render-only).")
    vault = os.environ.get("VAULT_PATH", DEFAULT_VAULT)
    model = os.environ.get("ANALYSIS_MODEL", DEFAULT_MODEL)
    today = datetime.date.today().isoformat()
    if not os.path.exists(TREE_JSON):
        sys.exit("review/tree.json missing - run tree.py first.")
    tree = json.load(open(TREE_JSON))
    sources = load_sources(vault)
    manifest = json.load(open(MANIFEST_PATH))["entries"]
    if render_only:
        if not os.path.exists(CURRICULUM_JSON):
            sys.exit("review/curriculum.json missing - run once without --render-only.")
        cur = json.load(open(CURRICULUM_JSON))
    else:
        cur = generate(tree, sources, model, key)
        json.dump(cur, open(CURRICULUM_JSON, "w"), indent=1)
    slug_titles = {s: (manifest.get(s, {}).get("title") or s) for s in sources}
    page = render_curriculum_page(cur, slug_titles, today, pages=load_source_files(vault))
    dest = os.path.join(vault, "wiki", "syntheses", "mcsp-curriculum.md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w").write(page)
    print(f"[curriculum] -> {dest}")
    append_log(vault, f"- {today} synthesize: [[mcsp-curriculum]] updated ({len(cur['stages'])} stages) - M4")


if __name__ == "__main__":
    main()
