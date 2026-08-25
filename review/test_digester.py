#!/usr/bin/env python3
"""Contract tests for review/digester.py (M2). No network: LLM calls injected.

Run: python3 review/test_digester.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digester  # noqa: E402

ENTRY = {
    "slug": "blind-test-6", "tier": "A", "status": "resolved",
    "title": "Report on the sixth blind test of organic crystal structure prediction methods",
    "doi": "10.1107/s2052520616007447", "year": 2016,
    "venue": "Acta Crystallographica Section B", "citations": 605,
    "authors": ["Anthony M. Reilly", "Richard I. Cooper"],
    "openalex_id": "W123", "fulltext": "abstract-only", "raw_file": None,
}

BRIEF = {
    "summary": "The community benchmark for CSP methods.",
    "contribution": "Defined the state of the art across five target classes.",
    "method": "Blind prediction against withheld experimental structures.",
    "key_results": ["25 groups participated", "flexible molecule hardest"],
    "limitations": ["0 K lattice energies only"],
    "takeaways": ["CSP = generation + ranking", "blind tests anchor progress"],
    "gator_relevance": "GAtor targets come from these tests.",
    "concepts": ["csp-blind-tests", "crystal-structure-prediction"],
    "tags": ["blind-test"],
    "confidence": "medium",
}


def fake_brief(doc, ctx, model, key):
    return dict(BRIEF)


def fake_verify_ok(doc, ctx, brief, model, key):
    return "ALL SUPPORTED"


def fake_verify_flagged(doc, ctx, brief, model, key):
    return "The claim '25 groups participated' is not supported by the abstract."


class TestDigester(unittest.TestCase):
    def setUp(self):
        # keep tests fully offline: abstract fetch is stubbed out
        self._orig_fetch_abstract = digester.fetch_abstract
        digester.fetch_abstract = lambda entry, fetch=None: None

    def tearDown(self):
        digester.fetch_abstract = self._orig_fetch_abstract

    def _vault(self):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "wiki", "sources"))
        open(os.path.join(d, "log.md"), "w").write("# log\n")
        return d

    def test_page_contract(self):
        vault = self._vault()
        path = digester.digest_one(ENTRY, vault, "m", "k",
                                   brief_fn=fake_brief, verify_fn=fake_verify_ok)
        self.assertTrue(path and os.path.exists(path))
        self.assertTrue(os.path.basename(path).endswith("_blind-test-6.md"))
        page = open(path).read()
        # frontmatter contract (vault schema)
        for needle in ("type: source", 'source_url: "https://doi.org/10.1107/s2052520616007447"',
                       "ingested:", "raw_path: n/a", "mcsp-corpus"):
            self.assertIn(needle, page)
        # section contract (M5 renderer depends on these)
        for sec in ("## Contribution", "## Method", "## Key results", "## Limitations",
                    "## Takeaways", "## Relevance to GAtor 2.0", "## Linked concepts"):
            self.assertIn(sec, page)
        self.assertIn("[[csp-blind-tests]]", page)
        self.assertIn("confidence: **medium**", page)
        self.assertIn("verified: all claims supported", page)
        self.assertNotIn("## Verification flags", page)
        # log appended
        self.assertIn("M2 digester", open(os.path.join(vault, "log.md")).read())

    def test_verification_flag_surfaces(self):
        vault = self._vault()
        path = digester.digest_one(ENTRY, vault, "m", "k",
                                   brief_fn=fake_brief, verify_fn=fake_verify_flagged)
        page = open(path).read()
        self.assertIn("## Verification flags", page)
        self.assertIn("FLAGGED", page)

    def test_idempotent_skip_and_force(self):
        vault = self._vault()
        p1 = digester.digest_one(ENTRY, vault, "m", "k", brief_fn=fake_brief, verify_fn=fake_verify_ok)
        self.assertIsNotNone(p1)
        p2 = digester.digest_one(ENTRY, vault, "m", "k", brief_fn=fake_brief, verify_fn=fake_verify_ok)
        self.assertIsNone(p2)                       # skipped
        p3 = digester.digest_one(ENTRY, vault, "m", "k", brief_fn=fake_brief,
                                 verify_fn=fake_verify_ok, force=True)
        self.assertIsNotNone(p3)                    # redone

    def test_metadata_mode_when_no_fulltext(self):
        vault = self._vault()
        block, ctx, mode = digester.load_document(dict(ENTRY, raw_file=None), vault)
        self.assertIsNone(block)
        self.assertEqual(mode, "metadata")
        self.assertIn("confidence to 'low'", ctx)

    def test_clipping_mode(self):
        vault = self._vault()
        os.makedirs(os.path.join(vault, "raw"), exist_ok=True)
        open(os.path.join(vault, "raw", "clip.md"), "w").write("Full text here " * 10)
        block, ctx, mode = digester.load_document(dict(ENTRY, raw_file="raw/clip.md"), vault)
        self.assertIsNone(block)
        self.assertEqual(mode, "clipping")
        self.assertIn("Full text here", ctx)


if __name__ == "__main__":
    unittest.main(verbosity=2)
