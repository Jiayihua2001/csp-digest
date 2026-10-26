#!/usr/bin/env python3
"""
Molecular-CSP classics pool for csp-digest (one of the two landmark lanes).

Mines a pool of well-cited, established molecular-CSP papers from OpenAlex
(real DOIs/metadata) and caches it in-repo so CI never needs OpenAlex. The
daily pick and its three-question explanation live in landmarks.py; this
module only builds the pool.

Refresh the cache locally (needs OPENALEX_API_KEY; stale after 45 days):
    python3 classic.py

Stdlib only.
"""
from __future__ import annotations
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# The classics pool is mostly static, so it's mined once (locally, where
# OpenAlex works) and cached in-repo; CI runs never need OpenAlex at all.
POOL_CACHE = os.path.join("review", "classics_pool.json")
POOL_MAX_AGE_DAYS = 365       # a canon barely changes; refresh by hand with `python3 classic.py`

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
        if os.environ.get("OPENALEX_API_KEY"):
            params["api_key"] = os.environ["OPENALEX_API_KEY"]
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


def _pool_cached() -> list:
    """Load the committed pool cache; re-mine only when stale AND OpenAlex is
    reachable (a failed refresh falls back to the stale cache). CI cannot reach
    OpenAlex, so in practice the cache is refreshed locally and committed."""
    cached, age = [], 10**6
    if os.path.exists(POOL_CACHE):
        try:
            d = json.load(open(POOL_CACHE))
            cached = d.get("pool", [])
            mined = datetime.date.fromisoformat(d.get("mined", "1970-01-01"))
            age = (datetime.date.today() - mined).days
        except Exception:  # noqa: BLE001
            pass
    if cached and age <= POOL_MAX_AGE_DAYS:
        return cached
    try:
        pool = mine_pool()
        if pool:
            os.makedirs(os.path.dirname(POOL_CACHE), exist_ok=True)
            json.dump({"mined": datetime.date.today().isoformat(), "pool": pool},
                      open(POOL_CACHE, "w"), indent=1)
            return pool
    except Exception as e:  # noqa: BLE001
        print(f"[warn] classic pool refresh failed: {e}", file=sys.stderr)
    return cached                      # stale cache beats no pool


if __name__ == "__main__":
    pool = mine_pool()
    if not pool:
        sys.exit("no pool mined (OpenAlex unreachable or budget exhausted)")
    os.makedirs(os.path.dirname(POOL_CACHE), exist_ok=True)
    json.dump({"mined": datetime.date.today().isoformat(), "pool": pool}, open(POOL_CACHE, "w"), indent=1)
    print(f"{len(pool)} classics -> {POOL_CACHE}")
