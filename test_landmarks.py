#!/usr/bin/env python3
"""Offline tests for landmarks.py (no network). Run: python3 test_landmarks.py"""
import datetime
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import landmarks  # noqa: E402

AF = {"title": "Highly accurate protein structure prediction with AlphaFold", "publication_year": 2021,
      "doi": "https://doi.org/10.1038/s41586-021-03819-2", "cited_by_count": 43588,
      "primary_location": {"source": {"display_name": "Nature"}},
      "authorships": [{"author": {"display_name": n}} for n in ("John Jumper", "Richard Evans", "A", "B")],
      "abstract_inverted_index": {"Proteins": [0], "fold.": [1]}}
FM = {"title": "Flow Matching for Generative Modeling", "publication_year": 2022,
      "doi": "https://doi.org/10.48550/arxiv.2210.02747", "cited_by_count": 192,
      "primary_location": {"source": {"display_name": "arXiv"}},
      "authorships": [{"author": {"display_name": "Yaron Lipman"}}], "abstract_inverted_index": None}


def fake_fetch(url):
    if "doi:10.1038%2Fs41586-021-03819-2" in url:
        return json.dumps(AF).encode()
    if "doi:10.48550%2Farxiv.2210.02747" in url:
        return json.dumps(FM).encode()
    if "doi:10.9999%2Fwrong" in url:
        return json.dumps({**AF, "title": "Something else entirely about cardiology"}).encode()
    if "search=" in url and "Geometric" in url:
        near = {**FM, "title": "Scalable Geometric Deep Learning on Molecular Graphs", "cited_by_count": 5}
        return json.dumps({"results": [near]}).encode()
    if "search=" in url:
        repost = {**FM, "doi": "https://doi.org/10.5555/repost", "cited_by_count": 0}
        return json.dumps({"results": [repost, FM]}).encode()
    raise RuntimeError("404")


class TestResolve(unittest.TestCase):
    def test_doi_and_arxiv_seed(self):
        r = landmarks.resolve_seed({"id": "doi:10.1038/s41586-021-03819-2", "area": "protein",
                                    "title": "Highly accurate protein structure prediction with AlphaFold"}, fetch=fake_fetch)
        self.assertEqual(r["doi"], "10.1038/s41586-021-03819-2")
        self.assertEqual(r["url"], "https://doi.org/10.1038/s41586-021-03819-2")
        self.assertEqual(r["authors"], ["John Jumper", "Richard Evans", "A"])
        self.assertEqual(r["authors_n"], 4)
        self.assertEqual(r["abstract"], "Proteins fold.")
        r = landmarks.resolve_seed({"id": "arxiv:2210.02747", "area": "generative-theory",
                                    "title": "Flow Matching for Generative Modeling"}, fetch=fake_fetch)
        self.assertEqual(r["arxiv_id"], "2210.02747")
        self.assertEqual(r["url"], "https://arxiv.org/abs/2210.02747")
        self.assertEqual(r["venue"], "arXiv")

    def test_wrong_doi_is_rejected_not_displayed(self):
        r = landmarks.resolve_seed({"id": "doi:10.9999/wrong", "area": "x",
                                    "title": "Highly accurate protein structure prediction with AlphaFold"}, fetch=fake_fetch)
        self.assertIn("error", r)

    def test_title_fallback_and_pool_file(self):
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, "pool.json")
        seeds = [{"id": "doi:10.5555/missing", "area": "generative-theory",
                  "title": "Flow Matching for Generative Modeling"},
                 {"id": "doi:10.5555/nomatch", "area": "x", "title": "A completely unrelated title here"}]
        data = landmarks.refresh_pool(fetch=fake_fetch, out=out, seeds=seeds, pause=0, log=lambda *a, **k: None)
        self.assertEqual(len(data["pool"]), 1)
        self.assertEqual(data["pool"][0]["title"], "Flow Matching for Generative Modeling")
        self.assertGreaterEqual(data["pool"][0]["match"], landmarks.MATCH_THRESHOLD)
        self.assertEqual(len(data["unresolved"]), 1)
        self.assertEqual(landmarks.load_pool("ai4sci", pool_path=out)[0]["id"], "doi:10.5555/missing")
        # near-identical titles: the most-cited (canonical) record wins over a repost
        self.assertEqual(data["pool"][0]["doi"], "10.48550/arxiv.2210.02747")

    def test_similar_title_is_not_enough(self):
        r = landmarks.resolve_seed({"id": "doi:10.5555/missing2", "area": "x",
                                    "title": "Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, and Gauges"}, fetch=fake_fetch)
        self.assertIn("error", r)       # 0.61 similarity to 'Scalable Geometric Deep Learning on Molecular Graphs' 


def _resp(payload):
    return {"stop_reason": "end_turn", "content": [{"type": "text", "text": json.dumps(payload)}]}


