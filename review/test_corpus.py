#!/usr/bin/env python3
"""Unit tests for review/corpus.py (M1). No network: fetchers are injected.

Run: python3 review/test_corpus.py
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus  # noqa: E402


class TestPureHelpers(unittest.TestCase):
    def test_normalize_doi(self):
        for raw, want in [
            ("https://doi.org/10.1021/ACS.JCTC.7B01152", "10.1021/acs.jctc.7b01152"),
            ("doi:10.1107/S2052520616007447", "10.1107/s2052520616007447"),
            ("  10.1063/1.2210932/ ", "10.1063/1.2210932"),
            ("", ""),
        ]:
            self.assertEqual(corpus.normalize_doi(raw), want)

    def test_slugify(self):
        self.assertEqual(corpus.slugify("GAtor: A First-Principles GA!"), "gator-a-first-principles-ga")
        self.assertEqual(corpus.slugify(""), "untitled")
        self.assertTrue(len(corpus.slugify("x" * 200)) <= 60)

    def test_title_match_score(self):
        hi = corpus.title_match_score(
            "Report on the sixth blind test of organic crystal structure prediction methods",
            "Report on the sixth blind test of organic crystal-structure prediction methods")
        lo = corpus.title_match_score(
            "Report on the sixth blind test of organic crystal structure prediction methods",
            "Factors of Risk in the Development of Coronary Heart Disease")
        self.assertGreater(hi, 0.8)
        self.assertLess(lo, 0.2)
        self.assertEqual(corpus.title_match_score("", "x"), 0.0)

    def test_pick_pdf_url_fallback_order(self):
        w = {"best_oa_location": {"pdf_url": "https://a/x.pdf"},
             "locations": [{"pdf_url": "https://b/y.pdf"}],
             "open_access": {"oa_url": "https://c/z.pdf"}}
        self.assertEqual(corpus.pick_pdf_url(w), "https://a/x.pdf")
        del w["best_oa_location"]
        self.assertEqual(corpus.pick_pdf_url(w), "https://b/y.pdf")
        w["locations"] = []
        self.assertEqual(corpus.pick_pdf_url(w), "https://c/z.pdf")
        w["open_access"] = {"oa_url": "https://c/landing"}   # not a .pdf -> reject
        self.assertIsNone(corpus.pick_pdf_url(w))
        self.assertIsNone(corpus.pick_pdf_url({}))


WORK = {
    "id": "https://openalex.org/W123",
    "title": "Report on the sixth blind test of organic crystal structure prediction methods",
    "publication_year": 2016,
    "doi": "https://doi.org/10.1107/S2052520616007447",
    "cited_by_count": 605,
    "authorships": [{"author": {"display_name": "Anthony M. Reilly"}}],
    "primary_location": {"source": {"display_name": "Acta Crystallographica Section B"}},
    "best_oa_location": {"pdf_url": "https://journals.iucr.org/paper.pdf"},
}


class TestManifestEntry(unittest.TestCase):
    def test_schema_resolved(self):
        seed = {"slug": "blind-test-6", "tier": "A", "confirm": False}
        e = corpus.manifest_entry(seed, WORK, 1.0, "pdf", "raw/2026-08-25_x.pdf")
        for key in ("slug", "tier", "status", "needs_confirm", "match_score", "fulltext",
                    "raw_file", "title", "doi", "year", "venue", "citations", "authors", "openalex_id"):
            self.assertIn(key, e)
        self.assertEqual(e["status"], "resolved")
        self.assertEqual(e["doi"], "10.1107/s2052520616007447")   # normalized, from OpenAlex only
        self.assertEqual(e["openalex_id"], "W123")

    def test_schema_unresolved_keeps_seed_title(self):
        e = corpus.manifest_entry({"slug": "x", "tier": "G", "title": "Mystery"}, None, 0.2, "none", None,
                                  error="no confident OpenAlex match")
        self.assertEqual(e["status"], "unresolved")
        self.assertEqual(e["title"], "Mystery")


class TestResolve(unittest.TestCase):
    def test_doi_path_is_authoritative(self):
        def fake_fetch(url, **kw):
            self.assertIn("/works/doi:", url)
            return json.dumps(WORK).encode()
        work, score = corpus.resolve({"slug": "s", "doi": "10.1107/S2052520616007447"}, fetch=fake_fetch)
        self.assertEqual(score, 1.0)
        self.assertEqual(work["publication_year"], 2016)

    def test_title_search_picks_best_and_scores(self):
        results = {"results": [
            {"title": "Coronary Heart Disease Study", "publication_year": 1961},
            dict(WORK),
        ]}
        def fake_fetch(url, **kw):
            return json.dumps(results).encode()
        seed = {"slug": "s", "title": WORK["title"], "year": 2016}
        work, score = corpus.resolve(seed, fetch=fake_fetch)
        self.assertEqual(work["publication_year"], 2016)
        self.assertGreater(score, corpus.MATCH_THRESHOLD)

    def test_title_search_low_score_when_nothing_matches(self):
        def fake_fetch(url, **kw):
            return json.dumps({"results": [{"title": "Unrelated", "publication_year": 1999}]}).encode()
        work, score = corpus.resolve({"slug": "s", "title": WORK["title"], "year": 2016}, fetch=fake_fetch)
        self.assertLess(score, corpus.MATCH_THRESHOLD)


class TestDedupAndIdempotence(unittest.TestCase):
    def test_dedup_existing(self):
        with tempfile.TemporaryDirectory() as vault:
            os.makedirs(os.path.join(vault, "raw"))
            open(os.path.join(vault, "raw", "clip.md"), "w").write("x")
            self.assertEqual(corpus.dedup_existing({"existing_raw": "raw/clip.md"}, vault), "raw/clip.md")
            self.assertIsNone(corpus.dedup_existing({"existing_raw": "raw/nope.md"}, vault))
            self.assertIsNone(corpus.dedup_existing({}, vault))


if __name__ == "__main__":
    unittest.main(verbosity=2)
