#!/usr/bin/env python3
"""
Reading gate for csp-digest: decides what is worth the reader's time.

The reader's own rule: reading 100 new but unimportant papers is no better than
reading ONE really important one. So the default verdict is "skip", the digest
is allowed to be empty, and every paper that survives carries the reader's
three questions answered on a 1-5 scale:

  Q1 worth_30_min  Is it novel, important, breakthrough-level, high quality
                   enough to be worth 30 minutes of reading?
  Q2 inspiring     Is it insightful or inspiring for the reader's own work
                   (molecular CSP with genetic algorithms) - or, more broadly,
                   for AI-for-science research?
  Q3 foundational  Does it contain foundational knowledge or theory worth
                   reading and learning?

Two stages, stdlib + the Anthropic Messages API (no SDK, so GitHub Actions
needs no pip install):

  triage(item)  cheap model drops obvious noise (experimental-only, off-topic,
                tooling/application notes). Fail-open: errors -> keep.
  judge(item)   frontier model answers Q1-Q3 with structured output. The
                verdict (read / skim / skip) is derived IN CODE from the scores,
                so thresholds are tunable without touching the prompt.

Every decision is cached in site/data/judged.json keyed by paper id, so a
paper is judged once even though the digest re-fetches a rolling window daily
(this also stops one-line summaries from flip-flopping day to day).

Failure policy: a broken judge must never silently publish unjudged papers as
"worth reading" (silent-degraded-but-green is this stack's recurring disease).
run() reports judge_ok=False when the judge could not do its job; digest.py
then refuses to publish if JUDGE_REQUIRED=1 (set in the daily workflow).

Env:
  ANTHROPIC_API_KEY  required for judging
  JUDGE_MODEL        default claude-opus-5-5     JUDGE_EFFORT   default medium ("" = omit)
  TRIAGE_MODEL       default claude-haiku-5-5    TRIAGE_EFFORT  default low  ("" = skip triage / omit)
  JUDGE_FALLBACKS    1 (default) = server-side refusal fallback on the judge
  DIGEST_JUDGE=0     disable judging on purpose (local runs without a key)
  JUDGE_READ_Q1 / JUDGE_READ_Q2 / JUDGE_READ_Q3   read thresholds (4 / 3 / 4)

Validate live (one call each stage):   ANTHROPIC_API_KEY=... python3 judge.py --selftest
Re-judge a dump, no cache, see scores:  ANTHROPIC_API_KEY=... python3 judge.py --file digests/csp_digest_2026-10-26.json
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://api.anthropic.com/v1/messages"
JUDGE_MODEL_DEFAULT = "claude-opus-5-5"
TRIAGE_MODEL_DEFAULT = "claude-haiku-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
PROMPT_VERSION = "2026-10-26.1"          # bump -> every paper is re-judged
CACHE_PATH = os.path.join("site", "data", "judged.json")
CACHE_MAX_AGE_DAYS = 180

# ------------------------------ the reader --------------------------------

READER = (
    "THE READER: a PhD researcher in molecular crystal structure prediction (MCSP) - polymorph "
    "search with genetic algorithms (GAtor, Genarris), dispersion-corrected DFT lattice-energy "
    "ranking, machine-learned potentials used only as accelerators. Beyond MCSP they want the "
    "LANDMARK papers of AI for science and the foundational theory behind them: the AlphaFold, "
    "flow-matching, diffusion-model, Boltzmann-generator, GNoME/MatterGen, AlphaGo-search tier - "
    "plus genuinely new state-of-the-art results in MCSP itself. They are explicitly NOT looking "
    "for: new ML-potential architectures or training tricks, uncertainty-quantification variants, "
    "benchmark re-runs, datasets/software/pipeline tooling, applications of an existing method to "
    "one system, surveys of narrow subfields, or experimental-only work - however on-topic the "
    "keywords look."
)
PHILOSOPHY = (
    "Their reading time is the scarce resource: reading 100 unimportant papers is worse than "
    "reading one important paper. The default is skip. A wrong skip costs little; a wrong read "
    "costs 30 minutes. Most papers - including most competent ones - must score low."
)

# ------------------------------- triage -----------------------------------

TRIAGE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"keep": {"type": "boolean"}, "reason": {"type": "string"}},
    "required": ["keep", "reason"],
}
TRIAGE_PROMPT = (
    "You pre-filter papers for a reading gate. " + READER + "\n\n"
    "DROP (keep=false) when the paper is clearly: experimental-only (synthesis, characterization, "
    "devices, XRD of made samples) with no computational or AI method; an unrelated field; an "
    "application of an existing method to one material/system; a dataset, software, pipeline or "
    "tooling paper; an incremental architecture/training/uncertainty tweak for ML potentials; or "
    "a narrow survey.\n"
    "KEEP (keep=true) when it could plausibly be a methodological advance in crystal structure "
    "prediction, a significant AI-for-science result, or foundational theory. When unsure, keep - "
    "a stricter judge reads everything you keep.\n"
    "reason: at most 12 words."
)

# -------------------------------- judge -----------------------------------

RUBRIC_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "q1_worth_30_min": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "q2_inspiring": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "q3_foundational": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "likely_low_quality": {"type": "boolean"},
        "lane": {"type": "string", "enum": ["mcsp", "ai4sci", "off_topic"]},
        "contribution": {"type": "string"},
        "why": {"type": "string"},
    },
    "required": ["q1_worth_30_min", "q2_inspiring", "q3_foundational", "likely_low_quality",
                 "lane", "contribution", "why"],
}
RUBRIC_PROMPT = (
    "You are the reading gatekeeper for one researcher. " + READER + "\n\n" + PHILOSOPHY + "\n\n"
    "Answer three questions about the paper below, each scored 1-5.\n"
    "Q1 q1_worth_30_min - Is this paper novel, important, breakthrough-level and high quality "
    "enough to be worth 30 minutes of this reader's attention?\n"
    "   5 landmark (AlphaFold / flow-matching tier; a few per year in all of AI4Sci)\n"
    "   4 clear state-of-the-art advance or a genuinely new idea with strong evidence\n"
    "   3 solid, competent, ordinary   2 incremental   1 weak, vague, or likely low quality\n"
    "Q2 q2_inspiring - Would it give this reader a new idea for their own MCSP / genetic-algorithm "
    "work, or more broadly for AI-for-science research? 5 directly suggests a new direction; "
    "3 loosely transferable; 1 nothing to take.\n"
    "Q3 q3_foundational - Does it contain foundational knowledge or theory worth learning (a "
    "framework, derivation, or principle the field builds on)? 5 canonical theory or method; "
    "3 a useful technique; 1 none.\n\n"
    "Calibration: the large majority of papers score 1-2 on Q1. New SOTA in MCSP itself (blind-test "
    "level results, a new search or ranking method with real validation) deserves Q1 4-5 even if it "
    "is small news for AI4Sci at large. Judge the abstract critically: grand claims without concrete "
    "evidence, no baselines or numbers, 'novel framework/paradigm' language, buzzword density, or "
    "signs of machine-generated boilerplate -> Q1 1-2 and likely_low_quality=true. Prominent venue "
    "or group raises the prior for quality but does not by itself make a paper worth reading.\n"
    "lane: 'mcsp' if the work is centrally about molecular/organic crystal structure prediction or "
    "polymorph energy ranking; 'ai4sci' for AI-for-science / ML methodology; 'off_topic' otherwise.\n"
    "contribution: at most 28 words, concrete - what is new versus prior work; no hype, no 'this "
    "paper'. why: at most 25 words - the decisive reason behind your scores. Plain ASCII."
)

SYNTHESIS_PROMPT = (
    "You brief the reader described here. " + READER + "\n\n"
    "Below are today's papers that passed a strict reading gate (verdict and the three scores "
    "Q1 worth-30-min / Q2 inspiring / Q3 foundational), plus the landmark pick of the day. Write 1-2 "
    "sentences (max 50 words) on what is worth their time today and why. If nothing passed as "
    "'read', say so plainly - a quiet day is a good day. No hype, no 'today's papers'. Plain ASCII."
)


class JudgeError(Exception):
    """The API could not deliver a judgment (network, auth, server, quota)."""


class Refused(Exception):
    """The model declined to assess (stop_reason refusal)."""


# ------------------------------ API layer ---------------------------------

def _post(body: dict, key: str, betas=None, timeout: int = 240, tries: int = 3) -> dict:
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    if betas:
        headers["anthropic-beta"] = ",".join(betas)
    last = "no attempt"
    for t in range(tries):
        try:
            req = urllib.request.Request(API, data=json.dumps(body).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
            if resp.get("stop_reason") == "refusal":
                det = resp.get("stop_details") or {}
                raise Refused(str(det.get("category") or "refusal"))
            return resp
        except Refused:
            raise
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:  # noqa: BLE001
                pass
            last = f"HTTP {e.code} {detail}"
            if e.code in (400, 401, 403, 404, 413):
                raise JudgeError(last)                  # not retryable
            time.sleep(20.0 * (t + 1) if e.code == 429 else 4.0 * (t + 1))
        except Exception as e:  # noqa: BLE001 - transient network
            last = f"{type(e).__name__}: {e}"
            time.sleep(4.0 * (t + 1))
    raise JudgeError(last)


def _json_of(resp: dict) -> dict:
    text = "".join(b.get("text", "") for b in resp.get("content", [])
                   if b.get("type") == "text").strip()
    return json.loads(text)


def call_json(prompt: str, schema: dict, model: str, key: str, effort: str = "medium",
              max_tokens: int = 4000, fallbacks: bool = False, api=None) -> dict:
    """One structured-output call. `api` is injectable for offline tests:
    api(body, key, betas) -> response dict."""
    api = api or _post
    body = {"model": model, "max_tokens": max_tokens,
            "output_config": {"format": {"type": "json_schema", "schema": schema}},
            "messages": [{"role": "user", "content": prompt}]}
    if effort:                                          # "" omits the field (escape hatch)
        body["output_config"]["effort"] = effort
    betas = []
    if fallbacks:
        body["fallbacks"] = "default"                   # Anthropic-picked model on a policy decline
        betas.append(FALLBACK_BETA)
    resp = api(body, key, betas)
    if resp.get("stop_reason") == "max_tokens":         # thinking used the budget: once more, bigger
        body["max_tokens"] = max_tokens * 2
        resp = api(body, key, betas)
    try:
        return _json_of(resp)
    except (ValueError, TypeError) as e:
        raise JudgeError(f"unparseable model output: {e}")


# ----------------------------- per-paper logic ----------------------------

def item_id(it: dict) -> str:
    aid = it.get("arxiv_id") or ""
    return it.get("doi") or re.sub(r"v\d+$", "", aid) or (it.get("title") or "")


def paper_text(it: dict) -> str:
    authors = it.get("authors_all") or it.get("authors") or []
    who = ", ".join(authors[:5]) + (" et al." if len(authors) > 5 else "")
    return (f"Title: {it.get('title', '')}\nVenue: {it.get('venue', '') or it.get('src', '')}\n"
            f"Date: {it.get('date', '')}\nAuthors: {who or '(unknown)'}\n"
            f"Abstract: {(it.get('abstract') or '(none - judge from the title, cautiously)')[:1500]}")


def thresholds() -> tuple:
    return (int(os.environ.get("JUDGE_READ_Q1", "4")),
            int(os.environ.get("JUDGE_READ_Q2", "3")),
            int(os.environ.get("JUDGE_READ_Q3", "4")))


def verdict_from(r: dict, th: tuple = None) -> str:
    """read / skim / skip from the three scores. Deterministic so a threshold
    change never requires re-judging."""
    r1, r2, r3 = th or thresholds()
    if r.get("likely_low_quality") or r.get("lane") == "off_topic":
        return "skip"
    q1, q2, q3 = int(r.get("q1", 1)), int(r.get("q2", 1)), int(r.get("q3", 1))
    if q1 >= r1 and (q2 >= r2 or q3 >= r3):
        return "read"
    if q1 >= 3 and (q2 >= 3 or q3 >= 3):
        return "skim"
    return "skip"


def composite(r: dict) -> int:
    """0-100 sort key: Q1 dominates (importance), then inspiration, then theory."""
    return int(round((0.5 * r.get("q1", 0) + 0.3 * r.get("q2", 0) + 0.2 * r.get("q3", 0)) * 20))


def apply(it: dict, c: dict) -> None:
    """Write a cached/fresh decision onto the item (what the site renders)."""
    it["verdict"] = c.get("verdict", "skip")
    it["lane"] = c.get("lane") if c.get("lane") in ("mcsp", "ai4sci") else (
        "ai4sci" if it.get("ai4sci") else "mcsp")
    it["rubric"] = {k: c.get(k) for k in ("q1", "q2", "q3", "low_quality", "why", "stage")}
    it["rubric"]["verdict"] = it["verdict"]
    if c.get("stage") == "judge":
        it["score"] = composite(c)
        it["relevance"] = int(c.get("q2", 0)) * 20          # inspiring-for-you
        it["significance"] = int(c.get("q1", 0)) * 20       # worth-30-min
        if c.get("contribution"):
            it["summary"] = c["contribution"]


def triage_one(it: dict, model: str, key: str, api=None) -> dict:
    return call_json(TRIAGE_PROMPT + "\n\n" + paper_text(it), TRIAGE_SCHEMA, model, key,
                     effort=os.environ.get("TRIAGE_EFFORT", "low"), max_tokens=2000, api=api)


def judge_one(it: dict, model: str, key: str, effort: str, fallbacks: bool, api=None) -> dict:
    r = call_json(RUBRIC_PROMPT + "\n\nPAPER\n" + paper_text(it), RUBRIC_SCHEMA, model, key,
                  effort=effort, max_tokens=4000, fallbacks=fallbacks, api=api)
    return {"q1": int(r["q1_worth_30_min"]), "q2": int(r["q2_inspiring"]),
            "q3": int(r["q3_foundational"]), "low_quality": bool(r["likely_low_quality"]),
            "lane": r["lane"], "contribution": str(r["contribution"])[:300],
            "why": str(r["why"])[:220]}


# -------------------------------- cache -----------------------------------

def load_cache(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def save_cache(path: str, cache: dict, today: str) -> None:
    cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=CACHE_MAX_AGE_DAYS)).isoformat()
    cache = {k: v for k, v in cache.items() if (v.get("date") or today) >= cutoff}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(cache, f, indent=0, sort_keys=True)


VERDICT_RANK = {"read": 0, "skim": 1, "skip": 2}


def sort_kept(items: list) -> list:
    return sorted(items, key=lambda x: (VERDICT_RANK.get(x.get("verdict"), 3),
                                        -x.get("score", 0), x.get("date") or ""),
                  reverse=False)


# --------------------------------- run ------------------------------------

def run(items: list, cache_path: str = CACHE_PATH, api=None, today: str = None,
        log=print) -> tuple:
    """Triage + judge every item (cached). Returns (kept_items, judge_ok).
    kept = verdict read or skim, sorted read-first then by score.
    judge_ok=False means the judge could not do its job (no key, or most calls
    failed) - the caller decides whether that blocks publishing."""
    today = today or datetime.date.today().isoformat()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if os.environ.get("DIGEST_JUDGE", "1") == "0":
        log("[judge] disabled (DIGEST_JUDGE=0) - publishing unjudged items")
        return items, True
    if not key:
        log("[judge] no ANTHROPIC_API_KEY - nothing judged", file=sys.stderr)
        return items, False
    if not items:
        return [], True
    jmodel = os.environ.get("JUDGE_MODEL", JUDGE_MODEL_DEFAULT)
    tmodel = os.environ.get("TRIAGE_MODEL", TRIAGE_MODEL_DEFAULT)
    effort = os.environ.get("JUDGE_EFFORT", "medium")
    fallbacks = os.environ.get("JUDGE_FALLBACKS", "1") != "0"
    cache = load_cache(cache_path)
    kept, attempted, failed, fresh, triaged_out = [], 0, 0, 0, 0
    for it in items:
        pid = item_id(it)
        c = cache.get(pid)
        if not (c and c.get("v") == PROMPT_VERSION):
            c = None
            if tmodel:
                try:
                    t = triage_one(it, tmodel, key, api=api)
                except (JudgeError, Refused) as e:     # fail-open: the judge decides
                    t = {"keep": True, "reason": f"triage unavailable ({str(e)[:40]})"}
                if not t.get("keep", True):
                    c = {"v": PROMPT_VERSION, "model": tmodel, "date": today, "stage": "triage",
                         "verdict": "skip", "why": str(t.get("reason", ""))[:120],
                         "lane": "ai4sci" if it.get("ai4sci") else "mcsp"}
                    triaged_out += 1
            if c is None:
                attempted += 1
                try:
                    r = judge_one(it, jmodel, key, effort, fallbacks, api=api)
                except Refused as e:
                    # Not cached: a classifier false positive gets another chance tomorrow.
                    apply(it, {"stage": "judge", "verdict": "skip",
                               "why": f"model declined to assess ({e})"})
                    log(f"[judge] declined: {(it.get('title') or '')[:60]} ({e})", file=sys.stderr)
                    continue
                except JudgeError as e:
                    failed += 1          # not published, not cached -> retried next run
                    log(f"[judge] FAILED (held back): {(it.get('title') or '')[:60]}: {e}",
                        file=sys.stderr)
                    continue
                c = {"v": PROMPT_VERSION, "model": jmodel, "date": today, "stage": "judge", **r}
                c["verdict"] = verdict_from(c)
                fresh += 1
                time.sleep(0.2)
            cache[pid] = c
        apply(it, c)
        if it["verdict"] in ("read", "skim"):
            kept.append(it)
    save_cache(cache_path, cache, today)
    judge_ok = not (attempted and failed > attempted / 2)
    n_read = sum(1 for i in kept if i["verdict"] == "read")
    log(f"[judge] {len(items)} candidates -> {n_read} read, {len(kept) - n_read} skim "
        f"(triage dropped {triaged_out}, judged fresh {fresh}, cached {len(items) - fresh - triaged_out - failed}, "
        f"failed {failed}; models {tmodel or '-'} -> {jmodel}/{effort})")
    if not judge_ok:
        log(f"[judge] {failed}/{attempted} judge calls failed - judge unreliable", file=sys.stderr)
    return sort_kept(kept), judge_ok


def daily_synthesis(items: list, landmark: dict = None, api=None) -> str:
    """1-2 sentences on what is worth reading today. '' without a key/items."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or (not items and not landmark):
        return ""
    model = os.environ.get("JUDGE_MODEL", JUDGE_MODEL_DEFAULT)
    lines = []
    for i in items[:15]:
        r = i.get("rubric") or {}
        lines.append(f"- [{i.get('verdict', '?')} Q1={r.get('q1')} Q2={r.get('q2')} Q3={r.get('q3')}] "
                     f"{i.get('title', '')} ({i.get('venue', '')})")
    if landmark:
        lines.append(f"- [landmark of the day, {landmark.get('lane')}] {landmark.get('title', '')} "
                     f"({landmark.get('year', '')})")
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"synthesis": {"type": "string"}}, "required": ["synthesis"]}
    try:
        out = call_json(SYNTHESIS_PROMPT + "\n\n" + "\n".join(lines), schema, model, key,
                        effort="low", max_tokens=2000,
                        fallbacks=os.environ.get("JUDGE_FALLBACKS", "1") != "0", api=api)
        return str(out.get("synthesis", "")).strip()[:400]
    except (JudgeError, Refused) as e:
        print(f"[judge] synthesis skipped: {e}", file=sys.stderr)
        return ""