class TestPick(unittest.TestCase):
    def setUp(self):
        os.environ["ANTHROPIC_API_KEY"] = "k"
        # the MCSP lane reads classic.py's cache, which re-mines from OpenAlex when
        # stale - never from a test
        import classic
        self._pool_cached = classic._pool_cached
        classic._pool_cached = lambda: [{"doi": "10.2/c", "title": "Classic", "year": 2006, "citations": 2546,
                                         "authors": ["O"], "abstract": "c"}]
        self.tmp = tempfile.mkdtemp()
        self.pool = os.path.join(self.tmp, "pool.json")
        self.seen = os.path.join(self.tmp, "seen.json")
        recs = [{"id": "doi:10.1/af", "doi": "10.1/af", "arxiv_id": "", "url": "https://doi.org/10.1/af",
                 "title": "AlphaFold", "year": 2021, "citations": 40000, "venue": "Nature", "area": "protein",
                 "authors": ["J"], "authors_n": 1, "abstract": "a"},
                {"id": "arxiv:2210.02747", "doi": "", "arxiv_id": "2210.02747", "url": "https://arxiv.org/abs/2210.02747",
                 "title": "Flow Matching", "year": 2022, "citations": 192, "venue": "arXiv",
                 "area": "generative-theory", "authors": ["Y"], "authors_n": 1, "abstract": "b"}]
        json.dump({"mined": "2026-10-26", "pool": recs}, open(self.pool, "w"))

    def tearDown(self):
        import classic
        classic._pool_cached = self._pool_cached

    def test_lane_alternates(self):
        self.assertEqual(landmarks.lane_for(datetime.date(2026, 10, 26), "alternate"), "mcsp")    # day 299
        self.assertEqual(landmarks.lane_for(datetime.date(2026, 10, 27), "alternate"), "ai4sci")  # day 300
        self.assertEqual(landmarks.lane_for(datetime.date(2026, 10, 26), "ai4sci"), "ai4sci")

    def test_pick_marks_seen_and_skips_seen(self):
        calls = []

        def api(body, key, betas):
            calls.append(body)
            listing = body["messages"][0]["content"]
            chosen = "doi:10.1/af" if "doi:10.1/af" in listing else "arxiv:2210.02747"
            return _resp({"chosen_id": chosen, "none_worthwhile": False, "worth_30_min": "w",
                          "inspiration": "i", "foundations": "f", "reading_guide": "r"})
        lm = landmarks.landmark_of_the_day(lane="ai4sci", seen_path=self.seen, pool_path=self.pool, api=api,
                                           today=datetime.date(2026, 10, 27), log=lambda *a, **k: None)
        self.assertEqual(lm["id"], "doi:10.1/af")
        self.assertEqual(lm["lane"], "ai4sci")
        self.assertEqual(lm["picked_on"], "2026-10-27")
        self.assertEqual(lm["worth_30_min"], "w")
        self.assertEqual(json.load(open(self.seen)), ["doi:10.1/af"])
        self.assertEqual(calls[0]["output_config"]["effort"], "high")
        lm2 = landmarks.landmark_of_the_day(lane="ai4sci", seen_path=self.seen, pool_path=self.pool, api=api,
                                            today=datetime.date(2026, 10, 27), log=lambda *a, **k: None)
        self.assertEqual(lm2["id"], "arxiv:2210.02747")
        self.assertNotIn("doi:10.1/af", calls[1]["messages"][0]["content"])

    def test_none_worthwhile_falls_back_to_other_lane_then_none(self):
        def api(body, key, betas):
            return _resp({"chosen_id": "", "none_worthwhile": True, "worth_30_min": "", "inspiration": "",
                          "foundations": "", "reading_guide": ""})
        lm = landmarks.landmark_of_the_day(lane="ai4sci", seen_path=self.seen, pool_path=self.pool, api=api,
                                           today=datetime.date(2026, 10, 27), log=lambda *a, **k: None)
        self.assertIsNone(lm)
        self.assertFalse(os.path.exists(self.seen))

    def test_invented_id_is_ignored(self):
        def api(body, key, betas):
            return _resp({"chosen_id": "doi:10.0/invented", "none_worthwhile": False, "worth_30_min": "w",
                          "inspiration": "i", "foundations": "f", "reading_guide": "r"})
        lm = landmarks.landmark_of_the_day(lane="ai4sci", seen_path=self.seen, pool_path=self.pool, api=api,
                                           today=datetime.date(2026, 10, 27), log=lambda *a, **k: None)
        self.assertIsNone(lm)

    def test_legacy_bare_dois_in_ledger(self):
        json.dump(["10.1/af"], open(self.seen, "w"))
        self.assertEqual(landmarks.load_seen(self.seen), {"doi:10.1/af"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
