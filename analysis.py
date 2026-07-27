#!/usr/bin/env python3
"""
Deep per-paper analysis for csp-digest (Tier 1).

Reads a paper's full open-access PDF with a frontier model and returns a
structured, verified brief aimed at fast, accurate triage: what is the
contribution, does it matter to *you*, and should you read it. Falls back to
abstract-only (flagged, low confidence) when no PDF is fetchable, and never
raises — a failure returns None so the daily digest keeps running.

Used two ways:
  * imported by digest.py  -> deep_analyze(item) when DEEP_ANALYSIS=1
  * run standalone to validate output on one paper (needs your key in env):
        ANTHROPIC_API_KEY=sk-ant-... python3 analysis.py 2401.01234
        ANTHROPIC_API_KEY=sk-ant-... python3 analysis.py https://arxiv.org/pdf/2401.01234.pdf

Env knobs: ANALYSIS_MODEL (default claude-opus-4-8), DEEP_VERIFY=1 to run the
verification pass, OPENALEX_MAILTO for OA-link resolution.
Stdlib only — no pip install, so the GitHub Actions workflow needs no changes.
"""
from __future__ import annotations
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-opus-4-8"

# Edit this to sharpen the "relevance to you" judgement.
PROFILE = (
    "I work on molecular crystal structure prediction (CSP) using genetic-algorithm and "
    "evolutionary methods. I care about: new genetic operators (crossover/mutation), structure "
    "descriptors, energy-landscape ranking, machine-learned interatomic potentials for molecular "
    "crystals, Z'>1 and multi-component/co-crystals, and CSP benchmarks/blind tests. Groups I "
    "follow: Marom, Day, Neumann, Price, Beran, Oganov, Pickard, Woodley, Zhu."
)

BRIEF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "one_line_novelty": {"type": "string"},
        "contribution": {"type": "string"},
        "method": {"type": "string"},
        "key_results": {"type": "array", "items": {"type": "string"}},
        "datasets_or_benchmarks": {"type": "array", "items": {"type": "string"}},
        "code_or_data_available": {"type": "string"},
        "limitations": {"type": "array", "items": {"type": "string"}},
        "relevance_to_you": {"type": "string"},
        "relevance_score": {"type": "integer"},
        "verdict": {"type": "string", "enum": ["must-read", "skim", "skip"]},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": [
        "one_line_novelty", "contribution", "method", "key_results",
        "datasets_or_benchmarks", "code_or_data_available", "limitations",
        "relevance_to_you", "relevance_score", "verdict", "confidence",
    ],
}

_FAITHFUL = (
    "\n\nAccuracy matters more than completeness: state ONLY what the paper supports, never infer a "
    "result it does not report, and when something is ambiguous say so rather than guessing. The "
    "reader uses 'verdict' + 'relevance_score' to decide what to read first, so be well-calibrated, "
    "not generous. Set 'confidence' to how faithful the brief is to the source (use 'low' when you "
    "worked from the abstract only or had to infer)."
)


def _http_json(body: dict, key: str, timeout: int = 300) -> dict:
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _text(resp: dict) -> str:
    return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()


def _get(url: str, tries: int = 3) -> bytes:
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "csp-digest-analysis/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.0 * (t + 1))
    raise RuntimeError(f"GET failed: {last}")


def _oa_pdf_from_doi(doi: str) -> str | None:
    """Resolve a DOI to an open-access PDF URL via OpenAlex (best_oa_location)."""
    q = {"select": "best_oa_location,open_access"}
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        q["mailto"] = mailto
    url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="") + "?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(_get(url))
    except Exception:  # noqa: BLE001
        return None
    loc = data.get("best_oa_location") or {}
    return loc.get("pdf_url")


def pdf_url_for(item: dict) -> str | None:
    if item.get("pdf_url"):
        return item["pdf_url"]
    if item.get("arxiv_id"):
        return f"https://arxiv.org/pdf/{item['arxiv_id']}.pdf"
    if item.get("doi"):
        return _oa_pdf_from_doi(item["doi"])
    return None


