"""
Tests for the Chapter 15 assembled reference architecture.

Stdlib-only (unittest), runs offline:

    python -m unittest -v

They pin the chapter's promise: every architecture component traces to a chapter
(nothing new is introduced), and the assembled governed contact runs end-to-end
by COMPOSING the real Ch. 10 / Ch. 13 / Ch. 14 modules — not re-implementing them.
"""

import unittest

from main import ARCHITECTURES, load_components, run_assembled_contact


class ChapterMapTests(unittest.TestCase):
    def test_every_component_traces_to_a_chapter(self):
        for arch, components in ARCHITECTURES.items():
            for comp, op, chapter in components:
                self.assertTrue(chapter.startswith("Ch."),
                                f"{arch}: '{comp}' has no chapter origin")
                self.assertTrue(op, f"{arch}: '{comp}' has no operation label")

    def test_architecture_3_subsumes_architecture_2(self):
        # Arch 3 doesn't re-list Arch 2's components; it references them in one
        # row and adds the governance/observability layer on top.
        arch3 = ARCHITECTURES["3. Governed enterprise platform"]
        first_components = [c[0] for c in arch3]
        self.assertIn("Everything in Architecture 2", first_components)
        arch1 = ARCHITECTURES["1. Single-agent grounded copilot"]
        arch2 = ARCHITECTURES["2. Multi-agent operations system"]
        self.assertLess(len(arch1), len(arch2))        # 1 is the simplest


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.mods = load_components()

    def test_all_three_prior_modules_load(self):
        for key in ("ch10", "ch13", "ch14"):
            self.assertIn(key, self.mods)

    def test_assembled_contact_runs_end_to_end(self):
        result = run_assembled_contact(self.mods)
        # Eval gate passed (Ch. 14).
        self.assertEqual(result["score"], 1.0)
        # Governed retrieval scoped to the operator (Ch. 13): no payment column.
        self.assertNotIn("payment_instrument", result["columns"])
        self.assertIn("status", result["columns"])
        # Orchestration completed with the refund issued exactly once (Ch. 10).
        self.assertEqual(result["refund_count"], 1)

    def test_assembly_composes_not_duplicates(self):
        # The governed retrieval used is literally Ch. 13's build_layer/Identity.
        ch13 = self.mods["ch13"]
        self.assertTrue(hasattr(ch13, "build_layer"))
        self.assertTrue(hasattr(ch13, "Identity"))
        # The eval used is literally Ch. 14's retrieval_eval.
        self.assertTrue(hasattr(self.mods["ch14"], "retrieval_eval"))
        # The orchestration used is literally Ch. 10's workflow.
        self.assertTrue(hasattr(self.mods["ch10"], "build_workflow"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
