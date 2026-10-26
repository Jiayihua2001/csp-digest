#!/usr/bin/env python3
"""Offline tests for judge.py (no network). Run: python3 test_judge.py"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge  # noqa: E402


def _resp(payload, stop="end_turn"):
    return {"stop_reason": stop,
            "content": [{"type": "thinking", "thinking": ""},
                        {"type": "text", "text": json.dumps(payload)}]}


def fake_api(script):
    """script(body) -> response dict | Exception to raise. Records calls."""
    calls = []

    def api(body, key, betas):
        calls.append({"body": body, "betas": betas})
        out = script(body)
        if isinstance(out, Exception):
            raise out
        return out
    api.calls = calls
    return api


def _route(body, triage=None, rubric=None, synth=None):
    prompt = body["messages"][0]["content"]
    if prompt.startswith("You pre-filter"):
        return triage
    if prompt.startswith("You brief"):
        return synth
    return rubric


ITEMS = [
    {"title": "Landmark-like paper", "doi": "10.1/a", "venue": "Nature", "date": "2026-10-20",
     "abstract": "x", "ai4sci": True},
    {"title": "Incremental MLIP tweak", "doi": "10.1/b", "venue": "arXiv", "date": "2026-10-21",
     "abstract": "y", "ai4sci": True},
    {"title": "MCSP method", "arxiv_id": "2610.00001v2", "venue": "arXiv", "date": "2026-10-22",
     "abstract": "z"},
]


class TestVerdict(unittest.TestCase):
    def test_thresholds(self):
        th = (4, 3, 4)
        self.assertEqual(judge.verdict_from({"q1": 5, "q2": 4, "q3": 2}, th), "read")
        self.assertEqual(judge.verdict_from({"q1": 4, "q2": 2, "q3": 4}, th), "read")
        self.assertEqual(judge.verdict_from({"q1": 4, "q2": 2, "q3": 3}, th), "skim")
        self.assertEqual(judge.verdict_from({"q1": 3, "q2": 3, "q3": 1}, th), "skim")
        self.assertEqual(judge.verdict_from({"q1": 3, "q2": 2, "q3": 2}, th), "skip")
        self.assertEqual(judge.verdict_from({"q1": 2, "q2": 5, "q3": 5}, th), "skip")
        self.assertEqual(judge.verdict_from({"q1": 5, "q2": 5, "q3": 5, "likely_low_quality": True}, th), "skip")
        self.assertEqual(judge.verdict_from({"q1": 5, "q2": 5, "q3": 5, "lane": "off_topic"}, th), "skip")

    def test_composite_and_ids(self):
        self.assertEqual(judge.composite({"q1": 5, "q2": 5, "q3": 5}), 100)
        self.assertEqual(judge.composite({"q1": 1, "q2": 1, "q3": 1}), 20)
        self.assertEqual(judge.item_id({"arxiv_id": "2610.00001v2"}), "2610.00001")
        self.assertEqual(judge.item_id({"doi": "10.1/a", "arxiv_id": "x"}), "10.1/a")


class TestRun(unittest.TestCase):
    def setUp(self):
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        os.environ.pop("DIGEST_JUDGE", None)
        os.environ.pop("TRIAGE_MODEL", None)
        self.tmp = tempfile.mkdtemp()
        self.cache = os.path.join(self.tmp, "judged.json")

    def _script(self, body):
        prompt = body["messages"][0]["content"]
        if "Incremental MLIP tweak" in prompt:
            return _route(body, triage=_resp({"keep": False, "reason": "incremental"}))
        if "Landmark-like" in prompt:
            return _route(body, triage=_resp({"keep": True, "reason": "ok"}),
                          rubric=_resp({"q1_worth_30_min": 5, "q2_inspiring": 4, "q3_foundational": 5,
                                        "likely_low_quality": False, "lane": "ai4sci",
                                        "contribution": "Big thing.", "why": "landmark"}))
        return _route(body, triage=_resp({"keep": True, "reason": "ok"}),
                      rubric=_resp({"q1_worth_30_min": 3, "q2_inspiring": 4, "q3_foundational": 2,
                                    "likely_low_quality": False, "lane": "mcsp",
                                    "contribution": "Small thing.", "why": "ordinary"}))

    def test_pipeline_cache_and_structure(self):
        api = fake_api(self._script)
        items = [dict(i) for i in ITEMS]
        kept, ok = judge.run(items, cache_path=self.cache, api=api, today="2026-10-26", log=lambda *a, **k: None)
        self.assertTrue(ok)
        self.assertEqual([k["verdict"] for k in kept], ["read", "skim"])      # read first
        self.assertEqual(kept[0]["summary"], "Big thing.")
        self.assertEqual(kept[0]["score"], 94)   # (0.5*5 + 0.3*4 + 0.2*5) * 20
        self.assertEqual(kept[0]["significance"], 100)
        self.assertEqual(kept[0]["rubric"]["q3"], 5)
        self.assertEqual(kept[1]["lane"], "mcsp")
        # triage: 3 calls, judge: 2 calls; the judge call carries the fallback beta
        self.assertEqual(len(api.calls), 5)
        jcall = [c for c in api.calls if "fallbacks" in c["body"]][0]
        self.assertEqual(jcall["body"]["fallbacks"], "default")
        self.assertIn(judge.FALLBACK_BETA, jcall["betas"])
        self.assertEqual(jcall["body"]["output_config"]["format"]["type"], "json_schema")
        self.assertNotIn("thinking", jcall["body"])
        tcall = [c for c in api.calls if "fallbacks" not in c["body"]][0]
        self.assertEqual(tcall["body"]["output_config"]["effort"], "low")
        # cache: everything decided is stored; a second run makes no API calls
        cache = json.load(open(self.cache))
        self.assertEqual(set(cache), {"10.1/a", "10.1/b", "2610.00001"})
        self.assertEqual(cache["10.1/b"]["stage"], "triage")
        api2 = fake_api(lambda b: Exception("should not be called"))
        kept2, ok2 = judge.run([dict(i) for i in ITEMS], cache_path=self.cache, api=api2,
                               today="2026-10-27", log=lambda *a, **k: None)
        self.assertTrue(ok2)
        self.assertEqual(len(api2.calls), 0)
        self.assertEqual([k["verdict"] for k in kept2], ["read", "skim"])

    def test_prompt_version_bump_rejudges(self):
        api = fake_api(self._script)
        judge.run([dict(ITEMS[0])], cache_path=self.cache, api=api, today="2026-10-26", log=lambda *a, **k: None)
        cache = json.load(open(self.cache))
        cache["10.1/a"]["v"] = "old"
        json.dump(cache, open(self.cache, "w"))
        api2 = fake_api(self._script)
        judge.run([dict(ITEMS[0])], cache_path=self.cache, api=api2, today="2026-10-26", log=lambda *a, **k: None)
        self.assertEqual(len(api2.calls), 2)

    def test_judge_failures_are_loud_and_held_back(self):
        os.environ["TRIAGE_MODEL"] = ""        # no triage stage
        api = fake_api(lambda b: judge.JudgeError("HTTP 500"))
        kept, ok = judge.run([dict(i) for i in ITEMS], cache_path=self.cache, api=api,
                             today="2026-10-26", log=lambda *a, **k: None)
        self.assertFalse(ok)
        self.assertEqual(kept, [])                           # nothing published unjudged
        self.assertEqual(json.load(open(self.cache)), {})    # nothing cached -> retried next run

    def test_refusal_is_skip_not_failure_and_not_cached(self):
        os.environ["TRIAGE_MODEL"] = ""
        api = fake_api(lambda b: judge.Refused("bio"))
        kept, ok = judge.run([dict(ITEMS[0])], cache_path=self.cache, api=api,
                             today="2026-10-26", log=lambda *a, **k: None)
        self.assertTrue(ok)
        self.assertEqual(kept, [])
        self.assertEqual(json.load(open(self.cache)), {})

    def test_triage_failure_is_fail_open(self):
        def script(body):
            if body["messages"][0]["content"].startswith("You pre-filter"):
                return judge.JudgeError("HTTP 500")
            return _resp({"q1_worth_30_min": 4, "q2_inspiring": 4, "q3_foundational": 2,
                          "likely_low_quality": False, "lane": "ai4sci",
                          "contribution": "c", "why": "w"})
        api = fake_api(script)
        kept, ok = judge.run([dict(ITEMS[0])], cache_path=self.cache, api=api,
                             today="2026-10-26", log=lambda *a, **k: None)
        self.assertTrue(ok)
        self.assertEqual(kept[0]["verdict"], "read")

    def test_max_tokens_retry_doubles_budget(self):
        seq = [_resp({}, stop="max_tokens"),
               _resp({"q1_worth_30_min": 2, "q2_inspiring": 2, "q3_foundational": 2,
                      "likely_low_quality": False, "lane": "ai4sci", "contribution": "c", "why": "w"})]
        api = fake_api(lambda b: seq.pop(0))
        r = judge.judge_one(ITEMS[0], "m", "k", "medium", False, api=api)
        self.assertEqual(r["q1"], 2)
        self.assertEqual(api.calls[1]["body"]["max_tokens"], 8000)

    def test_no_key_and_disabled(self):
        del os.environ["ANTHROPIC_API_KEY"]
        kept, ok = judge.run([dict(ITEMS[0])], cache_path=self.cache, log=lambda *a, **k: None)
        self.assertFalse(ok)                      # CI refuses to publish when JUDGE_REQUIRED=1
        self.assertEqual(len(kept), 1)
        os.environ["DIGEST_JUDGE"] = "0"
        kept, ok = judge.run([dict(ITEMS[0])], cache_path=self.cache, log=lambda *a, **k: None)
        self.assertTrue(ok)

    def test_synthesis_uses_structured_output(self):
        api = fake_api(lambda b: _resp({"synthesis": "Quiet day; read the landmark."}))
        s = judge.daily_synthesis([{"title": "t", "verdict": "read", "rubric": {"q1": 4, "q2": 3, "q3": 2}}],
                                  {"title": "AlphaFold", "lane": "ai4sci", "year": 2021}, api=api)
        self.assertEqual(s, "Quiet day; read the landmark.")
        self.assertIn("AlphaFold", api.calls[0]["body"]["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
