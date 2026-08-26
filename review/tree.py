#!/usr/bin/env python3
"""
M3 — Knowledge-tree synthesizer (csp-digest issue #1).

Reads the digested wiki/sources pages + the corpus manifest and asks a
frontier model to organize the field into the PRD's FIXED branch structure,
then renders wiki/syntheses/mcsp-knowledge-tree.md deterministically and
creates stub pages for missing concepts (per the vault's concept template).

Accuracy invariants: the model may only place papers that exist in the
manifest (anything else is dropped and reported), and only from the digested
set it was shown; concept definitions are grounded in the digests provided.
Intermediate JSON is saved to review/tree.json so M4/M5 need no LLM re-run.

Usage:  ANTHROPIC_API_KEY=... python3 review/tree.py
Env: VAULT_PATH, ANALYSIS_MODEL. Stdlib only.
"""
from __future__ import annotations
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from digester import _api_call, _text_of, DEFAULT_VAULT, DEFAULT_MODEL, PROFILE, append_log  # noqa: E402

REVIEW_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(REVIEW_DIR, "corpus-manifest.json")
TREE_JSON = os.path.join(REVIEW_DIR, "tree.json")

BRANCHES = [
    ("history", "History: the CSP blind tests"),
    ("generation", "Structure generation & search"),
    ("ranking", "Energy ranking & accuracy"),
    ("systems", "Hard systems: salts, cocrystals, flexibility, Z'>1"),
    ("finite-t", "Finite temperature & free energy"),
    ("sota", "The ML era & state of the art"),
]

TREE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "branches": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "key": {"type": "string", "enum": [k for k, _ in BRANCHES]},
                "overview": {"type": "string"},          # 4-8 sentences, backbone narrative
                "papers": {"type": "array", "items": {"type": "string"}},   # manifest slugs, importance order
                "concepts": {"type": "array", "items": {"type": "string"}}, # kebab-case concept slugs
            },
            "required": ["key", "overview", "papers", "concepts"],
        }},
        "spine_note": {"type": "string"},                # how the branches connect, 3-5 sentences
        "gator_position": {"type": "string"},            # where GAtor 2.0 sits in the map
    },
    "required": ["branches", "spine_note", "gator_position"],
}

CONCEPT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"concepts": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "slug": {"type": "string"},
            "definition": {"type": "string"},            # 2-4 sentences, grounded in the digests
            "related": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["slug", "definition", "related"],
    }}},
    "required": ["concepts"],
}


def load_sources(vault: str) -> dict[str, str]:
    """slug -> source-page text, for pages produced by M2 (date_slug.md)."""
    return {s: md for s, (_, md) in load_source_files(vault).items()}


def load_source_files(vault: str) -> dict[str, tuple[str, str]]:
    """slug -> (page name without .md, page text). Page name is what Obsidian
    wikilinks must target ([[2026-08-25_gator-2018|Title]])."""
    d = os.path.join(vault, "wiki", "sources")
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        m = re.match(r"(\d{4}-\d{2}-\d{2}_(.+))\.md$", f)
        if m:
            out[m.group(2)] = (m.group(1),
                               open(os.path.join(d, f), encoding="utf-8", errors="replace").read())
    return out


def extract_summary(md: str) -> str:
    """First blockquote line of a source page = its digest summary."""
    for line in md.splitlines():
        if line.startswith("> "):
            return line[2:].strip()
    return ""


def extract_section(md: str, name: str) -> str:
    m = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", md, re.M | re.S)
    return " ".join(m.group(1).split()) if m else ""


def existing_concepts(vault: str) -> list[str]:
    out = []
    for sub in ("wiki/concepts", "concepts"):
        d = os.path.join(vault, sub)
        if os.path.isdir(d):
            out += [f[:-3] for f in os.listdir(d) if f.endswith(".md")]
    return sorted(set(out))


def synthesize(sources: dict, manifest_entries: dict, concepts: list, model: str, key: str,
               api=None) -> dict:
    api = api or _api_call
    paper_ctx = "\n\n".join(
        f"### slug={slug}\n{txt[:3000]}" for slug, txt in sources.items())
    branch_desc = "\n".join(f"- {k}: {t}" for k, t in BRANCHES)
    prompt = (
        "You are organizing a personal knowledge map of molecular crystal structure prediction. "
        + PROFILE + "\n\nBelow are digested source pages (slug + content). Assign the field into "
        "EXACTLY these fixed branches:\n" + branch_desc + "\n\nRules: 'papers' lists ONLY slugs "
        "shown below, most foundational first; a paper may appear in at most two branches; "
        "'concepts' are kebab-case slugs (prefer existing: " + ", ".join(concepts) + "); overviews "
        "are grounded ONLY in the digests - never assert results they don't contain; plain ASCII.\n\n"
        + paper_ctx
    )
    body = {"model": model, "max_tokens": 6000,
            "output_config": {"format": {"type": "json_schema", "schema": TREE_SCHEMA}},
            "messages": [{"role": "user", "content": prompt}]}
    tree = json.loads(_text_of(api(body, key)))
    # Accuracy gate: drop any paper slug not in the manifest/sources; report drops.
    valid = set(sources) | set(manifest_entries)
    for b in tree["branches"]:
        bad = [s for s in b["papers"] if s not in valid]
        if bad:
            print(f"[tree] DROPPED invented slugs from {b['key']}: {bad}", file=sys.stderr)
        b["papers"] = [s for s in b["papers"] if s in valid]
    return tree


