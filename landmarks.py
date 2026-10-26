#!/usr/bin/env python3
"""
Landmark of the day: ONE paper worth 30 minutes, every day, drawn from a canon.

Quality and novelty matter more than the date, so this lane ignores recency
entirely. Two pools alternate day by day:

  ai4sci  the curated seed list below - breakthrough and foundational papers of
          AI for science and the theory behind them (AlphaFold, flow matching,
          diffusion, Boltzmann generators, GNoME/MatterGen, AlphaGo-style search,
          evolutionary-computation theory, ...). Seeds are only DOIs / arXiv ids
          plus a title hint; `refresh` resolves each through OpenAlex and keeps
          it only when the resolved title matches the hint, so every record the
          reader sees is a real bibliographic entry, never a model's memory.
  mcsp    the well-cited molecular-CSP classics pool mined by classic.py.

Each day a frontier model picks the single most valuable UNSEEN paper for this
reader and explains it through the reader's three questions (worth 30 minutes?
inspiring for their work? foundational theory to learn?) plus a 30-minute
reading guide. "None of these is worth it" is a legitimate answer: the banner
is then simply absent. Picks are recorded in site/data/landmarks_seen.json.

Usage (stdlib only):
  OPENALEX_API_KEY=...  python3 landmarks.py refresh            # rebuild review/landmarks_pool.json
  ANTHROPIC_API_KEY=... python3 landmarks.py pick [--lane ai4sci|mcsp] [--commit]
Env: LANDMARK_LANE (alternate | ai4sci | mcsp), LANDMARK_MODEL (claude-opus-5-5),
LANDMARK_EFFORT (high; "" omits the field).
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import judge                      # API layer + reader profile (same directory)

POOL_PATH = os.path.join("review", "landmarks_pool.json")
SEEN_PATH = os.path.join("site", "data", "landmarks_seen.json")
OPENALEX_WORKS = "https://api.openalex.org/works"
MODEL_DEFAULT = "claude-opus-5-5"
MATCH_THRESHOLD = 0.6            # identifier-resolved record vs. title hint
TITLE_SEARCH_THRESHOLD = 0.8     # title-search fallback: no identifier, so demand near-identity
CANDIDATES_SHOWN = 40

# id: "doi:<doi>" or "arxiv:<id>". title: hint used ONLY to verify the resolved record.
SEEDS = [
    # --- generative-modeling theory ---
    {"id": "arxiv:2210.02747", "area": "generative-theory", "title": "Flow Matching for Generative Modeling"},
    {"id": "arxiv:2006.11239", "area": "generative-theory", "title": "Denoising Diffusion Probabilistic Models"},
    {"id": "arxiv:2011.13456", "area": "generative-theory", "title": "Score-Based Generative Modeling through Stochastic Differential Equations"},
    {"id": "arxiv:2209.03003", "area": "generative-theory", "title": "Flow Straight and Fast: Learning to Generate and Transfer Data with Rectified Flow"},
    {"id": "arxiv:2303.08797", "area": "generative-theory", "title": "Stochastic Interpolants: A Unifying Framework for Flows and Diffusions"},
    {"id": "arxiv:2302.03660", "area": "generative-theory", "title": "Riemannian Flow Matching on General Geometries"},
    {"id": "arxiv:2010.02502", "area": "generative-theory", "title": "Denoising Diffusion Implicit Models"},
    {"id": "arxiv:2207.12598", "area": "generative-theory", "title": "Classifier-Free Diffusion Guidance"},
    {"id": "arxiv:2206.00364", "area": "generative-theory", "title": "Elucidating the Design Space of Diffusion-Based Generative Models"},
    {"id": "arxiv:1503.03585", "area": "generative-theory", "title": "Deep Unsupervised Learning using Nonequilibrium Thermodynamics"},
    {"id": "arxiv:1312.6114", "area": "generative-theory", "title": "Auto-Encoding Variational Bayes"},
    {"id": "arxiv:1406.2661", "area": "generative-theory", "title": "Generative Adversarial Networks"},
    {"id": "arxiv:1505.05770", "area": "generative-theory", "title": "Variational Inference with Normalizing Flows"},
    {"id": "arxiv:2112.10752", "area": "generative-theory", "title": "High-Resolution Image Synthesis with Latent Diffusion Models"},
    {"id": "arxiv:2106.04399", "area": "generative-theory", "title": "Flow Network based Generative Models for Non-Iterative Diverse Candidate Generation"},
    {"id": "arxiv:2407.15595", "area": "generative-theory", "title": "Discrete Flow Matching"},
    # --- ML foundations ---
    {"id": "arxiv:1706.03762", "area": "ml-foundations", "title": "Attention Is All You Need"},
    {"id": "arxiv:1806.07366", "area": "ml-foundations", "title": "Neural Ordinary Differential Equations"},
    {"id": "arxiv:2001.08361", "area": "ml-foundations", "title": "Scaling Laws for Neural Language Models"},
    {"id": "arxiv:1806.01261", "area": "ml-foundations", "title": "Relational inductive biases, deep learning, and graph networks"},
    {"id": "doi:10.1038/nature14539", "area": "ml-foundations", "title": "Deep learning"},
    {"id": "arxiv:1704.01212", "area": "ml-foundations", "title": "Neural Message Passing for Quantum Chemistry"},
    {"id": "arxiv:1802.08219", "area": "ml-foundations", "title": "Tensor field networks: Rotation- and translation-equivariant neural networks for 3D point clouds"},
    {"id": "arxiv:2102.09844", "area": "ml-foundations", "title": "E(n) Equivariant Graph Neural Networks"},
    {"id": "arxiv:2006.10503", "area": "ml-foundations", "title": "SE(3)-Transformers: 3D Roto-Translation Equivariant Attention Networks"},
    {"id": "arxiv:2010.08895", "area": "ml-foundations", "title": "Fourier Neural Operator for Parametric Partial Differential Equations"},
    {"id": "doi:10.1016/j.jcp.2018.10.045", "area": "ml-foundations", "title": "Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations"},
    {"id": "arxiv:2002.09405", "area": "ml-foundations", "title": "Learning to Simulate Complex Physics with Graph Networks"},
    # --- search, evolution, discovery by search + learning (closest to GA-based CSP) ---
    {"id": "doi:10.1038/nature16961", "area": "search-and-evolution", "title": "Mastering the game of Go with deep neural networks and tree search"},
    {"id": "doi:10.1038/nature24270", "area": "search-and-evolution", "title": "Mastering the game of Go without human knowledge"},
    {"id": "doi:10.1038/s41586-022-05172-4", "area": "search-and-evolution", "title": "Discovering faster matrix multiplication algorithms with reinforcement learning"},
    {"id": "doi:10.1038/s41586-023-06924-6", "area": "search-and-evolution", "title": "Mathematical discoveries from program search with large language models"},
    {"id": "doi:10.1038/s41586-023-06747-5", "area": "search-and-evolution", "title": "Solving olympiad geometry without human demonstrations"},
    {"id": "arxiv:2506.13131", "area": "search-and-evolution", "title": "AlphaEvolve: A coding agent for scientific and algorithmic discovery"},
    {"id": "arxiv:2206.08896", "area": "search-and-evolution", "title": "Evolution through Large Models"},
    {"id": "arxiv:1504.04909", "area": "search-and-evolution", "title": "Illuminating search spaces by mapping elites"},
    {"id": "doi:10.1162/EVCO_a_00025", "area": "search-and-evolution", "title": "Abandoning Objectives: Evolution Through the Search for Novelty Alone"},
    {"id": "doi:10.1109/4235.996017", "area": "search-and-evolution", "title": "A fast and elitist multiobjective genetic algorithm: NSGA-II"},
    {"id": "doi:10.1162/106365601750190398", "area": "search-and-evolution", "title": "Completely Derandomized Self-Adaptation in Evolution Strategies"},
    {"id": "doi:10.1109/JPROC.2015.2494218", "area": "search-and-evolution", "title": "Taking the Human Out of the Loop: A Review of Bayesian Optimization"},
    {"id": "doi:10.1021/jp970984n", "area": "search-and-evolution", "title": "Global Optimization by Basin-Hopping and the Lowest Energy Structures of Lennard-Jones Clusters Containing up to 110 Atoms"},
    {"id": "arxiv:1712.06567", "area": "search-and-evolution", "title": "Deep Neuroevolution: Genetic Algorithms Are a Competitive Alternative for Training Deep Neural Networks for Reinforcement Learning"},
    # --- protein structure & design (the AlphaFold tier) ---
    {"id": "doi:10.1038/s41586-021-03819-2", "area": "protein", "title": "Highly accurate protein structure prediction with AlphaFold"},
    {"id": "doi:10.1038/s41586-024-07487-w", "area": "protein", "title": "Accurate structure prediction of biomolecular interactions with AlphaFold 3"},
    {"id": "doi:10.1038/s41586-023-06415-8", "area": "protein", "title": "De novo design of protein structure and function with RFdiffusion"},
    {"id": "doi:10.1126/science.ade2574", "area": "protein", "title": "Evolutionary-scale prediction of atomic-level protein structure with a language model"},
    {"id": "doi:10.1073/pnas.2016239118", "area": "protein", "title": "Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences"},
    {"id": "doi:10.1126/science.ads0018", "area": "protein", "title": "Simulating 500 million years of evolution with a language model"},
    {"id": "doi:10.1126/science.adv9817", "area": "protein", "title": "Scalable emulation of protein equilibrium ensembles with generative deep learning"},
    {"id": "arxiv:2210.01776", "area": "protein", "title": "DiffDock: Diffusion Steps, Twists, and Turns for Molecular Docking"},
    # --- materials & molecular generation / discovery ---
    {"id": "doi:10.1038/s41586-023-06735-9", "area": "materials-discovery", "title": "Scaling deep learning for materials discovery"},
    {"id": "doi:10.1038/s41586-025-08628-x", "area": "materials-discovery", "title": "A generative model for inorganic materials design"},
    {"id": "arxiv:2110.06197", "area": "materials-discovery", "title": "Crystal Diffusion Variational Autoencoder for Periodic Material Generation"},
    {"id": "arxiv:2309.04475", "area": "materials-discovery", "title": "Crystal Structure Prediction by Joint Equivariant Diffusion"},
    {"id": "arxiv:2406.04713", "area": "materials-discovery", "title": "FlowMM: Generating Materials with Riemannian Flow Matching"},
    {"id": "arxiv:2402.04379", "area": "materials-discovery", "title": "Fine-Tuned Language Models Generate Stable Inorganic Materials as Text"},
    {"id": "arxiv:2403.15734", "area": "materials-discovery", "title": "Space Group Informed Transformer for Crystalline Materials Generation"},
    {"id": "arxiv:2203.17003", "area": "materials-discovery", "title": "Equivariant Diffusion for Molecule Generation in 3D"},
    {"id": "arxiv:2206.01729", "area": "materials-discovery", "title": "Torsional Diffusion for Molecular Conformer Generation"},
    {"id": "doi:10.1103/PhysRevLett.120.145301", "area": "materials-discovery", "title": "Crystal Graph Convolutional Neural Networks for an Accurate and Interpretable Prediction of Material Properties"},
    {"id": "doi:10.1038/s41586-023-06734-w", "area": "materials-discovery", "title": "An autonomous laboratory for the accelerated synthesis of novel materials"},
    {"id": "doi:10.1038/s41586-018-0337-2", "area": "materials-discovery", "title": "Machine learning for molecular and materials science"},
    {"id": "arxiv:2308.14920", "area": "materials-discovery", "title": "Matbench Discovery - A framework to evaluate machine learning crystal stability predictions"},
    {"id": "doi:10.1038/s41586-023-06887-8", "area": "materials-discovery", "title": "Discovery of a structural class of antibiotics with explainable deep learning"},
    # --- simulation, sampling, potentials (foundations only, not architectures) ---
    {"id": "doi:10.1126/science.aaw1147", "area": "simulation-and-sampling", "title": "Boltzmann generators: Sampling equilibrium states of many-body systems with deep learning"},
    {"id": "arxiv:2306.15030", "area": "simulation-and-sampling", "title": "Equivariant flow matching"},
    {"id": "arxiv:2406.14426", "area": "simulation-and-sampling", "title": "Transferable Boltzmann Generators"},
    {"id": "doi:10.1103/PhysRevLett.98.146401", "area": "simulation-and-sampling", "title": "Generalized Neural-Network Representation of High-Dimensional Potential-Energy Surfaces"},
    {"id": "doi:10.1103/PhysRevLett.104.136403", "area": "simulation-and-sampling", "title": "Gaussian Approximation Potentials: The Accuracy of Quantum Mechanics, without the Electrons"},
    {"id": "doi:10.1038/s41467-022-29939-5", "area": "simulation-and-sampling", "title": "E(3)-equivariant graph neural networks for data-efficient and accurate interatomic potentials"},
    {"id": "arxiv:2206.07697", "area": "simulation-and-sampling", "title": "MACE: Higher Order Equivariant Message Passing Neural Networks for Fast and Accurate Force Fields"},
    {"id": "arxiv:2401.00096", "area": "simulation-and-sampling", "title": "A foundation model for atomistic materials chemistry"},
    {"id": "doi:10.1103/PhysRevLett.120.143001", "area": "simulation-and-sampling", "title": "Deep Potential Molecular Dynamics: A Scalable Model with the Accuracy of Quantum Mechanics"},
    {"id": "doi:10.1126/sciadv.1603015", "area": "simulation-and-sampling", "title": "Machine learning of accurate energy-conserving molecular force fields"},
    {"id": "arxiv:1706.08566", "area": "simulation-and-sampling", "title": "SchNet: A continuous-filter convolutional neural network for modeling quantum interactions"},
    {"id": "arxiv:2506.23971", "area": "simulation-and-sampling", "title": "UMA: A Family of Universal Models for Atoms"},
    {"id": "doi:10.1038/s42256-023-00716-x", "area": "simulation-and-sampling", "title": "CHGNet as a pretrained universal neural network potential for charge-informed atomistic modelling"},
    {"id": "doi:10.1038/s43588-022-00349-3", "area": "simulation-and-sampling", "title": "A universal graph deep learning interatomic potential for the periodic table"},
    # --- AI agents / autonomous science ---
    {"id": "doi:10.1038/s41586-023-06792-0", "area": "ai-agents-for-science", "title": "Autonomous chemical research with large language models"},
    {"id": "doi:10.1038/s41586-023-06221-2", "area": "ai-agents-for-science", "title": "Scientific discovery in the age of artificial intelligence"},
    {"id": "doi:10.1038/s42256-024-00832-8", "area": "ai-agents-for-science", "title": "Augmenting large language models with chemistry tools"},
    # --- other AI4Sci landmarks, data infrastructure ---
    {"id": "doi:10.1126/science.adi2336", "area": "other-ai4sci", "title": "Learning skillful medium-range global weather forecasting"},
    {"id": "doi:10.1038/s41586-023-06185-3", "area": "other-ai4sci", "title": "Accurate medium-range global weather forecasting with 3D neural networks"},
    {"id": "doi:10.1038/sdata.2014.22", "area": "data-and-benchmarks", "title": "Quantum chemistry structures and properties of 134 kilo molecules"},
    {"id": "doi:10.1021/acscatal.0c04525", "area": "data-and-benchmarks", "title": "Open Catalyst 2020 (OC20) Dataset and Community Challenges"},
    {"id": "doi:10.1063/1.4812323", "area": "data-and-benchmarks", "title": "Commentary: The Materials Project: A materials genome approach to accelerating materials innovation"},
]

# ------------------------------- resolving --------------------------------

_STOP = {"a", "an", "the", "of", "for", "and", "on", "in", "to", "with", "by", "using"}


def title_match_score(a: str, b: str) -> float:
    """Jaccard/containment blend in [0,1] (same rule as review/corpus.py)."""
    tok = lambda t: {w for w in re.findall(r"[a-z0-9]+", (t or "").lower()) if w not in _STOP}  # noqa: E731
    ta, tb = tok(a), tok(b)
    if not ta or not tb:
        return 0.0
    if ta == tb:                        # short titles ("Deep learning") match exactly
        return 1.0
    inter = len(ta & tb)
    if inter < 3:
        return inter / max(len(ta), len(tb)) * 0.5
    return min(1.0, max(inter / max(len(ta), len(tb)), 0.92 * inter / min(len(ta), len(tb))))


def _http_get(url: str, tries: int = 4, timeout: int = 45) -> bytes:
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "csp-digest-landmarks/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(min(120.0, 15.0 * (2 ** t)) if "429" in str(e) else 1.5 * (t + 1))
    raise RuntimeError(f"GET failed: {last}")


def _abstract(inv: dict) -> str:
    if not inv:
        return ""
    ws = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in ws)[:600]


def _oa_params(extra: dict) -> dict:
    p = {"select": "id,title,publication_year,doi,ids,authorships,cited_by_count,primary_location,"
                   "abstract_inverted_index"}
    if os.environ.get("OPENALEX_API_KEY"):
        p["api_key"] = os.environ["OPENALEX_API_KEY"]
    p.update(extra)
    return p


def _record(seed: dict, w: dict, match: float) -> dict:
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    m = re.match(r"10\.48550/arxiv\.(.+)$", doi, re.I)      # DataCite DOI of an arXiv record
    arxiv_id = m.group(1) if m else ""
    venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    authors = [a["author"]["display_name"] for a in w.get("authorships", []) if a.get("author")]
    url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else f"https://doi.org/{doi}"
    return {"id": seed["id"], "doi": doi, "arxiv_id": arxiv_id, "url": url, "area": seed["area"],
            "title": w.get("title") or "", "year": w.get("publication_year"),
            "citations": w.get("cited_by_count") or 0, "venue": venue,
            "authors": authors[:3], "authors_n": len(authors),
            "abstract": _abstract(w.get("abstract_inverted_index")),
            "seed_title": seed["title"], "match": round(match, 2)}


def resolve_seed(seed: dict, fetch=None) -> dict:
    """Resolve one seed via OpenAlex: by DOI (arXiv ids map to their DataCite
    DOI 10.48550/arxiv.<id>), then by title search. Returns the record or
    {'id', 'error'} when nothing matches the hint well enough."""
    fetch = fetch or _http_get
    ident = seed["id"]
    doi = ident[4:] if ident.startswith("doi:") else "10.48550/arxiv." + ident[6:]
    work = None
    try:
        url = (OPENALEX_WORKS + "/doi:" + urllib.parse.quote(doi.lower(), safe="")
               + "?" + urllib.parse.urlencode(_oa_params({})))
        work = json.loads(fetch(url))
    except Exception:  # noqa: BLE001 - fall through to title search
        work = None
    note = ""
    if work and work.get("title"):
        m = title_match_score(seed["title"], work["title"])
        if m >= MATCH_THRESHOLD:
            return _record(seed, work, 1.0)
        # OpenAlex occasionally files a wrong record under an arXiv DOI; fall
        # through to a title search rather than trusting the identifier.
        note = f" (DOI record has a different title: {work['title'][:60]!r})"
    try:
        q = _oa_params({"search": re.sub(r"[^A-Za-z0-9 ]+", " ", seed["title"]), "per-page": 5})
        data = json.loads(fetch(OPENALEX_WORKS + "?" + urllib.parse.urlencode(q)))
    except Exception as e:  # noqa: BLE001
        return {"id": ident, "error": f"lookup failed: {e}"}
    # Among near-identical titles prefer the most-cited record (the canonical
    # entry, not a repost); a merely similar title is never accepted here.
    scored = [(title_match_score(seed["title"], w.get("title") or ""), w.get("cited_by_count") or 0, w)
              for w in data.get("results", [])]
    good = sorted((x for x in scored if x[0] >= TITLE_SEARCH_THRESHOLD), key=lambda x: (x[1], x[0]), reverse=True)
    if good:
        return _record(seed, good[0][2], good[0][0])
    best_m = max((x[0] for x in scored), default=0.0)
    return {"id": ident, "error": f"no confident title match (best {best_m:.2f}){note}"}


def refresh_pool(fetch=None, out: str = POOL_PATH, seeds: list = None, pause: float = 0.7,
                 log=print) -> dict:
    """Resolve every seed and write the pool file. Unresolved seeds are listed
    separately so they can be fixed; they never reach the reader."""
    pool, unresolved = [], []
    seen_ids = set()
    for s in seeds or SEEDS:
        if s["id"] in seen_ids:
            continue
        seen_ids.add(s["id"])
        rec = resolve_seed(s, fetch=fetch)
        if rec.get("error"):
            unresolved.append(rec)
            log(f"  ?? {s['id']}: {rec['error']}")
        else:
            pool.append(rec)
            log(f"  ok {s['id']}: {rec['title'][:70]} ({rec['year']}, {rec['citations']} cites)")
        time.sleep(pause)
    data = {"mined": datetime.date.today().isoformat(), "pool": pool, "unresolved": unresolved}
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    log(f"pool: {len(pool)} resolved, {len(unresolved)} unresolved -> {out}")
    return data


# --------------------------------- pools ----------------------------------

def load_pool(lane: str, pool_path: str = POOL_PATH) -> list:
    if lane == "ai4sci":
        try:
            with open(pool_path) as f:
                return json.load(f).get("pool", [])
        except Exception:  # noqa: BLE001
            return []
    import classic                               # MCSP classics (committed cache)
    out = []
    for c in classic._pool_cached():
        out.append({"id": "doi:" + c["doi"], "doi": c["doi"], "arxiv_id": "", "area": "mcsp-classic",
                    "url": f"https://doi.org/{c['doi']}", "title": c["title"], "year": c.get("year"),
                    "citations": c.get("citations", 0), "venue": "", "authors": c.get("authors", []),
                    "abstract": c.get("abstract", "")})
    return out


def _norm_id(x: str) -> str:
    x = (x or "").strip()
    return x if ":" in x.split("/")[0] else "doi:" + x        # legacy bare DOIs


def load_seen(path: str = SEEN_PATH) -> set:
    try:
        with open(path) as f:
            return {_norm_id(x) for x in json.load(f)}
    except Exception:  # noqa: BLE001
        return set()


def save_seen(path: str, ids: set) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(sorted(ids), f, indent=1)


# --------------------------------- pick -----------------------------------

PICK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "chosen_id": {"type": "string"},
        "none_worthwhile": {"type": "boolean"},
        "worth_30_min": {"type": "string"},
        "inspiration": {"type": "string"},
        "foundations": {"type": "string"},
        "reading_guide": {"type": "string"},
    },
    "required": ["chosen_id", "none_worthwhile", "worth_30_min", "inspiration", "foundations",
                 "reading_guide"],
}
PICK_PROMPT = (
    "You choose ONE paper for a researcher to read today, from a canon of established papers. "
    + judge.READER + "\n\n" + judge.PHILOSOPHY + "\n\n"
    "Below are REAL bibliographic records (from OpenAlex). Pick the SINGLE unseen paper most worth "
    "30 minutes for this reader next - prefer genuine breakthroughs and foundational theory over "
    "narrow applications or tooling. Return its exact id from the list in chosen_id (never invent "
    "one). If none of them is worth 30 minutes, set none_worthwhile=true and chosen_id=''.\n"
    "Then answer the reader's three questions about the chosen paper, grounded in its title and "
    "abstract and in what is reliably known about well-known papers (never assert numbers that are "
    "not in the abstract):\n"
    "  worth_30_min  (Q1) why it is important / breakthrough / high quality - what changed because of it\n"
    "  inspiration   (Q2) what it could inspire in molecular-CSP / genetic-algorithm work, or in AI4Sci broadly\n"
    "  foundations   (Q3) the foundational knowledge or theory to learn from it\n"
    "  reading_guide a 30-minute plan: which sections/figures first, what to skip\n"
    "Each field at most 70 words. Plain ASCII punctuation.\n\nCANDIDATES:\n"
)


def _listing(cands: list) -> str:
    return "\n".join(
        f"{i + 1}. id={c['id']} | {c.get('year', '')} | {c.get('citations', 0)} cites | "
        f"{c.get('venue') or ''}\n   {c.get('title', '')}\n   {(c.get('abstract') or '')[:280]}"
        for i, c in enumerate(cands))


def pick(cands: list, model: str, key: str, api=None) -> dict:
    cands = sorted(cands, key=lambda c: c.get("citations", 0), reverse=True)[:CANDIDATES_SHOWN]
    return judge.call_json(PICK_PROMPT + _listing(cands), PICK_SCHEMA, model, key,
                           effort=os.environ.get("LANDMARK_EFFORT", "high"), max_tokens=8000,
                           fallbacks=os.environ.get("JUDGE_FALLBACKS", "1") != "0", api=api)


def lane_for(today: datetime.date, setting: str = None) -> str:
    setting = (setting or os.environ.get("LANDMARK_LANE", "alternate")).lower()
    if setting in ("ai4sci", "mcsp"):
        return setting
    return "ai4sci" if today.timetuple().tm_yday % 2 == 0 else "mcsp"


def landmark_of_the_day(lane: str = None, seen_path: str = SEEN_PATH, pool_path: str = POOL_PATH,
                        model: str = None, api=None, today: datetime.date = None,
                        commit: bool = True, log=print) -> dict:
    """Pick today's landmark (dict) or None. Never raises past this function."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    today = today or datetime.date.today()
    model = model or os.environ.get("LANDMARK_MODEL", MODEL_DEFAULT)
    first = lane_for(today, lane)
    seen = load_seen(seen_path)
    for ln in (first, "mcsp" if first == "ai4sci" else "ai4sci"):
        cands = [c for c in load_pool(ln, pool_path) if c["id"] not in seen]
        if not cands:
            log(f"[landmark] {ln}: pool exhausted", file=sys.stderr)
            continue
        try:
            sel = pick(cands, model, key, api=api)
        except (judge.JudgeError, judge.Refused) as e:
            log(f"[landmark] {ln}: pick failed: {e}", file=sys.stderr)
            return None
        chosen = {c["id"]: c for c in cands}.get(sel.get("chosen_id", ""))
        if sel.get("none_worthwhile") or not chosen:
            log(f"[landmark] {ln}: nothing worth 30 minutes among {len(cands)} unseen")
            continue
        if commit:
            save_seen(seen_path, seen | {chosen["id"]})
        return {**chosen, "lane": ln, "picked_on": today.isoformat(),
                "worth_30_min": sel["worth_30_min"], "inspiration": sel["inspiration"],
                "foundations": sel["foundations"], "reading_guide": sel["reading_guide"]}
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("refresh", help="resolve the seed list through OpenAlex and write the pool")
    p = sub.add_parser("pick", help="preview today's pick (needs ANTHROPIC_API_KEY)")
    p.add_argument("--lane", choices=["ai4sci", "mcsp"])
    p.add_argument("--commit", action="store_true", help="record the pick in the seen ledger")
    a = ap.parse_args()
    if a.cmd == "refresh":
        if not os.environ.get("OPENALEX_API_KEY"):
            print("warning: OPENALEX_API_KEY not set - keyless OpenAlex budgets are tiny", file=sys.stderr)
        refresh_pool()
    elif a.cmd == "pick":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("Set ANTHROPIC_API_KEY first.")
        lm = landmark_of_the_day(lane=a.lane, commit=a.commit)
        print(json.dumps(lm, indent=2, ensure_ascii=False) if lm else "no landmark produced")
    else:
        ap.print_help()
