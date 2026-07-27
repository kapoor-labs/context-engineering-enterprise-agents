"""
Tests for the Chapter 10 minimal orchestrator.

Stdlib-only (unittest), runs offline:

    python -m unittest -v

They pin the chapter's claims: durable state + checkpoints make a workflow
resumable and idempotent (the refund is issued exactly once across an
interruption), retries handle transient failures, routing includes a QA-fail
loop-back that fixes the named defect without re-issuing the refund, and the
approval gate is a real pause, not a prompt.
"""

import unittest

from main import (
    AwaitingApproval,
    build_workflow,
    scenario_approval_and_resume,
    scenario_qa_fail_loops_back,
    Node,
    Workflow,
)


class ResumeAndIdempotencyTests(unittest.TestCase):
    def test_refund_issued_exactly_once_across_interruption(self):
        state = scenario_approval_and_resume()
        self.assertEqual(state["refund_issued_count"], 1)
        self.assertEqual(state["qa_verdict"], "pass")

    def test_all_stages_checkpointed(self):
        state = scenario_approval_and_resume()
        for stage in ("triage", "resolution", "approval", "qa"):
            self.assertIn(stage, state["checkpoints"])

    def test_audit_records_the_approver(self):
        state = scenario_approval_and_resume()
        self.assertTrue(any("lead:ravi" in e for e in state["audit"]))


class RoutingTests(unittest.TestCase):
    def test_qa_fail_loops_back_and_fixes_named_defect(self):
        state = scenario_qa_fail_loops_back()
        self.assertEqual(state["qa_verdict"], "pass")
        self.assertTrue(state["disclosure_given"])
        # The loop-back re-ran resolution and qa (they appear twice)...
        self.assertEqual(state["checkpoints"].count("resolution"), 2)
        self.assertEqual(state["checkpoints"].count("qa"), 2)
        # ...but the refund was NOT re-issued on the second pass.
        self.assertEqual(state["refund_issued_count"], 1)

    def test_low_confidence_triage_escalates_to_human(self):
        wf = build_workflow()
        # Stop as soon as triage routes, so we only inspect the routing decision.
        state = {"confidence": 0.3}
        node = wf.nodes["triage"]
        node.run(state)
        state.update({"confidence": 0.3})
        self.assertEqual(node.route(state), "human_review")


class ApprovalGateTests(unittest.TestCase):
    def test_workflow_pauses_when_not_approved(self):
        wf = build_workflow()
        state = {"disclosure_given": True}
        with self.assertRaises(AwaitingApproval):
            wf.run(state)
        # It paused at approval; resolution ran, approval did not complete.
        self.assertIn("resolution", state["completed"])
        self.assertNotIn("approval", state["completed"])
        self.assertEqual(state["refund_issued_count"], 0)  # no money moved


if __name__ == "__main__":
    unittest.main(verbosity=2)
