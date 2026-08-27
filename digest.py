#!/usr/bin/env python3
"""Self-contained CSP literature digest.

Queries OpenAlex (published articles + ChemRxiv preprints) and arXiv for recent
crystal structure prediction papers (molecular + inorganic), filters off-field
noise, deduplicates, ranks toward genetic-algorithm / evolutionary methods,
tags watchlist authors, optionally adds a one-line AI "why it matters" per
paper, and renders a styled single-file HTML brief.

No platform dependencies: uses public OpenAlex/arXiv APIs directly and the
Anthropic Messages API for summaries. Designed to run in GitHub Actions or
locally.

Environment variables:
  OPENALEX_API_KEY   optional; only for premium OpenAlex accounts (API is free/keyless)
  ANTHROPIC_API_KEY  optional; if set, generates one-line summaries
  OPENALEX_MAILTO    recommended contact email for the OpenAlex polite pool
  DIGEST_DAYS        look-back window in days (default 4)
  DIGEST_SCOPE       "molecular", "inorganic", or "both" (default both)
  SUMMARY_MODEL      Anthropic model id (default claude-sonnet-5)
"""
from __future__ import annotations
import os
import re
import sys
import json
import time
import html
import datetime
import urllib.parse
import urllib.request
import urllib.error

# ----------------------------- configuration -----------------------------

QUERIES_MOLECULAR = [
    "molecular crystal structure prediction",
    "organic crystal polymorph prediction",
    "crystal energy landscape molecular",
    "genetic algorithm crystal structure prediction",
    "lattice energy ranking polymorph",
]
QUERIES_INORGANIC = [
    "inorganic crystal structure prediction",
    "evolutionary algorithm crystal structure prediction",
    "USPEX CALYPSO crystal structure search",
    "generative model crystal structure discovery",
    "machine learning interatomic potential crystal structure prediction",
]
ARXIV_QUERIES = [
    'abs:"crystal structure prediction"',
    'abs:"molecular crystal" AND abs:polymorph',
    'abs:"crystal structure prediction" AND abs:"genetic algorithm"',
    'abs:"crystal structure prediction" AND abs:generative',
]
PREPRINT_VENUE = "ChemRxiv"
CHEMRXIV_SOURCE_ID = "S4393918830"  # OpenAlex source id for ChemRxiv

WATCHLIST = [
    "Noa Marom", "Graeme M. Day", "Marcus A. Neumann", "Sarah L. Price",
    "Gregory J. O. Beran", "Artem R. Oganov", "Chris J. Pickard",
    "Scott M. Woodley", "Qiang Zhu",
]

# NB: trailing s? on nouns so plurals (crystals, polymorphs, landscapes) still match.
POS_PAT = r"\b(crystals?|polymorphs?|lattices?|cocrystals?|co-crystals?|solid[- ]state|salt forms?|packings?|space groups?)\b"
CSP_PAT = r"\b(structure predictions?|energy landscapes?|lattice energ(?:y|ies)|polymorphs?|CSP|space groups?|genetic algorithms?|evolutionary|generative|conformational|USPEX|CALYPSO)\b"
NEG_PAT = r"\b(SARS|COVID|cancer|tumou?r|patient|clinical trial|receptor|antibody|genom|transcription|phage|bacteri|viral|immun|mutagenesis|nucleoside|APOBEC|flavonoid|endothelial)\b"

# Molecular-crystal positive signals (organic / molecular-solid vocabulary).
MOLECULAR_PAT = (r"\b(molecular crystals?|organic (?:crystals?|molecules?|semiconductors?)|"
                 r"pharmaceutical|drug|API|cocrystals?|co-crystals?|polymorphs?|"
                 r"conformational|conformer|hydrogen[- ]bond|Z['\u2032]|"
                 r"active pharmaceutical|salt forms?|solvates?|hydrates?|"
                 r"aspirin|paracetamol|amino acids?|small molecules?)\b")
# Inorganic / materials-science signals — exclude these from a molecular digest
# unless a molecular signal is also present.
INORGANIC_PAT = (r"\b(alloys?|intermetallics?|perovskites?|oxides?|nitrides?|hydrides?|"
                 r"borides?|carbides?|superconduct\w*|thermoelectric|cathodes?|anodes?|"
                 r"battery|photovoltaic|high[- ]pressure phases?|solid solution|"
                 r"binary system|ternary system|chalcogenides?|halide perovskites?|"
                 r"[A-Z][a-z]?Fe[A-Z][a-z]?|superhard)\b")
FOCUS_PAT = r"\b(genetic algorithm|evolutionary|GAtor|Genarris|USPEX|CALYPSO|XtalOpt|molecular crystal|polymorph|generative|energy landscape|interatomic potential|niching|crossover|mutation operator|relative coordinate descriptor|physics-informed|population-based|conformational search|packing search|multi-objective)\b"

