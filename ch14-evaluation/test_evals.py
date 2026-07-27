"""
Tests for the Chapter 14 evaluation instruments.

Stdlib-only (unittest), runs offline:

    python -m unittest -v

They pin the chapter's claims: the rubric routes the book's four failures to
"context" (and non-context failures out of the model column), the retrieval
golden set catches a bad policy-article edit before it ships, and the compaction
probe eval scores fidelity as a regressable number.
"""

import unittest

from main import (
    BOOK_FAILURES,
    GOLDEN_SET,
    PROBES,
    Article,
    FailureSignals,
    build_corpus,
    classify_failure,
    compaction_probe_eval,
    field_compactor,
    naive_compactor,
    retrieval_eval,
)


class RubricTests(unittest.TestCase):
    def test_all_four_book_failures_are_context_failures(self):
        for label, sig in BOOK_FAILURES.items():
            self.assertEqual(classify_failure(sig), "context", label)

    def test_tool_failure_is_not_called_a_model_failure(self):
        sig = FailureSignals(True, True, False, False)
        self.assertEqual(classify_failure(sig), "tool")

    def test_orchestration_failure_is_routed_to_the_seam(self):
        sig = FailureSignals(True, False, True, False)
        self.assertEqual(classify_failure(sig), "orchestration")

    def test_genuine_model_failure_requires_correct_context(self):
        sig = FailureSignals(True, False, False, True)
        self.assertEqual(classify_failure(sig), "model")

    def test_tool_is_ruled_out_before_orchestration(self):
        # Both signals present -> tool wins (checked first).
        sig = FailureSignals(True, True, True, False)
        self.assertEqual(classify_failure(sig), "tool")


class RetrievalGoldenSetTests(unittest.TestCase):
    def test_baseline_passes(self):
        score, fails = retrieval_eval(GOLDEN_SET, build_corpus())
        self.assertEqual(score, 1.0)
        self.assertEqual(fails, [])

    def test_bad_policy_edit_is_caught_by_the_eval(self):
        corpus = build_corpus()
        corpus["standard-returns"] = Article("Returns accepted within 3 dys.", "current")
        score, fails = retrieval_eval(GOLDEN_SET, corpus)
        self.assertLess(score, 1.0)
        self.assertTrue(fails)

    def test_archived_article_is_never_retrieved(self):
        # Even though it also matches "return", it's archived -> filtered out.
        from main import retrieve
        hits = [h[0] for h in retrieve("return window", build_corpus())]
        self.assertIn("standard-returns", hits)
        self.assertNotIn("returns-archive-2019", hits)


class CompactionProbeTests(unittest.TestCase):
    def test_field_compactor_preserves_all_probes(self):
        self.assertEqual(compaction_probe_eval(field_compactor, PROBES), 1.0)

    def test_naive_compactor_regresses(self):
        self.assertLess(compaction_probe_eval(naive_compactor, PROBES), 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
