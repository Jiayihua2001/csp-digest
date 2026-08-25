#!/usr/bin/env python3
"""
M5 — Learn-tab renderer (csp-digest issue #1).

Pure, deterministic vault -> static HTML transform. No LLM, no network:
reads review/tree.json + review/curriculum.json + the vault's wiki/sources
pages and writes site/learn.html (the tree + curriculum view) plus
site/learn/<slug>.html per-paper pages. Wikilinks resolve to paper pages
when the target is a digested source, otherwise render as plain concept
chips. Group-line papers (tier B) get a distinct badge.

Usage:  python3 review/render_learn.py            # writes into site/
Env: VAULT_PATH. Stdlib only. Safe to run in CI.
"""
from __future__ import annotations
import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tree import load_sources, BRANCHES  # noqa: E402

REVIEW_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(REVIEW_DIR)
MANIFEST_PATH = os.path.join(REVIEW_DIR, "corpus-manifest.json")
TREE_JSON = os.path.join(REVIEW_DIR, "tree.json")
CURRICULUM_JSON = os.path.join(REVIEW_DIR, "curriculum.json")
DEFAULT_VAULT = os.path.expanduser("~/Documents/workspace/Code/AI_brain/Jade")

CSS = """
body{font-family:-apple-system,"Segoe UI",sans-serif;background:#FCFCFB;color:#2E2C27;margin:0;line-height:1.55}
.wrap{max-width:860px;margin:0 auto;padding:36px 26px 60px}
h1{font-size:25px;margin:0 0 4px}h2{font-size:19px;margin:28px 0 8px;border-bottom:1px solid #E4E3DC;padding-bottom:4px}
.sub{color:#6B6A63;font-size:14px;margin-bottom:22px}
a{color:#2f5d52}
.branch{background:#fff;border:1px solid #E4E3DC;border-radius:8px;padding:14px 18px;margin:12px 0}
.paper{margin:6px 0;padding-left:10px;border-left:3px solid #EAF1EF}
.paper a{font-weight:600;text-decoration:none}
.why{color:#6B6A63;font-size:13.5px}
.chip{display:inline-block;font-size:11.5px;color:#5b6b78;background:#EEF1F3;border-radius:10px;padding:2px 9px;margin:2px 3px 0 0}
.badge-group{display:inline-block;font-size:10.5px;font-weight:700;color:#fff;background:#C6613F;border-radius:3px;padding:1px 6px;margin-left:6px;vertical-align:middle}
.badge-conf{display:inline-block;font-size:10.5px;font-weight:600;color:#9c6b1f;background:#FBF3E2;border-radius:3px;padding:1px 6px;margin-left:6px}
.stage{background:#F0F4F8;border:1px solid #D3DEE7;border-left:4px solid #4a7a6f;border-radius:8px;padding:14px 18px;margin:12px 0}
.goal{font-size:14px;margin:4px 0}.gator{font-size:13px;color:#3a5c53;margin-top:8px}
.meta{color:#6B6A63;font-size:13px;margin-bottom:14px}
.section{white-space:pre-wrap}
.vflag{color:#B23A2E;font-weight:600}
.top{font-size:13px;margin-bottom:18px}
"""


def _page(title: str, body: str, depth: int = 0) -> str:
    root = "../" * depth
    return (f"<!doctype html><html><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
            f"<div class=\"wrap\"><div class=\"top\"><a href=\"{root}index.html\">&larr; CSP Reading Room</a>"
            f" &nbsp;&middot;&nbsp; <a href=\"{root}learn.html\">Learn</a></div>"
            f"{body}</div></body></html>")


def _link_paper(slug: str, titles: dict, tiers: dict, depth: int = 0) -> str:
    t = html.escape(titles.get(slug, slug))
    badge = '<span class="badge-group">our group</span>' if tiers.get(slug) == "B" else ""
    root = "" if depth else "learn/"
    return f'<a href="{root}{slug}.html">{t}</a>{badge}'


def _wikilinks_to_chips(text: str, sources: set, depth: int = 0) -> str:
    """[[slug]] -> paper link if digested source, else a concept chip."""
    def sub(m):
        s = m.group(1)
        if s in sources:
            root = "" if depth else "learn/"
            return f'<a href="{root}{s}.html">{html.escape(s)}</a>'
        return f'<span class="chip">{html.escape(s)}</span>'
    return re.sub(r"\[\[([^\]|]+)\]\]", sub, text)


