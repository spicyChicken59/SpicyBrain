"""Negation and unknown cases for the source classifier in academy-source-review.py.

A record's words decide how its URL was checked. These cases pin the rules
that keep a negated or second-hand statement from counting as a read.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("source_review", ROOT / "scripts" / "academy-source-review.py")
source_review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source_review)
classify = source_review.classify


class ClassifyTest(unittest.TestCase):
    def test_read_in_this_build(self):
        self.assertEqual(classify("Read in this build on 2026-09-23 from https://raw.githubusercontent.com/o/r/abc/f.py."), "read-this-build")

    def test_page_body_not_fetched_is_never_a_read(self):
        text = ("Search-result title and snippet confirmed 2026-09-23; page body not fetched in this build "
                "(documentation host blocked by the sandbox egress proxy).")
        self.assertEqual(classify(text), "search-level")

    def test_fetched_in_this_build_inside_a_negation(self):
        self.assertEqual(classify("Search result confirmed; the page body was not fetched in this build."), "search-level")

    def test_unverified_author_summary_is_not_a_read(self):
        text = ("Search-result title and snippet confirmed 2026-09-23; page body not fetched in this build. "
                "Unverified summary written by the module's author; no read of this page body is recorded in this "
                "build or in any earlier review: the page says X.")
        self.assertEqual(classify(text), "search-level")

    def test_a_negated_read_is_never_a_read(self):
        text = "Search-result title and snippet confirmed 2026-09-23 (not a read in this build)."
        self.assertEqual(classify(text), "search-level")

    def test_not_confirmed_wins_over_any_stronger_word(self):
        self.assertEqual(classify("Read in this build? No: the URL could not be confirmed."), "unconfirmed")

    def test_not_searched_or_fetched_is_unconfirmed(self):
        self.assertEqual(classify("Not searched or fetched in this authoring session."), "unconfirmed")

    def test_neither_title_nor_body_is_unconfirmed(self):
        self.assertEqual(classify("Neither the title nor the body was re-checked."), "unconfirmed")

    def test_silence_is_unstated_not_unsupported(self):
        self.assertEqual(classify(""), "unstated")
        self.assertEqual(classify("An overview page."), "unstated")

    def test_earlier_release_review(self):
        self.assertEqual(classify("Reviewed on 2026-09-19 for the GenAI module and recorded in that module's source record."), "earlier-release")

    def test_package_source(self):
        self.assertEqual(classify("Facts read from the wheel published on PyPI."), "package-source")


if __name__ == "__main__":
    unittest.main()