def _pdf_block(data: bytes) -> dict:
    b64 = base64.standard_b64encode(data).decode("ascii")   # no newlines
    return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}


def _analyze(content: list, model: str, key: str) -> dict:
    body = {
        "model": model,
        "max_tokens": 4000,
        "output_config": {"format": {"type": "json_schema", "schema": BRIEF_SCHEMA}},
        "messages": [{"role": "user", "content": content}],
    }
    return json.loads(_text(_http_json(body, key)))


def _verify(data: bytes, brief: dict, model: str, key: str) -> str:
    prompt = (
        "Below is an AI-generated brief about the attached paper. Re-read the paper and check every "
        "claim. List each statement that is unsupported, overstated, or fabricated (quote it + why). "
        "If every claim is faithful, reply exactly: ALL SUPPORTED.\n\nBRIEF:\n" + json.dumps(brief, indent=2)
    )
    body = {"model": model, "max_tokens": 1500,
            "messages": [{"role": "user", "content": [_pdf_block(data), {"type": "text", "text": prompt}]}]}
    return _text(_http_json(body, key))


def deep_analyze(item: dict, model: str | None = None, verify: bool | None = None) -> dict | None:
    """Return a structured brief for one digest item, or None on failure."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    model = model or os.environ.get("ANALYSIS_MODEL", DEFAULT_MODEL)
    if verify is None:
        verify = os.environ.get("DEEP_VERIFY") == "1"
    try:
        base = (
            "You are a research analyst briefing a molecular-CSP specialist. Read the paper "
            "IN FULL (including results tables and figures) and produce the structured brief. Be "
            "concrete and quantitative (cite the actual numbers, benchmarks, model/dataset names). "
            "Judge 'relevance_to_you'/'relevance_score' against this profile:\n" + PROFILE + _FAITHFUL
        )
        pdf_data = None
        url = pdf_url_for(item)
        if url:
            try:
                pdf_data = _get(url)
                if len(pdf_data) > 30 * 1024 * 1024:   # over the 32 MB API limit
                    pdf_data = None
            except Exception:  # noqa: BLE001
                pdf_data = None

        if pdf_data:
            brief = _analyze([_pdf_block(pdf_data), {"type": "text", "text": base}], model, key)
            brief["source"] = "full-text"
            if verify:
                brief["verification"] = _verify(pdf_data, brief, model, key)
        else:
            abstract = item.get("abstract") or ""
            if not abstract:
                return None                            # nothing to work from
            prompt = (base + "\n\nNo full text was available; work ONLY from the title and abstract "
                      "below and set confidence to 'low'.\n\nTitle: " + (item.get("title") or "")
                      + "\nVenue: " + (item.get("venue") or "") + "\nAbstract: " + abstract)
            brief = _analyze([{"type": "text", "text": prompt}], model, key)
            brief["source"] = "abstract"
        return brief
    except Exception as e:  # noqa: BLE001 - analysis must never break the digest
        print(f"[warn] deep_analyze('{(item.get('title') or '')[:50]}'): {e}", file=sys.stderr)
        return None


def _main() -> None:
    if os.environ.get("ANTHROPIC_API_KEY") is None:
        sys.exit("Set ANTHROPIC_API_KEY first.")
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 analysis.py <arxiv_id | pdf_url | doi>")
    arg = sys.argv[1]
    if arg.startswith("http"):
        item = {"pdf_url": arg, "title": arg}
    elif "/" in arg or arg.lower().startswith("10."):
        item = {"doi": arg.replace("https://doi.org/", "")}
    else:
        item = {"arxiv_id": arg}
    brief = deep_analyze(item, verify=True)
    print(json.dumps(brief, indent=2, ensure_ascii=False) if brief else "no brief produced")


if __name__ == "__main__":
    _main()
