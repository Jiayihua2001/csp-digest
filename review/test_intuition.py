#!/usr/bin/env python3
"""Offline tests for review/intuition.py. Run: python3 review/test_intuition.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intuition  # noqa: E402

REC = {
    "slug": "nyman-day-statistics-2015", "title": "Static and lattice vibrational energy differences",
    "doi": "10.1039/c5ce00045a", "year": 2015, "tier": "C", "source_mode": "pdf",
    "date": "2026-09-04",
    "core_idea": "Large-sample statistics of polymorph energetics.",
    "innovation": "First big CSD-scale polymorph energy survey.",
    "chunks": [
        {"type": "statistic", "statement": "Most polymorph pairs differ by < 2 kJ/mol",
         "scope": "508 organic polymorph pairs", "evidence": "over half within 2 kJ/mol",
         "generality": "established"},
        {"type": "decision_rule", "statement": "Vibrational free energy can reorder ~9% of pairs",
         "scope": "harmonic estimates on the same set", "evidence": "9% reordering reported",
         "generality": "suggested"},
    ],
    "synthesis": "Energy windows justify tight GA convergence thresholds.",
}
DB = {"records": [REC]}


class TestPick(unittest.TestCase):
    def test_fulltext_first_and_skip_done(self):
        manifest = {
            "a": {"slug": "a", "status": "resolved", "fulltext": "abstract-only"},
            "b": {"slug": "b", "status": "resolved", "fulltext": "pdf"},
            "c": {"slug": "c", "status": "deferred"},
        }
        self.assertEqual(intuition.pick_next(manifest, {"records": []})["slug"], "b")
        self.assertEqual(intuition.pick_next(manifest, {"records": [{"slug": "b"}]})["slug"], "a")
        self.assertIsNone(intuition.pick_next(manifest, {"records": [{"slug": "a"}, {"slug": "b"}]}))


class TestRender(unittest.TestCase):
    def test_vault_page(self):
        md = intuition.render_vault_page(DB, {"nyman-day-statistics-2015": ("2026-08-25_nyman-day-statistics-2015", "")},
                                         "2026-09-04")
        for needle in ("# MCSP intuition handbook", "Field statistics & magic numbers",
                       "Most polymorph pairs differ by < 2 kJ/mol",
                       "[[2026-08-25_nyman-day-statistics-2015|",
                       "generality: *established*", "Decision rules",
                       "Paper syntheses (assistant interpretation)"):
            self.assertIn(needle, md)

    def test_site_page(self):
        h = intuition.render_site_page(DB, "2026-09-04")
        for needle in ("intuition handbook", "Today's paper", "Core idea:",
                       "Most polymorph pairs differ by &lt; 2 kJ/mol" if "&lt;" in intuition.render_site_page(DB, "x")
                       else "Most polymorph pairs", 'class="gen-established"',
                       "Assistant synthesis (interpretation)", 'href="https://doi.org/10.1039/c5ce00045a"'):
            self.assertIn(needle, h)
        self.assertIn("2 intuition chunks from 1 papers", h)
        # starring + explicit source URLs + nav to the other pages
        self.assertIn('data-cid="nyman-day-statistics-2015:0"', h)
        self.assertIn('class="cstar"', h)
        self.assertIn("doi.org/10.1039/c5ce00045a", h)
        self.assertIn('href="intuition-history.html"', h)
        self.assertIn('href="intuition-starred.html"', h)

    def test_history_page(self):
        h = intuition.render_history_page(DB, "2026-09-04")
        for needle in ("Distillation history", "1 papers distilled", "Core idea:",
                       "2026-09-04 &mdash; pdf", 'data-cid="nyman-day-statistics-2015:1"',
                       "Assistant synthesis (interpretation)"):
            self.assertIn(needle, h)

    def test_starred_page(self):
        h = intuition.render_starred_page(DB, "2026-09-04")
        for needle in ("My starred intuitions", 'id="starlist"', 'id="copystars"',
                       "const DATA=", "renderStars", "nyman-day-statistics-2015:0",
                       "Copy as Markdown"):
            self.assertIn(needle, h)

    def test_render_all_writes_three_pages(self):
        import tempfile, json as _json
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            os.makedirs(os.path.join(vault, "wiki", "syntheses"))
            orig_repo = intuition.REPO
            try:
                intuition.REPO = tmp
                os.makedirs(os.path.join(tmp, "site"))
                intuition.render_all(DB, vault)
            finally:
                intuition.REPO = orig_repo
            for f in ("intuition.html", "intuition-history.html", "intuition-starred.html"):
                self.assertTrue(os.path.exists(os.path.join(tmp, "site", f)), f)
            self.assertTrue(os.path.exists(os.path.join(vault, "wiki", "syntheses",
                                                        "mcsp-intuition-handbook.md")))

    def test_abstract_only_flagged(self):
        rec2 = dict(REC, source_mode="metadata", slug="x2", chunks=[dict(REC["chunks"][0])])
        h = intuition.render_site_page({"records": [rec2]}, "2026-09-04")
        self.assertIn("(abstract-only)", h)


if __name__ == "__main__":
    unittest.main(verbosity=1)
