"""
Tests for the Chapter 11 session-continuity investigation.

Stdlib-only (unittest), runs offline:

    python -m unittest -v

They pin the chapter's canon: a long-horizon task survives session boundaries
via durable state alone (the fresh-instance test), a blocked external dependency
suspends and resumes cleanly, and idempotent write tools make a crash-and-replay
safe (the submit is CALLED twice but SUBMITTED once).
"""

import unittest

from main import Store, World, run_session, SessionCrash


class ContinuityTests(unittest.TestCase):
    def test_investigation_completes_across_sessions(self):
        store, world = Store(), World(bank_reply_day=3)
        task = "T1"
        self.assertEqual(run_session(store, world, task, day=1), "waiting")
        self.assertEqual(run_session(store, world, task, day=4), "complete")
        state = store.load(task)
        self.assertTrue(all(s["status"] == "done" for s in state["plan"]))
        self.assertIsNotNone(state["receipt"])
        self.assertEqual(world.submit_calls, 1)      # submitted exactly once

    def test_blocked_on_external_dependency_then_resumes(self):
        store, world = Store(), World(bank_reply_day=3)
        task = "T2"
        # Before the bank replies, the await step blocks and the session waits.
        self.assertEqual(run_session(store, world, task, day=2), "waiting")
        self.assertEqual(_status(store, task, 3), "blocked")
        # Once it replies, a later session sails past it to completion.
        self.assertEqual(run_session(store, world, task, day=5), "complete")

    def test_fresh_instance_continues_from_store_alone(self):
        # Each run_session call is a fresh instance with NO shared context; the
        # only continuity is the Store. If this completes, continuity holds.
        store, world = Store(), World(bank_reply_day=2)
        task = "T3"
        run_session(store, world, task, day=0)       # establish, wait
        run_session(store, world, task, day=1)       # still waiting
        result = run_session(store, world, task, day=3)   # a "stranger" finishes it
        self.assertEqual(result, "complete")
        self.assertIsNotNone(store.load(task)["receipt"])

    def test_no_step_is_redone(self):
        store, world = Store(), World(bank_reply_day=1)
        task = "T4"
        run_session(store, world, task, day=0)       # waits
        run_session(store, world, task, day=2)       # completes
        # Evidence gathered once each; the world saw exactly one submission.
        state = store.load(task)
        self.assertEqual(set(state["evidence"]), {"order", "scans", "bank_reply"})
        self.assertEqual(len(world.submissions), 1)


class IdempotencyTests(unittest.TestCase):
    def test_crash_after_submit_does_not_double_submit_on_resume(self):
        store, world = Store(), World(bank_reply_day=1)
        task = "T5"
        run_session(store, world, task, day=0)       # establish, wait
        with self.assertRaises(SessionCrash):
            run_session(store, world, task, day=2, crash_before_recording=True)
        # The crash left the submit step unrecorded, so resume calls submit again.
        result = run_session(store, world, task, day=2)
        self.assertEqual(result, "complete")
        self.assertEqual(world.submit_calls, 2)      # called twice (crash + replay)
        self.assertEqual(len(world.submissions), 1)  # but only ONE real submission
        self.assertIsNotNone(store.load(task)["receipt"])

    def test_partial_package_progress_survives_and_is_not_restarted(self):
        # package_progress is checkpointed per part, so a resume continues it.
        store, world = Store(), World(bank_reply_day=1)
        task = "T6"
        run_session(store, world, task, day=0)
        try:
            run_session(store, world, task, day=2, crash_before_recording=True)
        except SessionCrash:
            pass
        # After the crash, all three package parts were already checkpointed.
        self.assertEqual(store.load(task)["package_progress"],
                         ["order", "scans", "policy_citation"])


def _status(store: Store, task: str, step_id: int) -> str:
    for s in store.load(task)["plan"]:
        if s["id"] == step_id:
            return s["status"]
    raise AssertionError("step not found")


if __name__ == "__main__":
    unittest.main(verbosity=2)