def render_learn_page(tree: dict, cur: dict, manifest: dict, sources: dict, today: str) -> str:
    titles = {s: (manifest.get(s, {}).get("title") or s) for s in sources}
    tiers = {s: manifest.get(s, {}).get("tier", "?") for s in sources}
    parts = [f"<h1>Learn MCSP</h1><div class=\"sub\">A backbone-first map and curriculum of "
             f"molecular crystal structure prediction &mdash; built from {len(sources)} digested "
             f"papers &middot; updated {today}</div>"]
    parts.append("<h2>How the field fits together</h2>"
                 f"<div class=\"branch\"><div class=\"section\">{html.escape(tree.get('spine_note', ''))}</div>"
                 f"<p class=\"gator\"><b>Where GAtor 2.0 sits:</b> {html.escape(tree.get('gator_position', ''))}</p></div>")
    order = {k: i for i, (k, _) in enumerate(BRANCHES)}
    names = dict(BRANCHES)
    parts.append("<h2>The knowledge tree</h2>")
    for b in sorted(tree.get("branches", []), key=lambda x: order.get(x["key"], 99)):
        papers = "".join(f'<div class="paper">{_link_paper(s, titles, tiers)}</div>'
                         for s in b.get("papers", []))
        chips = "".join(f'<span class="chip">{html.escape(c)}</span>' for c in b.get("concepts", []))
        parts.append(f'<div class="branch"><h3>{html.escape(names.get(b["key"], b["key"]))}</h3>'
                     f'<div class="section">{html.escape(b.get("overview", ""))}</div>'
                     f'{papers}<div>{chips}</div></div>')
    parts.append("<h2>The curriculum</h2>")
    for n, st in enumerate(cur.get("stages", []), 1):
        items = "".join(
            f'<div class="paper">{_link_paper(i["slug"], titles, tiers)}'
            f'<div class="why">{html.escape(i.get("why", ""))}</div></div>'
            for i in st.get("items", []))
        parts.append(f'<div class="stage"><h3>Stage {n}: {html.escape(st.get("title", ""))}</h3>'
                     f'<div class="goal"><b>Goal:</b> {html.escape(st.get("goal", ""))}</div>'
                     f'<div class="goal"><b>Why now:</b> {html.escape(st.get("why_now", ""))}</div>'
                     f'{items}<div class="gator"><b>GAtor 2.0:</b> {html.escape(st.get("gator_note", ""))}</div></div>')
    return _page("Learn MCSP", "".join(parts))


_MD_SEC = re.compile(r"^## (.+)$", re.M)

def render_paper_page(slug: str, page_md: str, entry: dict, sources: set) -> str:
    """Vault source page (markdown) -> standalone HTML paper page."""
    body_md = re.sub(r"^---.*?---\n", "", page_md, count=1, flags=re.S)     # strip frontmatter
    title = entry.get("title") or slug
    doi = entry.get("doi")
    meta = (f"{html.escape(', '.join(entry.get('authors', [])))} &middot; "
            f"{html.escape(str(entry.get('venue', '')))} ({entry.get('year', '')}) &middot; "
            f"{entry.get('citations', 0)} citations")
    if doi:
        meta += f' &middot; <a href="https://doi.org/{html.escape(doi)}" target="_blank">doi:{html.escape(doi)}</a>'
    if entry.get("tier") == "B":
        meta += ' <span class="badge-group">our group</span>'
    conf = re.search(r"confidence: \*\*(\w+)\*\*", page_md)
    if conf:
        meta += f' <span class="badge-conf">confidence: {conf.group(1)}</span>'
    if "## Verification flags" in page_md:
        meta += ' <span class="vflag">&#9888; verification flagged claims</span>'
    # markdown-lite: sections to h2, bullets kept, wikilinks resolved
    html_body = html.escape(body_md)
    html_body = _MD_SEC.sub(lambda m: f"<h2>{m.group(1)}</h2>", html_body)
    html_body = re.sub(r"^# .+$", "", html_body, count=1, flags=re.M)       # drop md h1 (we render our own)
    html_body = _wikilinks_to_chips(html_body, sources, depth=1)
    html_body = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", html_body)
    body = (f"<h1>{html.escape(title)}</h1><div class=\"meta\">{meta}</div>"
            f"<div class=\"section\">{html_body}</div>")
    return _page(title, body, depth=1)


def build(site_dir: str | None = None, vault: str | None = None) -> dict:
    vault = vault or os.environ.get("VAULT_PATH", DEFAULT_VAULT)
    site_dir = site_dir or os.path.join(REPO, "site")
    today = datetime.date.today().isoformat()
    tree = json.load(open(TREE_JSON)) if os.path.exists(TREE_JSON) else {"branches": [], "spine_note": "", "gator_position": ""}
    cur = json.load(open(CURRICULUM_JSON)) if os.path.exists(CURRICULUM_JSON) else {"stages": [], "closing_note": ""}
    manifest = json.load(open(MANIFEST_PATH))["entries"] if os.path.exists(MANIFEST_PATH) else {}
    sources = load_sources(vault)
    os.makedirs(os.path.join(site_dir, "learn"), exist_ok=True)
    open(os.path.join(site_dir, "learn.html"), "w").write(
        render_learn_page(tree, cur, manifest, sources, today))
    n = 0
    for slug, md in sources.items():
        p = render_paper_page(slug, md, manifest.get(slug, {}), set(sources))
        open(os.path.join(site_dir, "learn", f"{slug}.html"), "w").write(p)
        n += 1
    print(f"[learn] site/learn.html + {n} paper pages")
    return {"papers": n}


if __name__ == "__main__":
    build()
