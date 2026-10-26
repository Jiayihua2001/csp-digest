#!/usr/bin/env python3
"""Self-contained reading digest: molecular CSP + AI-for-science landmarks.

Two lanes feed one strict reading gate (judge.py):
  mcsp    new molecular crystal structure prediction work from OpenAlex
          (published + ChemRxiv), Crossref (CI fallback) and arXiv.
  ai4sci  broad AI-for-science scouting: ML papers in high-visibility science
          journals (Nature, Science, Nat Mach Intell, ...) and ML x science
          arXiv categories. Deliberately broad - the judge, not the query,
          decides what is worth reading.
Every candidate is scored on the reader's three questions (worth 30 minutes?
inspiring for their work? foundational theory?) and only read/skim verdicts
are published - an empty day is a valid day. A "landmark of the day" from a
curated canon (landmarks.py) gives every day one paper worth 30 minutes.

No platform dependencies: uses public OpenAlex/arXiv APIs directly and the
Anthropic Messages API for summaries. Designed to run in GitHub Actions or
locally.

Environment variables:
  OPENALEX_API_KEY   optional; only for premium OpenAlex accounts (API is free/keyless)
  ANTHROPIC_API_KEY  optional; if set, generates one-line summaries
  OPENALEX_MAILTO    recommended contact email for the OpenAlex polite pool
  DIGEST_DAYS        look-back window in days (default 4)
  DIGEST_SCOPE       "molecular", "inorganic", or "both" (default both)
  JUDGE_MODEL / TRIAGE_MODEL / JUDGE_EFFORT   see judge.py (defaults claude-opus-5-5 /
                     claude-haiku-5-5 / medium); DIGEST_JUDGE=0 publishes unjudged
  JUDGE_REQUIRED     1 = refuse to publish when the judge could not run (CI default)
  LANDMARK_OF_DAY    1 = pick one canon paper per day (see landmarks.py)
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

import judge                      # three-question reading gate (same directory)

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

# AI-for-science lane. Broad on purpose: keyword scouting (the old MLIP queries)
# filled the digest with incremental potential papers. Candidates from here skip
# the CSP regex gates; the three-question judge decides, and most are skipped.
#   journals: ML-flavoured papers in high-visibility science venues
#   arXiv:    ML x science categories, and cs.LG papers about science
AI4SCI_JOURNALS = {               # OpenAlex source id -> (ISSN for the Crossref fallback, AI-native?)
    "S137773608": ("0028-0836", False),   # Nature
    "S3880285": ("0036-8075", False),     # Science
    "S2912241403": ("2522-5839", True),   # Nature Machine Intelligence (fetch everything)
    "S4210228084": ("2662-8457", True),   # Nature Computational Science (fetch everything)
    "S202193212": ("1755-4330", False),   # Nature Chemistry
    "S103895331": ("1476-1122", False),   # Nature Materials
    "S125754415": ("0027-8424", False),   # PNAS
    "S2737427234": ("2375-2548", False),  # Science Advances
    "S111155417": ("0002-7863", False),   # JACS
}
AI4SCI_TERMS = ["machine learning", "deep learning", "neural network", "generative model",
                "language model", "foundation model"]
# Local gate for journal-sourced AI4Sci candidates: Crossref's text search is
# loose ("machine learning" also matches "machine-washed"), so require real ML
# vocabulary in the title/abstract before spending a model call.
AI4SCI_PAT = (r"\b(machine[- ]learn\w*|deep[- ]learn\w*|neural[- ]network\w*|generative|language model\w*|"
              r"foundation model\w*|transformer\w*|diffusion model\w*|reinforcement learning|"
              r"artificial intelligence|AI)\b")
ARXIV_QUERIES_AI4SCI = [
    '(cat:physics.chem-ph OR cat:cond-mat.mtrl-sci OR cat:physics.comp-ph OR cat:q-bio.BM '
    'OR cat:physics.bio-ph) AND (abs:"deep learning" OR abs:"machine learning" OR '
    'abs:"neural network" OR abs:generative OR abs:"language model" OR abs:"foundation model")',
    'cat:cs.LG AND (abs:molecule OR abs:molecular OR abs:protein OR abs:crystal OR abs:materials '
    'OR abs:chemistry OR abs:"scientific discovery" OR abs:"partial differential")',
]
ARXIV_AI4SCI_MAX = 200            # newest N per query; ~12-18 days of volume
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
CROSSREF = "https://api.crossref.org/works"
CHEMRXIV_DOI_PREFIX = "10.26434"

# Circuit breaker: OpenAlex hard-throttles GitHub-runner IPs (429 before auth,
# even with a valid api_key). Once the main fetch fails, all further OpenAlex
# calls (author stats, arXiv enrichment) are skipped so they don't each burn a
# multi-minute backoff ladder, and Crossref takes over as the article source.
_OA_DOWN = False


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


def fetch_openalex(query, since, work_type, venue=None, source_ids=None):
    # Filter by when OpenAlex INDEXED the work (created_date), not its nominal
    # publication_date: OpenAlex lags days-to-weeks, so a short publication_date
    # window misses papers that are, in practice, brand new to the index.
    filt = f"from_created_date:{since},title_and_abstract.search:{query},type:{work_type}"
    if venue == PREPRINT_VENUE:
        filt += f",primary_location.source.id:{CHEMRXIV_SOURCE_ID}"
    if source_ids:                                   # restrict to given journals
        filt += f",primary_location.source.id:{'|'.join(source_ids)}"
    url = OPENALEX + "?" + urllib.parse.urlencode(_oa_params({"filter": filt, "per-page": 100}))
    # OA_TRIES lets CI fail over to Crossref quickly instead of walking the
    # full 429 backoff ladder (GitHub runner IPs are throttled pre-auth).
    data = json.loads(_get(url, tries=int(os.environ.get("OA_TRIES", "5"))))
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


def _jats_strip(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()[:1200]


def fetch_crossref(query, since, kind, issn=None):
    """CI-friendly fallback source. kind: 'journal' or 'chemrxiv'.
    Crossref indexes both journal articles and ChemRxiv preprints (posted-content
    under prefix 10.26434) and does not throttle datacenter IPs the way OpenAlex
    does. Maps records into the same item schema as fetch_openalex."""
    filt = f"from-created-date:{since}," + (
        "type:journal-article" if kind == "journal"
        else f"type:posted-content,prefix:{CHEMRXIV_DOI_PREFIX}")
    if issn:
        filt += f",issn:{issn}"
    params = {"filter": filt, "rows": 50,
              "select": "DOI,title,created,author,container-title,abstract,is-referenced-by-count"}
    if query:                                 # "" = everything in the window (small journals)
        params["query.bibliographic"] = query
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto
    data = json.loads(_get(CROSSREF + "?" + urllib.parse.urlencode(params)))
    out = []
    for w in (data.get("message") or {}).get("items", []):
        doi = (w.get("DOI") or "").lower()
        title = (w.get("title") or [""])[0]
        if not doi or not title:
            continue
        parts = ((w.get("created") or {}).get("date-parts") or [[None]])[0]
        date = "-".join(f"{p:02d}" if i else f"{p:04d}" for i, p in enumerate(parts)) if parts[0] else None
        authors = [" ".join(x for x in (a.get("given"), a.get("family")) if x)
                   for a in (w.get("author") or [])]
        venue = (w.get("container-title") or [""])[0] or ("ChemRxiv" if kind == "chemrxiv" else "")
        out.append({
            "src": "ChemRxiv" if kind == "chemrxiv" else "journal",
            "title": title,
            "date": date,
            "doi": doi,
            "authors": authors[:3],
            "authors_all": authors,
            "corresponding": authors[-1:] if authors else [],
            "cited_by": w.get("is-referenced-by-count") or 0,
            "venue": venue,
            "abstract": _jats_strip(w.get("abstract")),
            "matched": [query],
        })
    return out


def fetch_arxiv(query, since, max_results=25):
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
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
    # Crossref/OpenAlex titles can carry markup and embedded newlines.
    return re.sub(r"\s+", " ", re.sub(r"&lt;.*?&gt;|<[^>]+>", "", t or "")).strip()


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
    if not author_id or _OA_DOWN:
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
    if item.get("src") != "arXiv" or item.get("author_ids") or _OA_DOWN:
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
        # AI4Sci-scouted items skip the CSP regex gates (an MLIP paper rarely
        # says "structure prediction" in its title) - the LLM screen judges
        # them instead, against a higher bar.
        if it.get("ai4sci"):
            if it.get("src") != "arXiv" and not re.search(
                    AI4SCI_PAT, it["title"] + " " + (it.get("abstract") or ""), re.I):
                continue                       # journal text search matched loosely
        else:
            if it.get("src") != "arXiv" and not csp_relevant(it["title"]):
                continue
            if scope == "molecular" and not is_molecular(it):
                continue
            enrich_arxiv_from_openalex(it)
        it["tags"] = keyword_tags(it)
        it["relevance"] = relevance_score(it)
        # AI4Sci candidates are many and get their real scores from the judge;
        # skip the per-author OpenAlex enrichment (one call per author id).
        it["significance"] = 0 if it.get("ai4sci") else significance_score(it, sset)
        it["score"] = it["relevance"] + it["significance"]     # combined sort key
        out.append(it)
    out.sort(key=lambda x: (x.get("score", 0), x.get("date") or ""), reverse=True)
    return out


def write_site_data(items, scope, synthesis, landmark=None, site_dir="site"):
    """Write the day's data + update the manifest the website reads.
      site/data/<YYYY-MM-DD>.json  - full item list (+ landmark) for the day
      site/data/index.json         - manifest: [{date, count, read_count, ..., landmark, top}]
    Idempotent per day (re-running the same date overwrites that day's entry)."""
    data_dir = os.path.join(site_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    today = datetime.date.today().isoformat()

    # First-seen ledger: the day file is a rolling-window view, so papers repeat
    # across days. first_seen/is_new let the UI distinguish "new today" from
    # "still in the window" - without this every quiet day looks broken.
    ledger_path = os.path.join(data_dir, "first_seen.json")
    try:
        ledger = json.load(open(ledger_path))
    except Exception:  # noqa: BLE001
        ledger = {}
    for it in items:
        pid = it.get("doi") or it.get("arxiv_id") or it.get("title") or ""
        if pid and pid not in ledger:
            ledger[pid] = today
        it["first_seen"] = ledger.get(pid, today)
        it["is_new"] = it["first_seen"] == today
    with open(ledger_path, "w") as f:
        json.dump(ledger, f, indent=0, sort_keys=True)

    day_payload = {"date": today, "scope": scope, "synthesis": synthesis,
                   "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                   "landmark": landmark, "items": items}
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
        "date": today, "count": len(items),
        "new_count": sum(1 for i in items if i.get("is_new")),
        "read_count": sum(1 for i in items if i.get("verdict") == "read"),
        "skim_count": sum(1 for i in items if i.get("verdict") == "skim"),
        "synthesis": synthesis,
        "landmark": ({k: landmark.get(k) for k in ("id", "title", "url", "lane", "year", "area")}
                     if landmark else None),
        "top": [{"title": i.get("title", ""), "relevance": i.get("relevance", 0),
                 "significance": i.get("significance", 0), "verdict": i.get("verdict")}
                for i in items[:3]],
    })
    manifest.sort(key=lambda m: m.get("date", ""), reverse=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=1)
    return data_dir


# ------------------------------- render -----------------------------------

LANE_LABEL = {"ai4sci": "AI for Science", "mcsp": "Molecular CSP"}


def _landmark_html(lm):
    """Render the 'landmark of the day' banner (empty if none): the reader's
    three questions answered, plus a 30-minute reading guide."""
    if not lm:
        return ""
    authors = lm.get("authors") or []
    et = " et al." if lm.get("authors_n", len(authors)) > 3 else ""
    who = ", ".join(authors) + et
    kind = "AI for Science landmark" if lm.get("lane") == "ai4sci" else "Molecular-CSP classic"
    venue = f", {lm['venue']}" if lm.get("venue") else ""
    return (
        '<div class="classic">'
        f'<div class="k">&#128218; Landmark of the day &mdash; {html.escape(kind)}</div>'
        f'<div class="ct"><a href="{html.escape(lm.get("url", "#"))}" target="_blank">'
        f'{html.escape(lm.get("title", ""))}</a></div>'
        f'<div class="cm">{html.escape(who)} &nbsp;({lm.get("year", "")}, {lm.get("citations", "")} citations'
        f'{html.escape(venue)})</div>'
        f'<p><b>Worth 30 minutes?</b> {html.escape(lm.get("worth_30_min", ""))}</p>'
        f'<p><b>What it could inspire:</b> {html.escape(lm.get("inspiration", ""))}</p>'
        f'<p><b>Foundations to learn:</b> {html.escape(lm.get("foundations", ""))}</p>'
        f'<p><b>30-minute reading guide:</b> {html.escape(lm.get("reading_guide", ""))}</p>'
        '</div>'
    )


def _scores_html(i):
    """Three-question chips when judged; legacy relevance/significance otherwise."""
    r = i.get("rubric") or {}
    if r.get("q1") is not None:
        lane = LANE_LABEL.get(i.get("lane"), "")
        return (f'<span class="score sig">worth 30 min {r.get("q1")}/5</span>'
                f'<span class="score rel">inspiring {r.get("q2")}/5</span>'
                f'<span class="score fnd">foundational {r.get("q3")}/5</span>'
                + (f'<span class="lane">{html.escape(lane)}</span>' if lane else ""))
    return (f'<span class="score rel">relevance {i.get("relevance", 0)}</span>'
            f'<span class="score sig">significance {i.get("significance", 0)}</span>')


def render_html(items, out_path, scope_label, landmark=None):
    today = datetime.date.today()
    sset = watch_surnames()
    EMDASH = "\u2014"
    MIDDOT = "\u00b7"
    STAR = "\u2605"

    def link(i):
        if i.get("src") == "arXiv":
            return i.get("url") or f"https://arxiv.org/abs/{i.get('arxiv_id')}"
        return f"https://doi.org/{i.get('doi')}"

    def row(i):
        authors = i.get("authors", []) or []
        who = ", ".join(authors) + (" et al." if len(authors) >= 3 else "") if authors else EMDASH
        wl = tag_watchlist(i.get("authors_all") or authors, sset)
        wtag = f'<span class="wtag">{STAR} {", ".join(wl)}</span>' if wl else ""
        src = i.get("src", "journal")
        badge = src if src in ("arXiv", "ChemRxiv") else "journal"
        bc = "#C6613F" if src in ("arXiv", "ChemRxiv", "preprint") else "#4a7a6f"
        summ = html.escape(i.get("summary", "")) if i.get("summary") else ""
        why = html.escape((i.get("rubric") or {}).get("why") or "")
        tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in i.get("tags", []))
        return (
            f'<div class="item"><div class="meta">'
            f'<span class="badge" style="color:{bc};border-color:{bc}">{badge}</span>'
            f'<span class="date">{i.get("date", "")}</span>'
            + ('<span class="newtag">NEW</span>' if i.get("is_new") else '')
            + f'<span class="venue">{html.escape(i.get("venue") or "")}</span>{wtag}</div>'
            f'<a class="title" href="{link(i)}" target="_blank">{html.escape(i.get("title", ""))}</a>'
            f'<div class="authors">{html.escape(who)}</div>'
            f'<div class="scores">{_scores_html(i)}{tags_html}</div>'
            + (f'<div class="summary"><b>Contribution:</b> {summ}</div>' if summ else "")
            + (f'<div class="why">{why}</div>' if why else "")
            + '</div>'
        )

    groups = [("read", "Worth reading"), ("skim", "Set aside &mdash; skim if curious"),
              (None, "Unjudged")]
    sections = []
    for verdict, label in groups:
        rows = [row(i) for i in items if i.get("verdict") == verdict]
        if rows:
            sections.append(f'<div class="group">{label} ({len(rows)})</div>' + "".join(rows))
    n_read = sum(1 for i in items if i.get("verdict") == "read")
    n_skim = sum(1 for i in items if i.get("verdict") == "skim")
    rows_html = "".join(sections) or (
        '<div class="item">Nothing worth 30 minutes in this window &mdash; a quiet day is a good day.</div>')
    wl_list = html.escape(", ".join(sorted(WATCHLIST)))
    sub_line = today.strftime(f'%A {MIDDOT} %B %d, %Y')
    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reading digest {EMDASH} {today.isoformat()}</title><style>
