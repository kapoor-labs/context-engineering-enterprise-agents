"""
Tests for the Chapter 9 context-isolation demonstration.

Stdlib-only (unittest), runs offline:

    python -m unittest -v

They pin the chapter's claim: isolation fixes the contamination bug
*structurally*. The shared-context run reproduces the misrouting; the isolated
run cannot, and its resolution context is a fraction of the size.
"""

import unittest

from main import Contact, run_isolated, run_shared, triage, TaskSpec


CONTACT = Contact(
    customer_id="C-4471",
    first_message=("My replacement is delayed and I think I was charged "
                   "twice for order NW-4820193."))


class ContaminationTests(unittest.TestCase):
    def test_triage_concludes_billing_regardless_of_orchestration(self):
        spec = TaskSpec("classify", {"opening_message": CONTACT.first_message,
                                     "customer_id": CONTACT.customer_id}, ())
        _, result = triage(spec)
        self.assertEqual(result.category, "billing")

    def test_shared_context_contaminates_resolution(self):
        run = run_shared(CONTACT)
        # Triage concluded billing, but the deliberation drags resolution onto shipping.
        self.assertTrue(run["contaminated"])
        self.assertEqual(run["opened_on"], "shipping")
        self.assertNotEqual(run["opened_on"], run["concluded"])

    def test_isolation_prevents_contamination(self):
        run = run_isolated(CONTACT)
        self.assertFalse(run["contaminated"])
        self.assertEqual(run["opened_on"], "billing")
        self.assertEqual(run["opened_on"], run["concluded"])

    def test_isolated_resolution_context_is_much_smaller(self):
        shared = run_shared(CONTACT)
        isolated = run_isolated(CONTACT)
        # Only the conclusion crosses the boundary, so the window is far smaller.
        self.assertLess(isolated["context_tokens"], shared["context_tokens"] // 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