# ------------------------------ CLI helpers -------------------------------

_SELFTEST_ITEMS = [
    {"title": "Phonon dispersion of a single perovskite oxide from a fine-tuned machine-learned potential",
     "venue": "arXiv", "date": "2026-10-20", "authors": ["A. Author", "B. Author"],
     "abstract": ("We fine-tune an existing equivariant interatomic potential on 2,000 DFT "
                  "configurations of SrTiO3 and compute its phonon dispersion and thermal "
                  "conductivity, finding agreement with experiment within 8%.")},
    {"title": "Highly accurate protein structure prediction with AlphaFold",
     "venue": "Nature", "date": "2021-07-15", "authors": ["John Jumper", "Richard Evans"],
     "abstract": ("(Paraphrase for a self-test, not the published abstract.) A neural network "
                  "that predicts protein 3D structure from sequence with atomic accuracy, "
                  "validated blind in CASP14, incorporating physical and evolutionary knowledge "
                  "into an end-to-end attention-based architecture.")},
]


def _selftest() -> int:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("Set ANTHROPIC_API_KEY first.")
        return 2
    tmodel = os.environ.get("TRIAGE_MODEL", TRIAGE_MODEL_DEFAULT)
    jmodel = os.environ.get("JUDGE_MODEL", JUDGE_MODEL_DEFAULT)
    ok = True
    for it in _SELFTEST_ITEMS:
        print(f"\n== {it['title'][:70]}")
        if tmodel:
            try:
                print("  triage:", json.dumps(triage_one(it, tmodel, key)))
            except (JudgeError, Refused) as e:
                ok = False
                print("  triage FAILED:", e)
        try:
            r = judge_one(it, jmodel, key, os.environ.get("JUDGE_EFFORT", "medium"),
                          os.environ.get("JUDGE_FALLBACKS", "1") != "0")
            r["verdict"] = verdict_from(r)
            print("  judge: ", json.dumps(r))
        except (JudgeError, Refused) as e:
            ok = False
            print("  judge FAILED:", e)
    print("\nselftest", "OK" if ok else "FAILED")
    return 0 if ok else 1


def _rejudge_file(path: str) -> int:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("Set ANTHROPIC_API_KEY first.")
        return 2
    with open(path) as f:
        data = json.load(f)
    items = data.get("items", data) if isinstance(data, dict) else data
    jmodel = os.environ.get("JUDGE_MODEL", JUDGE_MODEL_DEFAULT)
    for it in items:
        try:
            r = judge_one(it, jmodel, key, os.environ.get("JUDGE_EFFORT", "medium"),
                          os.environ.get("JUDGE_FALLBACKS", "1") != "0")
            v = verdict_from(r)
            print(f"{v:4s} Q1={r['q1']} Q2={r['q2']} Q3={r['q3']} lowq={int(r['low_quality'])} "
                  f"{r['lane']:7s} | {(it.get('title') or '')[:70]}\n      {r['why']}")
        except (JudgeError, Refused) as e:
            print(f"FAIL {(it.get('title') or '')[:70]}: {e}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="one live call per stage")
    ap.add_argument("--file", help="re-judge every item in a digest JSON dump (no cache)")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(_selftest())
    if a.file:
        sys.exit(_rejudge_file(a.file))
    ap.print_help()