def define_missing_concepts(tree: dict, sources: dict, have: list, model: str, key: str,
                            api=None, cap: int = 12) -> list[dict]:
    api = api or _api_call
    wanted = []
    for b in tree["branches"]:
        wanted += b.get("concepts", [])
    missing = [c for c in dict.fromkeys(wanted) if c not in have][:cap]
    if not missing:
        return []
    ctx = "\n\n".join(f"### {s}\n{t[:2000]}" for s, t in list(sources.items())[:20])
    prompt = (
        "Write short grounded definitions for these molecular-CSP wiki concepts: "
        + ", ".join(missing) + ". Ground every statement in the digests below (or in standard "
        "textbook fact for basic definitions); 2-4 plain sentences each; 'related' lists other "
        "concept slugs from this same list or from: " + ", ".join(have) + ". Plain ASCII.\n\n" + ctx
    )
    body = {"model": model, "max_tokens": 4000,
            "output_config": {"format": {"type": "json_schema", "schema": CONCEPT_SCHEMA}},
            "messages": [{"role": "user", "content": prompt}]}
    got = json.loads(_text_of(api(body, key)))["concepts"]
    return [c for c in got if c["slug"] in missing]        # never accept invented slugs

# ---------------- deterministic renderers (pure; testable) ----------------

def render_tree_page(tree: dict, slug_titles: dict, today: str,
                     pages: dict | None = None, urls: dict | None = None) -> str:
    lines = ["---", "type: synthesis", 'title: "MCSP knowledge tree"',
             "tags: [\"mcsp-corpus\", \"map\"]", f"created: {today}", f"updated: {today}",
             "---", "", "# MCSP knowledge tree", "",
             "> Backbone-first map of molecular crystal structure prediction. "
             "Read branch overviews before diving into papers.", "",
             "## How the branches connect", "", tree.get("spine_note", ""), "",
             "## Where GAtor 2.0 sits", "", tree.get("gator_position", ""), ""]
    order = {k: i for i, (k, _) in enumerate(BRANCHES)}
    titles = dict(BRANCHES)
    pages = pages or {}
    urls = urls or {}
    for b in sorted(tree["branches"], key=lambda x: order.get(x["key"], 99)):
        lines += [f"## {titles.get(b['key'], b['key'])}", "", b["overview"], "", "**Read:**", ""]
        for s in b["papers"]:
            t = slug_titles.get(s, s)
            page_name, md = pages.get(s, (s, ""))
            link = f"- [[{page_name}|{t}]]"
            if urls.get(s):
                link += f" ([paper]({urls[s]}))"
            lines.append(link)
            summ = extract_summary(md)
            innov = extract_section(md, "Contribution")
            if summ:
                lines.append(f"    - **Summary:** {summ}")
            if innov:
                lines.append(f"    - **Innovation - why it matters:** {innov[:450]}")
        if b.get("concepts"):
            lines += ["", "**Concepts:** " + " ".join(f"[[{c}]]" for c in b["concepts"])]
        lines.append("")
    return "\n".join(lines)


def render_concept_stub(c: dict, today: str) -> str:
    rel = " ".join(f"[[{r}]]" for r in c.get("related", []))
    return "\n".join([
        "---", "type: concept", f'title: "{c["slug"].replace("-", " ")}"',
        "tags: [\"mcsp-corpus\"]", "sources: []",
        f"created: {today}", f"updated: {today}", "---", "",
        f"# {c['slug'].replace('-', ' ')}", "", f"> {c['definition']}", "",
        "## Related", "", rel or "(none)", "",
        "_Stub generated by M3; expand as sources accumulate._", ""])


def main() -> None:
    render_only = "--render-only" in sys.argv
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key and not render_only:
        sys.exit("Set ANTHROPIC_API_KEY first (or use --render-only).")
    vault = os.environ.get("VAULT_PATH", DEFAULT_VAULT)
    model = os.environ.get("ANALYSIS_MODEL", DEFAULT_MODEL)
    today = datetime.date.today().isoformat()
    manifest = json.load(open(MANIFEST_PATH))["entries"]
    sources = load_sources(vault)
    if len(sources) < 5:
        sys.exit(f"Only {len(sources)} digested sources found - run digester.py first.")
    have = existing_concepts(vault)
    if render_only:
        if not os.path.exists(TREE_JSON):
            sys.exit("review/tree.json missing - run once without --render-only.")
        tree = json.load(open(TREE_JSON))
    else:
        tree = synthesize(sources, manifest, have, model, key)
        json.dump(tree, open(TREE_JSON, "w"), indent=1)
    slug_titles = {s: (manifest.get(s, {}).get("title") or s) for s in sources}
    pages = load_source_files(vault)
    urls = {s: f"https://doi.org/{manifest[s]['doi']}" for s in sources
            if manifest.get(s, {}).get("doi")}
    page = render_tree_page(tree, slug_titles, today, pages=pages, urls=urls)
    dest = os.path.join(vault, "wiki", "syntheses", "mcsp-knowledge-tree.md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w").write(page)
    print(f"[tree] -> {dest}")
    stubs = [] if render_only else define_missing_concepts(tree, sources, have, model, key)
    cdir = os.path.join(vault, "wiki", "concepts")
    os.makedirs(cdir, exist_ok=True)
    for c in stubs:
        cpath = os.path.join(cdir, f"{c['slug']}.md")
        if not os.path.exists(cpath):
            open(cpath, "w").write(render_concept_stub(c, today))
            print(f"[tree] concept stub -> wiki/concepts/{c['slug']}.md")
    append_log(vault, f"- {today} synthesize: [[mcsp-knowledge-tree]] updated, "
                      f"{len(stubs)} concept stubs - M3")


if __name__ == "__main__":
    main()
