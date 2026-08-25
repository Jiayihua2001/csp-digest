#!/usr/bin/env python3
"""Golden-file tests for review/render_learn.py (M5). Fully offline.

Run: python3 review/test_render_learn.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_learn as rl  # noqa: E402

TREE = {
    "spine_note": "Blind tests anchor progress.",
    "gator_position": "GAtor sits at generation x GA x ranking.",
    "branches": [
        {"key": "history", "overview": "The blind tests.", "papers": ["blind-test-6"],
         "concepts": ["csp-blind-tests"]},
        {"key": "generation", "overview": "Random and GA generation.", "papers": ["gator-2018"],
         "concepts": ["genetic-algorithm-csp"]},
    ],
}
CUR = {
    "stages": [
        {"title": "The spine", "goal": "What is CSP?", "why_now": "Backbone first.",
         "items": [{"slug": "blind-test-6", "why": "The benchmark."}],
         "gator_note": "Targets come from here."},
    ],
    "closing_note": "Keep going.",
}
MANIFEST = {
    "blind-test-6": {"slug": "blind-test-6", "tier": "A", "title": "Sixth blind test",
                     "doi": "10.1107/x", "year": 2016, "venue": "Acta B", "citations": 605,
                     "authors": ["A. Reilly"]},
    "gator-2018": {"slug": "gator-2018", "tier": "B", "title": "GAtor GA for CSP",
                   "doi": "10.1021/x", "year": 2018, "venue": "JCTC", "citations": 120,
                   "authors": ["F. Curtis"]},
}
SRC_MD = """---
type: source
---

# Sixth blind test

> Benchmark summary.

**Corpus:** tier A - `blind-test-6` - source mode: pdf - confidence: **high** - verified: all claims supported

## Contribution
Defined the SOTA.

## Linked concepts
[[csp-blind-tests]] [[gator-2018]]
"""


class TestRenderLearn(unittest.TestCase):
    def setUp(self):
        self.sources = {"blind-test-6": SRC_MD, "gator-2018": SRC_MD.replace("blind-test-6", "gator-2018")}

    def test_learn_page_markers(self):
        h = rl.render_learn_page(TREE, CUR, MANIFEST, self.sources, "2026-08-25")
        for marker in (
            "<h1>Learn MCSP</h1>",
            "History: the CSP blind tests",             # branch title from fixed BRANCHES
            "Structure generation &amp; search",
            'href="learn/blind-test-6.html"',           # paper links into subpages
            "Stage 1:", "What is CSP?",                 # curriculum rendering
            'class="badge-group"',                      # tier-B group badge (gator)
            'class="chip"',                             # concept chips
            "Where GAtor 2.0 sits",
        ):
            self.assertIn(marker, h)

    def test_branch_order_follows_fixed_spec(self):
        h = rl.render_learn_page(TREE, CUR, MANIFEST, self.sources, "2026-08-25")
        self.assertLess(h.index("History: the CSP blind tests"),
                        h.index("Structure generation"))

    def test_paper_page_contract(self):
        h = rl.render_paper_page("blind-test-6", SRC_MD, MANIFEST["blind-test-6"], set(self.sources))
        for marker in (
            "<h1>Sixth blind test</h1>",
            "doi:10.1107/x",
            "confidence: high",
            "<h2>Contribution</h2>",                    # md section -> h2
            'href="gator-2018.html"',                   # wikilink to digested source -> paper link
            'class="chip">csp-blind-tests',             # wikilink to concept -> chip
            'href="../index.html"',                     # back-nav from depth 1
        ):
            self.assertIn(marker, h)
        self.assertNotIn("verification flagged", h)     # clean page has no flag

    def test_verification_flag_surfaces(self):
        md = SRC_MD + "\n## Verification flags\n\n> issues\n"
        h = rl.render_paper_page("blind-test-6", md, MANIFEST["blind-test-6"], set(self.sources))
        self.assertIn("verification flagged claims", h)

    def test_group_badge_only_for_tier_b(self):
        h_a = rl.render_paper_page("blind-test-6", SRC_MD, MANIFEST["blind-test-6"], set(self.sources))
        h_b = rl.render_paper_page("gator-2018", SRC_MD, MANIFEST["gator-2018"], set(self.sources))
        self.assertNotIn("our group", h_a)
        self.assertIn("our group", h_b)

    def test_build_end_to_end_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            os.makedirs(os.path.join(vault, "wiki", "sources"))
            for slug, md in self.sources.items():
                open(os.path.join(vault, "wiki", "sources", f"2026-08-25_{slug}.md"), "w").write(md)
            site = os.path.join(tmp, "site")
            # point module at fixture JSONs
            import json as _json
            rl_tree, rl_cur, rl_man = rl.TREE_JSON, rl.CURRICULUM_JSON, rl.MANIFEST_PATH
            try:
                rl.TREE_JSON = os.path.join(tmp, "tree.json")
                rl.CURRICULUM_JSON = os.path.join(tmp, "cur.json")
                rl.MANIFEST_PATH = os.path.join(tmp, "man.json")
                _json.dump(TREE, open(rl.TREE_JSON, "w"))
                _json.dump(CUR, open(rl.CURRICULUM_JSON, "w"))
                _json.dump({"entries": MANIFEST}, open(rl.MANIFEST_PATH, "w"))
                out = rl.build(site_dir=site, vault=vault)
            finally:
                rl.TREE_JSON, rl.CURRICULUM_JSON, rl.MANIFEST_PATH = rl_tree, rl_cur, rl_man
            self.assertEqual(out["papers"], 2)
            self.assertTrue(os.path.exists(os.path.join(site, "learn.html")))
            self.assertTrue(os.path.exists(os.path.join(site, "learn", "blind-test-6.html")))
            self.assertTrue(os.path.exists(os.path.join(site, "learn", "gator-2018.html")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