# Flexible CSP-phrase match: "... structure prediction ..." where a crystal/
# molecular qualifier appears nearby (handles titles like "Structure Prediction
# of Multi-Component Molecular Crystals" where words separate the phrase).
CSP_PHRASE_PAT = (r"crystal structure prediction"
                  r"|structure prediction of[\w\s,-]{0,40}?(crystal|molecul|polymorph|solid)"
                  r"|(crystal|molecular|polymorph)[\w\s,-]{0,40}?structure prediction")

# Field-vocabulary density: on-topic papers use many of these even when they
# match few of the digest's canned queries. Generic CSP terms only.
VOCAB_PAT = (r"\b(lattice energ|space group|Z['\u2032]|asymmetric unit|cocrystal|co-crystal|"
             r"conformer|torsion|dispersion correction|DFT-D|force field|"
             r"hydrogen bond|van der Waals|packing|energy window|global minimum|"
             r"RMSD|semi-flexible|rigid molecule|stoichiometric)\b")

OPENALEX = "https://api.openalex.org/works"
ARXIV = "http://export.arxiv.org/api/query"


# ------------------------------- fetching ---------------------------------

def _get(url, tries=5, timeout=45):
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "csp-digest"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - transient proxy/network
            last = e
            # GitHub runners share egress IPs, so OpenAlex 429s are common in CI
            # and need real cooldowns (20s/40s/80s/160s), not quick retries.
            time.sleep(min(300.0, 20.0 * (2 ** t)) if "429" in str(e) else 1.5 * (t + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {last}")


def _oa_params(extra):
    # OpenAlex is free and keyless; api_key is only for premium accounts.
    # Use it if provided, otherwise rely on the polite pool via mailto.
    params = {
        "select": "title,publication_date,doi,authorships,primary_location,type,abstract_inverted_index,cited_by_count,fwci",
        "sort": "publication_date:desc",
        "per-page": 40,
    }
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto
    params.update(extra)
    return params


def _reconstruct_abstract(inv):
    if not inv:
        return ""
    words = []
    for w, positions in inv.items():
        for p in positions:
            words.append((p, w))
    words.sort()
    return " ".join(w for _, w in words)[:1200]


def fetch_openalex(query, since, work_type, venue=None):
    # Filter by when OpenAlex INDEXED the work (created_date), not its nominal
    # publication_date: OpenAlex lags days-to-weeks, so a short publication_date
    # window misses papers that are, in practice, brand new to the index.
    filt = f"from_created_date:{since},title_and_abstract.search:{query},type:{work_type}"
    if venue == PREPRINT_VENUE:
        filt += f",primary_location.source.id:{CHEMRXIV_SOURCE_ID}"
    url = OPENALEX + "?" + urllib.parse.urlencode(_oa_params({"filter": filt, "per-page": 100}))
    data = json.loads(_get(url))
    out = []
    for w in data.get("results", []):
        doi = w.get("doi")
        if not doi:
            continue
        loc = w.get("primary_location") or {}
        src = (loc.get("source") or {}).get("display_name")
        out.append({
            "src": "ChemRxiv" if venue else ("journal" if work_type == "article" else "preprint"),
            "title": w.get("title") or "",
            "date": w.get("publication_date"),
            "doi": doi.replace("https://doi.org/", ""),
            "authors": [a["author"]["display_name"] for a in w.get("authorships", [])[:3]],
            "authors_all": [a["author"]["display_name"] for a in w.get("authorships", [])],
            "corresponding": [a["author"]["display_name"] for a in w.get("authorships", [])
                              if a.get("is_corresponding")]
                             or ([w["authorships"][-1]["author"]["display_name"]]
                                 if w.get("authorships") else []),
            "corresponding_ids": [a["author"]["id"].rsplit("/", 1)[-1]
                                  for a in w.get("authorships", [])
                                  if a.get("is_corresponding") and a.get("author", {}).get("id")]
                                 or ([w["authorships"][-1]["author"]["id"].rsplit("/", 1)[-1]]
                                     if w.get("authorships") and w["authorships"][-1].get("author", {}).get("id") else []),
            "author_ids": [a["author"]["id"].rsplit("/", 1)[-1]
                           for a in w.get("authorships", []) if a.get("author", {}).get("id")],
            "institutions": sorted({inst["display_name"]
                                    for a in w.get("authorships", [])
                                    for inst in (a.get("institutions") or [])
                                    if inst.get("display_name")}),
            "venue": venue or src,
            "abstract": _reconstruct_abstract(w.get("abstract_inverted_index")),
            "cited_by": w.get("cited_by_count") or 0,
            "fwci": w.get("fwci"),
            "matched": [query],
        })
    return out


def fetch_arxiv(query, since):
    params = {
        "search_query": query,
        "start": 0,
        "max_results": 25,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = ARXIV + "?" + urllib.parse.urlencode(params)
    raw = _get(url).decode("utf-8", "replace")
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", raw, re.S):
        aid_m = re.search(r"<id>http://arxiv\.org/abs/([^<]+)</id>", entry)
        title_m = re.search(r"<title>(.*?)</title>", entry, re.S)
        pub_m = re.search(r"<published>(\d{4}-\d\d-\d\d)", entry)
        summ_m = re.search(r"<summary>(.*?)</summary>", entry, re.S)
        authors = re.findall(r"<name>([^<]+)</name>", entry)
        if not aid_m or not pub_m:
            continue
        if pub_m.group(1) < since:
            continue
        aid = aid_m.group(1).strip()
        out.append({
            "src": "arXiv",
            "title": re.sub(r"\s+", " ", (title_m.group(1) if title_m else "")).strip(),
            "date": pub_m.group(1),
            "arxiv_id": aid,
            "url": f"https://arxiv.org/abs/{aid}",
            "authors": authors[:3],
            "authors_all": authors,
            "venue": "arXiv",
            "abstract": re.sub(r"\s+", " ", (summ_m.group(1) if summ_m else "")).strip()[:1200],
            "matched": [query],
        })
    time.sleep(3)  # arXiv API asks for 3s between calls
    return out


# --------------------------- filter / rank --------------------------------

def clean_title(t):
    return re.sub(r"&lt;.*?&gt;|<[^>]+>", "", t or "").strip()


def csp_relevant(title):
    t = clean_title(title)
    if not t:
        return False
    if re.search(NEG_PAT, t, re.I) and not re.search(r"structure prediction|polymorph|lattice energy", t, re.I):
        return False
    return bool(re.search(POS_PAT, t, re.I) and re.search(CSP_PAT, t, re.I)) or "crystal structure prediction" in t.lower()


# Institutions with recognized molecular-CSP groups (matched as substrings,
# case-insensitive). Presence of one is a publication-time significance signal.
KNOWN_CSP_INSTITUTIONS = [
    "Carnegie Mellon", "Southampton", "University of Southampton",
    "University of California, Riverside", "Avant-garde Materials",
    "Stony Brook", "University College London", "UCL",
    "Skolkovo", "Cambridge", "Nottingham", "Bath", "Oxford",
]

_AUTHOR_CACHE = {}


def author_stats(author_id):
    """Fetch (h_index, works_count) for one OpenAlex author id, cached.
    Available at publication time — does not depend on the paper's own citations.
    Returns (0, 0) on any failure so scoring degrades gracefully."""
    if not author_id:
        return (0, 0)
    if author_id in _AUTHOR_CACHE:
        return _AUTHOR_CACHE[author_id]
    try:
        url = ("https://api.openalex.org/authors/" + author_id + "?"
               + urllib.parse.urlencode(_oa_params({"select": "summary_stats,works_count"})))
        d = json.loads(_get(url))
        h = int((d.get("summary_stats") or {}).get("h_index") or 0)
        wc = int(d.get("works_count") or 0)
        res = (h, wc)
    except Exception:  # noqa: BLE001 - best-effort enrichment
        res = (0, 0)
    _AUTHOR_CACHE[author_id] = res
    return res


def enrich_arxiv_from_openalex(item):
    """arXiv records carry only author NAMES (no IDs/institutions), and name-based
    author lookup is unreliable (disambiguation). Instead, try to resolve the paper
    itself in OpenAlex by exact-ish title: if found, borrow its author_ids +
    institutions so significance enrichment works. Fresh preprints (not yet indexed)
    simply return unchanged — significance then rests on watchlist-name match only."""
    if item.get("src") != "arXiv" or item.get("author_ids"):
        return item
    title = item.get("title", "")
    if len(title) < 15:
        return item
    try:
        url = OPENALEX + "?" + urllib.parse.urlencode(_oa_params(
            {"filter": f"title.search:{title}", "per-page": 3,
             "select": "title,authorships,cited_by_count,fwci"}))
        data = json.loads(_get(url))
        for w in data.get("results", []):
            cand = (w.get("title") or "").lower().strip()
            if cand[:40] == title.lower().strip()[:40]:            # confident title match
                item["author_ids"] = [a["author"]["id"].rsplit("/", 1)[-1]
                                      for a in w.get("authorships", [])
                                      if a.get("author", {}).get("id")]
                item["authors_all"] = [a["author"]["display_name"]
                                       for a in w.get("authorships", [])] or item.get("authors_all")
                item["institutions"] = sorted({inst["display_name"]
                                               for a in w.get("authorships", [])
                                               for inst in (a.get("institutions") or [])
                                               if inst.get("display_name")})
                if item.get("cited_by") in (None, 0):
                    item["cited_by"] = w.get("cited_by_count") or 0
                if item.get("fwci") is None:
                    item["fwci"] = w.get("fwci")
                break
    except Exception:  # noqa: BLE001 - enrichment is best-effort
        pass
    return item


def best_author_hindex(item):
    """Max h-index among the paper's (listed) authors."""
    hs = [author_stats(aid)[0] for aid in (item.get("author_ids") or [])]
    return max(hs) if hs else 0


def corresponding_hindex(item):
    """h-index of the corresponding author (the PI/advisor on a typical CSP paper).
    Falls back to the last-author id when no explicit corresponding flag exists."""
    hs = [author_stats(aid)[0] for aid in (item.get("corresponding_ids") or [])]
    return max(hs) if hs else 0


def corresponding_is_watchlist(item, sset):
    """True if the corresponding author (advisor) is a watchlist PI — a stronger
    signal than any co-author being on the list."""
    return bool(tag_watchlist(item.get("corresponding") or [], sset))


def has_known_institution(item):
    insts = " ; ".join(item.get("institutions") or [])
    return any(k.lower() in insts.lower() for k in KNOWN_CSP_INSTITUTIONS)


def is_molecular(item):
    """True unless the paper is about an inorganic/materials system with no
    molecular-crystal signal. Applied when scope='molecular' to catch inorganic
    hits that arrive via the (scope-agnostic) arXiv queries — e.g. alloy or
    high-pressure-phase CSP."""
    text = (item.get("title", "") + " " + (item.get("abstract") or ""))
    if re.search(INORGANIC_PAT, text) and not re.search(MOLECULAR_PAT, text, re.I):
        return False
    return True


def watch_surnames():
    return {n.split()[-1] for n in WATCHLIST if n}


def tag_watchlist(authors, sset):
    hits = []
    for a in authors or []:
        sn = a.split()[-1] if a else ""
        if sn in sset and sn not in hits:
            hits.append(sn)
    return hits


# --- field-locating keyword tags: label -> pattern (searched over title+abstract) ---
TAG_PATTERNS = [
    ("genetic-algorithm", r"genetic algorithm|evolutionary algorithm|GAtor|Genarris|USPEX|CALYPSO"),
    ("generative-model", r"generative|diffusion model|GFlowNet|variational|VAE|normalizing flow|flow matching"),
    ("ML-potential", r"machine[- ]learn|neural network potential|interatomic potential|MLIP|foundation model|MACE|NequIP|GRACE|universal potential"),
    ("free-energy", r"free energy|quasi[- ]harmonic|QHA|phonon|entropy|finite temperature|vibrational"),
    ("lattice-energy", r"lattice energy|DFT-D|dispersion|electrostatic|force field|energy ranking"),
    ("polymorphism", r"polymorph|disappearing polymorph|form I|form II|enantiotropic|monotropic"),
    ("cocrystal-salt", r"cocrystal|co-crystal|salt form|solvate|hydrate|multicomponent|multi-component"),
    ("conformational", r"conformational|flexible molecule|torsion|Z['\u2032] ?> ?1|conformer"),
    ("space-group", r"space group|Sohncke|chiral crystal|packing"),
    ("benchmark", r"blind test|benchmark|CSP landscape|structure landscape"),
]


def keyword_tags(item):
    """Field-locating tags from title+abstract, capped to the most specific few."""
    text = (item.get("title", "") + " " + (item.get("abstract") or ""))
    tags = [label for label, pat in TAG_PATTERNS if re.search(pat, text, re.I)]
    return tags[:4]


def relevance_score(item):
    """0-100: how central the paper is to (molecular) CSP. Title+abstract driven."""
    text = (item.get("title", "") + " " + (item.get("abstract") or ""))
    s = 0
    s += 20 * min(len(item.get("matched", []) or []), 2)      # up to 40: query breadth
    if re.search(CSP_PHRASE_PAT, text, re.I):
        s += 20                                                # CSP phrase (flexible match)
    if re.search(FOCUS_PAT, text, re.I):
        s += 15                                                # GA/molecular focus vocabulary
    s += 5 * min(len(keyword_tags(item)), 3)                   # up to 15: tag-topic density
    vocab_hits = len(set(re.findall(VOCAB_PAT, text, re.I)))   # up to 10: field-vocab density
    s += 2 * min(vocab_hits, 5)
    return min(s, 100)


def significance_score(item, sset):
    """0-100: likely importance, weighted toward signals present AT PUBLICATION so
    fresh preprints are not all zero, and toward the CORRESPONDING author (the
    PI/advisor), whose standing is the best publication-time proxy for importance.
    Components:
      corresponding-author standing: watchlist PI (25) OR their h-index (<=25)
      + any co-author h-index (<=10) + known CSP institution (<=12) + venue (<=12)
      + accrued impact: FWCI (<=8) + log citations (<=8), which grow over time.
    Interpret as a prior, not a verdict."""
    import math
    s = 0
    # --- advisor / corresponding-author signal (dominant, publication-time) ---
    if corresponding_is_watchlist(item, sset):
        s += 25                                                # advisor is a watchlist PI
    else:
        hc = corresponding_hindex(item)                       # else the advisor's own standing
        s += min(25, 25 * (hc / 60.0))                        # h=60 saturates
    # any co-author on the watchlist is a weaker, additional signal
    coauthor_wl = tag_watchlist(item.get("authors_all") or item.get("authors", []), sset)
    if coauthor_wl and not corresponding_is_watchlist(item, sset):
        s += 8                                                 # watchlist co-author (not the PI)
    # --- other publication-time signals ---
    h = best_author_hindex(item)                               # up to 10: any senior co-author
    s += min(10, 10 * (h / 60.0))
    if has_known_institution(item):
        s += 12                                                # recognized molecular-CSP group
    venue = (item.get("venue") or "").lower()
    if any(k in venue for k in ("nature", "science", "j. am. chem", "jacs", "angew", "chem. sci", "pnas")):
        s += 12                                                # high-visibility venue
    # --- accrued-impact signals (near zero for new papers, grow later) ---
    fwci = item.get("fwci")
    if isinstance(fwci, (int, float)):
        s += min(12, 12 * (fwci / 3.0))                        # up to 12: FWCI (3x field avg saturates)
    cited = item.get("cited_by", 0) or 0
    s += min(8, 4 * math.log10(cited + 1))                     # up to 8: log citations
    return int(min(s, 100))


def rank_items(items, scope="molecular"):
    sset = watch_surnames()
    out = []
    for it in items:
        it["title"] = clean_title(it.get("title", ""))
        if it.get("src") != "arXiv" and not csp_relevant(it["title"]):
            continue
        if scope == "molecular" and not is_molecular(it):
            continue
        enrich_arxiv_from_openalex(it)
        it["tags"] = keyword_tags(it)
        it["relevance"] = relevance_score(it)
        it["significance"] = significance_score(it, sset)
        it["score"] = it["relevance"] + it["significance"]     # combined sort key
        out.append(it)
    out.sort(key=lambda x: (x.get("score", 0), x.get("date") or ""), reverse=True)
    return out


# ------------------------------ summaries ---------------------------------

def summarize(items):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return items  # summaries are optional
    model = os.environ.get("SUMMARY_MODEL", "claude-sonnet-5")
    for it in items:
        prompt = (
            "You brief a crystal structure prediction (CSP) specialist who works on genetic-algorithm "
            "and evolutionary methods. In ONE sentence (max 28 words), state the paper's specific "
            "INNOVATION or CONTRIBUTION - what is new here vs prior work (a new method, operator, "
            "descriptor, benchmark, or result). Lead with the novelty, be concrete, no hype, no 'this "
            "paper'. If the abstract is missing, infer cautiously from the title and hedge.\n\n"
            f"Title: {it.get('title','')}\nVenue: {it.get('venue','')}\nAbstract: {it.get('abstract') or '(none)'}"
        )
        body = json.dumps({
            "model": model,
            "max_tokens": 90,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read())
            it["summary"] = "".join(b.get("text", "") for b in resp.get("content", [])).strip()
        except Exception:  # noqa: BLE001 - summary is best-effort
            it["summary"] = ""
        time.sleep(0.3)
    return items


def daily_synthesis(items):
    """One-to-two sentence 'what's new today' across the day's papers.
    Uses the same Anthropic path as summarize(); returns '' if no key/items."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not items:
        return ""
    model = os.environ.get("SUMMARY_MODEL", "claude-sonnet-5")
    titles = "\n".join(f"- {i.get('title','')} ({i.get('venue','')})" for i in items[:12])
    prompt = (
        "You brief a molecular crystal structure prediction (CSP) specialist working on "
        "genetic-algorithm methods. Given today's new papers below, write a 1-2 sentence synthesis "
        "of what is notable today - themes, standout works, or 'quiet day' if minor. Max 45 words, "
        "no hype, no 'today's papers'.\n\n" + titles
    )
    body = json.dumps({"model": model, "max_tokens": 130,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
        return "".join(b.get("text", "") for b in resp.get("content", [])).strip()
    except Exception:  # noqa: BLE001
        return ""


def write_site_data(items, scope, synthesis, site_dir="site"):
    """Write the day's data + update the manifest the website reads.
      site/data/<YYYY-MM-DD>.json  - full item list for the day
      site/data/index.json         - manifest: [{date, count, synthesis, top:[...]}]
    Idempotent per day (re-running the same date overwrites that day's entry)."""
    data_dir = os.path.join(site_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    day_payload = {"date": today, "scope": scope, "synthesis": synthesis,
                   "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                   "items": items}
    with open(os.path.join(data_dir, f"{today}.json"), "w") as f:
        json.dump(day_payload, f, indent=1)

    manifest_path = os.path.join(data_dir, "index.json")
    manifest = []
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except Exception:  # noqa: BLE001
            manifest = []
    manifest = [m for m in manifest if m.get("date") != today]        # replace today's entry
    manifest.append({
        "date": today, "count": len(items), "synthesis": synthesis,
        "top": [{"title": i.get("title", ""), "relevance": i.get("relevance", 0),
                 "significance": i.get("significance", 0)} for i in items[:3]],
    })
    manifest.sort(key=lambda m: m.get("date", ""), reverse=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=1)
    return data_dir


# ------------------------------- render -----------------------------------

def render_html(items, out_path, scope_label):
    today = datetime.date.today()
    sset = watch_surnames()
    EMDASH = "\u2014"
    MIDDOT = "\u00b7"
    STAR = "\u2605"
    empty_row = '<div class="item">No new CSP papers in this window.</div>'

    def link(i):
        if i.get("src") == "arXiv":
            return i.get("url") or f"https://arxiv.org/abs/{i.get('arxiv_id')}"
        return f"https://doi.org/{i.get('doi')}"

    rows = []
    for i in items:
        authors = i.get("authors", []) or []
        who = ", ".join(authors) + (" et al." if len(authors) >= 3 else "") if authors else EMDASH
        wl = tag_watchlist(i.get("authors_all") or authors, sset)
        wtag = f'<span class="wtag">{STAR} {", ".join(wl)}</span>' if wl else ""
        src = i.get("src", "journal")
        badge = src if src in ("arXiv", "ChemRxiv") else "journal"
        bc = "#C6613F" if src in ("arXiv", "ChemRxiv", "preprint") else "#4a7a6f"
        summ = html.escape(i.get("summary", "")) if i.get("summary") else ""
        rel = i.get("relevance", 0)
        sig = i.get("significance", 0)
        tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in i.get("tags", []))
        scores_html = (
            f'<span class="score rel">relevance {rel}</span>'
            f'<span class="score sig">significance {sig}</span>'
        )
        rows.append(
            f'<div class="item"><div class="meta">'
            f'<span class="badge" style="color:{bc};border-color:{bc}">{badge}</span>'
            f'<span class="date">{i.get("date","")}</span>'
            f'<span class="venue">{html.escape(i.get("venue") or "")}</span>{wtag}</div>'
            f'<a class="title" href="{link(i)}" target="_blank">{html.escape(i.get("title",""))}</a>'
            f'<div class="authors">{html.escape(who)}</div>'
            f'<div class="scores">{scores_html}{tags_html}</div>'
            + (f'<div class="summary"><b>Contribution:</b> {summ}</div>' if summ else "")
            + '</div>'
        )

    n_pre = sum(1 for i in items if i.get("src") in ("arXiv", "ChemRxiv", "preprint"))
    n_oa = len(items) - n_pre
    wl_list = html.escape(", ".join(sorted(WATCHLIST)))
    rows_html = "".join(rows) if rows else empty_row
    sub_line = today.strftime(f'%A {MIDDOT} %B %d, %Y')
    has_summaries = any(i.get("summary") for i in items)
    notes_clause = "; one-line notes are AI-generated from abstracts" if has_summaries else ""
    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CSP digest {EMDASH} {today.isoformat()}</title><style>
body{{font-family:-apple-system,"Segoe UI",sans-serif;background:#FCFCFB;color:#2E2C27;margin:0;line-height:1.5}}
.wrap{{max-width:800px;margin:0 auto;padding:40px 28px 60px}}
h1{{font-size:26px;font-weight:600;margin:0 0 4px}}
.sub{{color:#6B6A63;font-size:14px;margin-bottom:6px}}
.count{{color:#B4B3A8;font-size:13px;margin-bottom:26px}}
.item{{border-top:1px solid #E4E3DC;padding:16px 0}}
.meta{{display:flex;gap:10px;align-items:center;margin-bottom:5px;font-size:12px;flex-wrap:wrap}}
.badge{{border:1px solid;border-radius:3px;padding:1px 7px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}}
.date{{color:#6B6A63}}.venue{{color:#B4B3A8}}.wtag{{color:#C6613F;font-weight:600;font-size:11.5px}}
.title{{font-size:16.5px;font-weight:600;color:#2E2C27;text-decoration:none;display:block;margin-bottom:3px}}
.title:hover{{text-decoration:underline}}
.authors{{color:#6B6A63;font-size:13.5px;margin-bottom:6px}}
.scores{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:7px;align-items:center}}
.score{{font-size:11px;font-weight:600;border-radius:3px;padding:2px 8px}}
.score.rel{{background:#EAF1EF;color:#2f5d52}}
.score.sig{{background:#F6ECE7;color:#9c4a2c}}
.tag{{font-size:11px;color:#5b6b78;background:#EEF1F3;border-radius:10px;padding:2px 9px}}
.summary{{color:#2E2C27;font-size:14px;background:#F4F3EF;border-left:3px solid #C6613F;padding:8px 12px;border-radius:0 4px 4px 0}}
.foot{{margin-top:34px;color:#B4B3A8;font-size:12.5px;border-top:1px solid #E4E3DC;padding-top:14px}}
</style></head><body><div class="wrap">
<h1>CSP literature digest</h1>
<div class="sub">{sub_line} {EMDASH} new work in crystal structure prediction ({scope_label})</div>
<div class="count">{len(items)} papers {MIDDOT} {n_oa} journal {MIDDOT} {n_pre} preprint {MIDDOT} ranked toward GA/evolutionary CSP {MIDDOT} {STAR} = watchlist author</div>
{rows_html}
<div class="foot">Sources: OpenAlex (published + ChemRxiv) and arXiv (preprints), filtered to CSP{notes_clause}. Watchlist: {wl_list}.</div>
</div></body></html>"""
    with open(out_path, "w") as f:
        f.write(doc)
    return out_path


# ------------------------- knowledge-management exports -------------------

def _slug(text, maxlen=80):
    s = re.sub(r"[^\w\s-]", "", text or "").strip()
    s = re.sub(r"\s+", "-", s)
    return (s[:maxlen] or "untitled")


def export_obsidian(items, out_dir):
    """One Markdown note per paper for an Obsidian vault: YAML frontmatter with
    tags/scores/DOI, [[wikilinks]] for authors and field tags (so the graph view
    connects papers sharing methods or authors), and an empty Notes section.
    Also writes a MOC (map-of-content) index note. Returns the directory."""
    os.makedirs(out_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    index_lines = [f"# CSP digest {today}", "", f"{len(items)} papers. Sorted by combined score.", ""]
    for i in items:
        title = i.get("title", "untitled")
        fname = f"{i.get('date','')}-{_slug(title,60)}.md"
        authors = i.get("authors", []) or []
        tags = i.get("tags", [])
        link = (i.get("url") if i.get("src") == "arXiv"
                else f"https://doi.org/{i.get('doi')}")
        # YAML frontmatter: obsidian reads `tags:` and arbitrary fields
        fm = ["---",
              f'title: "{title.replace(chr(34), chr(39))}"',
              f"date: {i.get('date','')}",
              f"source: {i.get('src','')}",
              f"venue: \"{(i.get('venue') or '')}\"",
              f"doi: {i.get('doi','') or ''}",
              f"arxiv: {i.get('arxiv_id','') or ''}",
              f"relevance: {i.get('relevance',0)}",
              f"significance: {i.get('significance',0)}",
              "tags:",
              "  - CSP"]
        for t in tags:
            fm.append(f"  - {t}")
        fm.append("---")
        body = ["", f"# {title}", ""]
        if authors:
            body.append("**Authors:** " + ", ".join(f"[[{a}]]" for a in authors))
        body.append(f"**Link:** {link}")
        body.append(f"**Scores:** relevance {i.get('relevance',0)} / significance {i.get('significance',0)}")
        if tags:
            body.append("**Field:** " + " ".join(f"[[{t}]]" for t in tags))
        body += ["", "## Why it matters", i.get("summary") or "_(no summary)_", ""]
        if i.get("abstract"):
            body += ["## Abstract", "> " + i["abstract"].replace("\n", " "), ""]
        body += ["## My notes", "", "- ", ""]
        with open(os.path.join(out_dir, fname), "w") as f:
            f.write("\n".join(fm + body))
        tag_str = " ".join(f"#{t}" for t in tags)
        index_lines.append(f"- [[{fname[:-3]}]] — relevance {i.get('relevance',0)}, "
                           f"significance {i.get('significance',0)} {tag_str}")
    with open(os.path.join(out_dir, f"_CSP-digest-{today}.md"), "w") as f:
        f.write("\n".join(index_lines) + "\n")
    return out_dir


def _ris_escape(v):
    return (v or "").replace("\n", " ").strip()


def export_zotero_ris(items, out_path):
    """Zotero-importable RIS (File -> Import). One record per paper; TY JOUR for
    journal, GEN for preprints. DOI included so Zotero can enrich metadata."""
    lines = []
    for i in items:
        ty = "JOUR" if i.get("src") == "journal" else "GEN"
        lines.append(f"TY  - {ty}")
        lines.append(f"TI  - {_ris_escape(i.get('title'))}")
        for a in (i.get("authors") or []):
            lines.append(f"AU  - {_ris_escape(a)}")
        if i.get("date"):
            lines.append(f"DA  - {i['date'].replace('-', '/')}")
            lines.append(f"PY  - {i['date'][:4]}")
        if i.get("venue"):
            lines.append(f"JO  - {_ris_escape(i.get('venue'))}")
        if i.get("doi"):
            lines.append(f"DO  - {i['doi']}")
        link = (i.get("url") if i.get("src") == "arXiv"
                else f"https://doi.org/{i.get('doi')}")
        lines.append(f"UR  - {link}")
        if i.get("abstract"):
            lines.append(f"AB  - {_ris_escape(i.get('abstract'))}")
        for t in (["CSP"] + i.get("tags", [])):
            lines.append(f"KW  - {t}")
        lines.append("ER  - ")
        lines.append("")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    return out_path


# -------------------------------- main ------------------------------------

def main():
    days = int(os.environ.get("DIGEST_DAYS", "4"))
    scope = os.environ.get("DIGEST_SCOPE", "molecular").lower()  # molecular-only by default
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

    oa_queries = []
    if scope in ("molecular", "both"):
        oa_queries += QUERIES_MOLECULAR
    if scope in ("inorganic", "both"):
        oa_queries += QUERIES_INORGANIC

    merged = {}

    def add(item, keyfield):
        k = item.get(keyfield)
        if not k:
            return
        if k in merged:
            merged[k]["matched"] = list(set(merged[k].get("matched", []) + item.get("matched", [])))
        else:
            merged[k] = item

    # One OR-combined search instead of a call per query: GitHub's shared
    # runner IPs get 429d by OpenAlex regardless of api_key, so success odds
    # scale with how FEW requests a run needs (10 -> 2).
    combined = " OR ".join(f'"{q}"' for q in oa_queries)
    oa_attempts = oa_failures = 0
    oa_attempts += 2
    try:
        for it in fetch_openalex(combined, since, "article"):
            add(it, "doi")
    except Exception as e:  # noqa: BLE001
        oa_failures += 1
        print(f"[warn] OpenAlex articles (combined): {e}", file=sys.stderr)
    time.sleep(4.0)
    try:
        for it in fetch_openalex(combined, since, "preprint", venue=PREPRINT_VENUE):
            add(it, "doi")
    except Exception as e:  # noqa: BLE001
        oa_failures += 1
        print(f"[warn] ChemRxiv (combined): {e}", file=sys.stderr)

    for q in ARXIV_QUERIES:
        try:
            for it in fetch_arxiv(q, since):
                add(it, "arxiv_id")
        except Exception as e:  # noqa: BLE001
            print(f"[warn] arXiv '{q}': {e}", file=sys.stderr)

    # A day where EVERY OpenAlex query failed and nothing came from any source
    # is an outage, not a quiet day - fail loudly instead of publishing an
    # empty digest that silently overwrites the site's "today".
    if oa_attempts and oa_failures == oa_attempts and not merged:
        print(f"[error] all {oa_attempts} OpenAlex queries failed (rate-limited?) and no "
              f"items from any source - refusing to publish an empty digest.", file=sys.stderr)
        sys.exit(3)

    items = rank_items(list(merged.values()), scope=scope)
    items = summarize(items)
    out = render_html(items, "csp_digest.html", scope_label=scope)
    print(f"Rendered {len(items)} items -> {out}")

    # website data layer (dated JSON + manifest + "what's new today")
    if os.environ.get("BUILD_SITE", "1") != "0":
        synth = daily_synthesis(items)
        d = write_site_data(items, scope, synth)
        print(f"Site data -> {d}/{datetime.date.today().isoformat()}.json (+ index.json)")

    # knowledge-management exports (on by default; disable with EXPORT_*=0)
    if os.environ.get("EXPORT_OBSIDIAN", "1") != "0":
        d = export_obsidian(items, "obsidian_notes")
        print(f"Obsidian notes -> {d}/ ({len(items)} notes + index)")
    if os.environ.get("EXPORT_ZOTERO", "1") != "0":
        z = export_zotero_ris(items, "csp_digest.ris")
        print(f"Zotero RIS -> {z}")

    # machine-readable dump for downstream tooling / knowledge base
    with open("csp_digest.json", "w") as f:
        json.dump(items, f, indent=1)
    print("JSON -> csp_digest.json")


if __name__ == "__main__":
    main()