body{{font-family:-apple-system,"Segoe UI",sans-serif;background:#FCFCFB;color:#2E2C27;margin:0;line-height:1.5}}
.wrap{{max-width:800px;margin:0 auto;padding:40px 28px 60px}}
h1{{font-size:26px;font-weight:600;margin:0 0 4px}}
.sub{{color:#6B6A63;font-size:14px;margin-bottom:6px}}
.count{{color:#B4B3A8;font-size:13px;margin-bottom:26px}}
.group{{margin:26px 0 4px;font-size:11.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#6B6A63}}
.item{{border-top:1px solid #E4E3DC;padding:16px 0}}
.meta{{display:flex;gap:10px;align-items:center;margin-bottom:5px;font-size:12px;flex-wrap:wrap}}
.badge{{border:1px solid;border-radius:3px;padding:1px 7px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}}
.date{{color:#6B6A63}}.venue{{color:#B4B3A8}}.wtag{{color:#C6613F;font-weight:600;font-size:11.5px}}
.newtag{{background:#B23A2E;color:#fff;font-size:10px;font-weight:700;border-radius:3px;padding:1px 6px;letter-spacing:.5px}}
.title{{font-size:16.5px;font-weight:600;color:#2E2C27;text-decoration:none;display:block;margin-bottom:3px}}
.title:hover{{text-decoration:underline}}
.authors{{color:#6B6A63;font-size:13.5px;margin-bottom:6px}}
.scores{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:7px;align-items:center}}
.score{{font-size:11px;font-weight:600;border-radius:3px;padding:2px 8px}}
.score.rel{{background:#EAF1EF;color:#2f5d52}}
.score.sig{{background:#F6ECE7;color:#9c4a2c}}
.score.fnd{{background:#EEF1F3;color:#3f4e5c}}
.lane{{font-size:10.5px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:#6B6A63;border:1px solid #E4E3DC;border-radius:3px;padding:1px 6px}}
.tag{{font-size:11px;color:#5b6b78;background:#EEF1F3;border-radius:10px;padding:2px 9px}}
.summary{{color:#2E2C27;font-size:14px;background:#F4F3EF;border-left:3px solid #C6613F;padding:8px 12px;border-radius:0 4px 4px 0}}
.why{{color:#6B6A63;font-size:13px;margin-top:6px}}
.classic{{margin:18px 0 6px;background:#F0F4F8;border:1px solid #D3DEE7;border-left:4px solid #4a7a6f;border-radius:6px;padding:14px 16px}}
.classic .k{{font-size:11.5px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:#4a7a6f;margin-bottom:6px}}
.classic .ct{{font-size:16px;font-weight:600;margin-bottom:3px}}.classic .ct a{{color:#2E2C27;text-decoration:none}}
.classic .cm{{color:#6B6A63;font-size:13px;margin-bottom:8px}}
.classic p{{margin:5px 0;font-size:13.5px}}.classic b{{color:#3a5c53}}
.foot{{margin-top:34px;color:#B4B3A8;font-size:12.5px;border-top:1px solid #E4E3DC;padding-top:14px}}
</style></head><body><div class="wrap">
<h1>Reading digest</h1>
<div class="sub">{sub_line} {EMDASH} molecular CSP ({scope_label}) + AI for Science, gated on three questions</div>
<div class="count">{n_read} worth reading {MIDDOT} {n_skim} set aside {MIDDOT} {len(items)} kept of all candidates {MIDDOT} {STAR} = watchlist author</div>
{_landmark_html(landmark)}
{rows_html}
<div class="foot">Sources: OpenAlex / Crossref (journals + ChemRxiv) and arXiv. Each paper is judged on: worth 30 minutes? inspiring for your work or AI4Sci? foundational theory? Scores, contribution lines and the landmark explanation are model-generated from titles and abstracts. Watchlist: {wl_list}.</div>
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
              f"verdict: {i.get('verdict','')}",
              f"worth_30_min: {(i.get('rubric') or {}).get('q1','')}",
              f"inspiring: {(i.get('rubric') or {}).get('q2','')}",
              f"foundational: {(i.get('rubric') or {}).get('q3','')}",
              f"lane: {i.get('lane','')}",
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
        if (i.get("rubric") or {}).get("why"):
            body += ["**Judge:** " + i["rubric"]["why"], ""]
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
    global _OA_DOWN
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

    cr_ok = 0
    if oa_failures == oa_attempts:
        # OpenAlex is unreachable (throttled CI IP). Trip the breaker so the
        # per-author/per-item enrichment calls don't grind, and fetch from
        # Crossref instead.
        _OA_DOWN = True
        print("[info] OpenAlex down for this run - falling back to Crossref", file=sys.stderr)
        for q in oa_queries:
            for kind in ("journal", "chemrxiv"):
                try:
                    for it in fetch_crossref(q, since, kind):
                        add(it, "doi")
                    cr_ok += 1
                except Exception as e:  # noqa: BLE001
                    print(f"[warn] Crossref {kind} '{q}': {e}", file=sys.stderr)
                time.sleep(1.0)

    # --- AI-for-science lane (flagged; skips the CSP regex gates, judged strictly) ---
    def _add_ai4sci(fetched):
        for it in fetched:
            it["ai4sci"] = True
            add(it, "doi" if it.get("doi") else "arxiv_id")

    if not _OA_DOWN:
        time.sleep(4.0)
        try:
            terms = " OR ".join(f'"{t}"' for t in AI4SCI_TERMS)
            _add_ai4sci(fetch_openalex(terms, since, "article", source_ids=list(AI4SCI_JOURNALS)))
        except Exception as e:  # noqa: BLE001
            print(f"[warn] OpenAlex ai4sci journals: {e}", file=sys.stderr)
    else:
        # Crossref ANDs every query term, so ask one short phrase at a time;
        # AI-native journals are small enough to fetch whole.
        for issn, ai_native in AI4SCI_JOURNALS.values():
            for q in ([""] if ai_native else AI4SCI_TERMS):
                try:
                    _add_ai4sci(fetch_crossref(q, since, "journal", issn=issn))
                except Exception as e:  # noqa: BLE001
                    print(f"[warn] Crossref ai4sci issn {issn} '{q}': {e}", file=sys.stderr)
                time.sleep(0.6)

    for q in ARXIV_QUERIES:
        try:
            for it in fetch_arxiv(q, since):
                add(it, "arxiv_id")
        except Exception as e:  # noqa: BLE001
            print(f"[warn] arXiv '{q}': {e}", file=sys.stderr)

    for q in ARXIV_QUERIES_AI4SCI:
        try:
            _add_ai4sci(fetch_arxiv(q, since, max_results=ARXIV_AI4SCI_MAX))
        except Exception as e:  # noqa: BLE001
            print(f"[warn] arXiv ai4sci '{q[:50]}...': {e}", file=sys.stderr)

    # A day where EVERY OpenAlex query failed and nothing came from any source
    # is an outage, not a quiet day - fail loudly instead of publishing an
    # empty digest that silently overwrites the site's "today".
    if oa_attempts and oa_failures == oa_attempts and cr_ok == 0 and not merged:
        print(f"[error] OpenAlex AND Crossref both failed and no items from any source - "
              f"refusing to publish an empty digest.", file=sys.stderr)
        sys.exit(3)

    items = rank_items(list(merged.values()), scope=scope)
    n_ai = sum(1 for i in items if i.get("ai4sci"))
    print(f"{len(items)} candidates after regex gates ({n_ai} AI4Sci, {len(items) - n_ai} MCSP)")

    # The reading gate: three questions per paper, read/skim kept, skip dropped.
    items, judge_ok = judge.run(items)
    if not judge_ok and os.environ.get("JUDGE_REQUIRED") == "1":
        print("[error] the reading judge could not run - refusing to publish unjudged papers "
              "as 'worth reading' (DIGEST_JUDGE=0 publishes without judging)", file=sys.stderr)
        sys.exit(3)

    landmark = None
    if os.environ.get("LANDMARK_OF_DAY") == "1":
        try:
            from landmarks import landmark_of_the_day
            landmark = landmark_of_the_day()
            if landmark:
                print(f"Landmark of the day ({landmark['lane']}): {landmark['title'][:60]}")
        except Exception as e:  # noqa: BLE001 - never break the digest
            print(f"[warn] landmark of the day skipped: {e}", file=sys.stderr)
    out = render_html(items, "csp_digest.html", scope_label=scope, landmark=landmark)
    print(f"Rendered {len(items)} items -> {out}")

    # website data layer (dated JSON + manifest + "what's worth reading today")
    if os.environ.get("BUILD_SITE", "1") != "0":
        synth = judge.daily_synthesis(items, landmark)
        d = write_site_data(items, scope, synth, landmark=landmark)
        print(f"Site data -> {d}/{datetime.date.today().isoformat()}.json (+ index.json)")

    # knowledge-management exports: only what is worth reading (unjudged = all)
    to_export = [i for i in items if i.get("verdict", "read") == "read"]
    if os.environ.get("EXPORT_OBSIDIAN", "1") != "0":
        d = export_obsidian(to_export, "obsidian_notes")
        print(f"Obsidian notes -> {d}/ ({len(to_export)} notes + index)")
    if os.environ.get("EXPORT_ZOTERO", "1") != "0":
        z = export_zotero_ris(to_export, "csp_digest.ris")
        print(f"Zotero RIS -> {z}")

    # machine-readable dump for downstream tooling / knowledge base
    with open("csp_digest.json", "w") as f:
        json.dump(items, f, indent=1)
    print("JSON -> csp_digest.json")


if __name__ == "__main__":
    main()
