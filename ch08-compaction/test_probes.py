"""
Probe-question tests for the Chapter 8 compaction pipeline.

Stdlib-only (unittest), so it runs offline with no installs:

    python -m unittest -v

These are the tests the manuscript's 📎 callout refers to: they encode the
chapter's claim that compaction fidelity is measurable, and they would catch a
regression (a prompt edit or model change that silently starts dropping
commitments) before it reaches a customer.
"""

import unittest

from main import (
    FieldCompactor,
    NaiveCompactor,
    build_tree_strand_session,
    probe_set,
    score,
)


class ToolResultClearingTests(unittest.TestCase):
    def test_tool_results_are_the_real_bloat(self):
        s = build_tree_strand_session()
        # Tool payloads should dominate the window, not the conversation.
        self.assertGreater(s.tool_tokens(), 5 * s.conversation_tokens())

    def test_clearing_reclaims_most_of_the_window(self):
        s = build_tree_strand_session()
        before = s.total_tokens()
        reclaimed = s.clear_tool_results(keep_pointers=True)
        after = s.total_tokens()
        self.assertGreater(reclaimed, 0)
        self.assertLess(after, before // 5)          # >80% reclaimed
        # Pointers remain so a wrong bet costs one re-fetch, not the fact.
        self.assertTrue(all(not t.used and t.cleared_note for t in s.tools))


class ProbeQuestionTests(unittest.TestCase):
    def setUp(self):
        self.session = build_tree_strand_session()
        self.probes = probe_set()

    def test_field_naming_compactor_preserves_all_task_critical_state(self):
        state = FieldCompactor().extract(self.session)
        passed, failures = score(state, self.probes)
        self.assertEqual(passed, len(self.probes), f"unexpected failures: {failures}")

    def test_naive_compactor_leaks_commitments_and_amounts(self):
        state = NaiveCompactor().extract(self.session)
        passed, failures = score(state, self.probes)
        self.assertLess(passed, len(self.probes))
        # The specific, dangerous drops the chapter warns about:
        self.assertIn("Was a no-charge replacement promised?", failures)
        self.assertIn("Was a refund/reversal promised, and for how much?", failures)

    def test_compacted_state_is_far_smaller_than_the_raw_session(self):
        raw = self.session.total_tokens()
        from main import state_tokens
        compacted = state_tokens(FieldCompactor().extract(self.session))
        self.assertLess(compacted, raw // 10)        # order-of-magnitude smaller


if __name__ == "__main__":
    unittest.main(verbosity=2)
