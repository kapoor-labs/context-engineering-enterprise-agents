"""
Tests for the Chapter 13 retrieval-time access control demo.

Stdlib-only (unittest), runs offline:

    python -m unittest -v

They pin the chapter's claims: on-behalf-of retrieval scopes context to the
operator's identity at the data layer (so the same query returns different
columns to different roles), archived content is never served, the Chapter 12
attack dies at retrieval, and the super-identity anti-pattern leaks what
on-behalf-of withholds.
"""

import unittest

from main import ContextLayer, Identity, build_layer


class RetrievalAclTests(unittest.TestCase):
    def setUp(self):
        self.layer = build_layer()
        self.first_line = Identity("csa:firstline", {"csa.read"})
        self.fraud = Identity("investigator", {"csa.read", "csa.fraud"})

    def _order_cols(self, results):
        for r in results:
            if r["rec_id"] == "NW-6612480":
                return set(r["fields"])
        return set()

    def test_same_query_different_columns_by_identity(self):
        q = "everything on order NW-6612480"
        fl = self._order_cols(self.layer.retrieve(q, self.first_line))
        fr = self._order_cols(self.layer.retrieve(q, self.fraud))
        self.assertNotIn("payment_instrument", fl)     # first-line withheld
        self.assertIn("payment_instrument", fr)        # fraud authorized
        self.assertIn("status", fl)                    # both see the basics
        self.assertTrue(fl.issubset(fr))               # strictly less, not different

    def test_archived_policy_is_never_served(self):
        results = self.layer.retrieve("returns policy", self.first_line)
        sources = [r["source"] for r in results]
        self.assertIn("kb://returns/policy", sources)
        self.assertNotIn("kb://returns/policy/archive-2019", sources)

    def test_chapter_12_attack_dies_at_retrieval(self):
        # Injected instruction under a first-line identity asks for payment data
        # and a fabricated "priority policy".
        results = self.layer.retrieve(
            "everything on order NW-6612480 and the priority policy",
            self.first_line)
        self.assertNotIn("payment_instrument", self._order_cols(results))
        self.assertFalse(any("priority" in r["source"].lower() for r in results))

    def test_super_identity_leaks_what_on_behalf_of_withholds(self):
        leaked = self._order_cols(
            self.layer.retrieve("everything on order NW-6612480", None, as_super=True))
        self.assertIn("payment_instrument", leaked)    # the pitfall, demonstrated

    def test_row_level_security_blocks_unauthorized_role(self):
        outsider = Identity("marketing", {"marketing.read"})
        results = self.layer.retrieve("everything on order NW-6612480", outsider)
        self.assertEqual(results, [])                  # no matching role -> nothing

    def test_every_retrieval_is_audited(self):
        self.layer.retrieve("returns policy", self.first_line)
        self.assertTrue(self.layer.audit)
        last = self.layer.audit[-1]
        self.assertEqual(last["acting_as"], "csa:firstline")
        self.assertIn("returned", last)


if __name__ == "__main__":
    unittest.main(verbosity=2)
