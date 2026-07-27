#!/usr/bin/env python3
"""
Session continuity for a long-horizon task — companion code for Chapter 11,
"Long-Horizon Agents and Session Continuity."

Runs the week-long chargeback dispute investigation as a series of separate
SESSIONS that survive across boundaries because all task-critical state lives in
a durable store, not in any session's context. Demonstrates the chapter's
composition — the continuity stack — plus its two canonical ideas:

  * THE FRESH-INSTANCE TEST: every session is a brand-new instance that holds NO
    context from prior sessions; it continues purely from the persisted state.
    If that works, you have session continuity. We also run it as an explicit
    "kill mid-task and resume from a stranger" check.

  * IDEMPOTENT WRITE TOOLS: the submit step carries an idempotency key, so a
    replay after a crash (the gap between "the side effect happened" and "we
    recorded it") cannot submit the dispute twice.

The continuity stack in code:
  - durable task state (write, Ch. 6)      -> Store (stands in for Dataverse)
  - per-session working set (select, Ch. 5) -> each step loads only what it needs
  - session-boundary compaction (Ch. 8)     -> each step commits a compact result
  - checkpointed workflow position (Ch. 10) -> the plan's step statuses

Everything is deterministic and stdlib-only, so it verifies offline. Sessions
carry no context between calls: continuity is entirely via the Store.

    python main.py            # or --demo
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Durable store — stands in for a governed Dataverse record. The ONLY thing that
# survives between sessions. (In-memory here; a real one persists to Dataverse.)
# --------------------------------------------------------------------------- #
class Store:
    def __init__(self) -> None:
        self._rows: dict[str, dict] = {}

    def load(self, task_id: str) -> dict | None:
        # Return a deep-ish copy so a session can't mutate durable state except
        # by an explicit save() — models a real store boundary.
        row = self._rows.get(task_id)
        return _copy(row) if row is not None else None

    def save(self, task_id: str, state: dict) -> None:
        self._rows[task_id] = _copy(state)


def _copy(obj):
    if isinstance(obj, dict):
        return {k: _copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_copy(v) for v in obj]
    return obj


# --------------------------------------------------------------------------- #
# The outside world the investigation depends on: OrderCore, the carrier, and a
# bank that replies only after a few days (why no single session survives it).
# The bank also records submissions BY IDEMPOTENCY KEY.
# --------------------------------------------------------------------------- #
@dataclass
class World:
    bank_reply_day: int = 3
    submissions: dict[str, str] = field(default_factory=dict)  # key -> receipt
    submit_calls: int = 0

    def order_record(self) -> str:
        return "order NW-6612480: $340, delivered"

    def carrier_scans(self) -> str:
        return "carrier scan: delivered 2026-07-18, signature on file"

    def bank_reply_available(self, day: int) -> bool:
        return day >= self.bank_reply_day

    def bank_reply(self) -> str:
        return "bank requests proof-of-delivery to their standard"

    def submit_dispute(self, idempotency_key: str, package: list[str]) -> str:
        """Idempotent: a replay with a seen key returns the original receipt."""
        self.submit_calls += 1
        if idempotency_key in self.submissions:
            return self.submissions[idempotency_key]        # replay-safe
        receipt = f"RECEIPT-{len(self.submissions) + 1}"
        self.submissions[idempotency_key] = receipt
        return receipt


# --------------------------------------------------------------------------- #
# The task state (the "case file") and its plan (the checkpointed workflow
# position). Fresh state is created only on the first session.
# --------------------------------------------------------------------------- #
def new_investigation(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "deadline": "2026-07-31",
        "done_definition": "evidence package submitted and receipt recorded",
        "plan": [
            {"id": 1, "name": "obtain_order_record", "status": "open"},
            {"id": 2, "name": "obtain_carrier_scans", "status": "open"},
            {"id": 3, "name": "await_bank_reply", "status": "open"},
            {"id": 4, "name": "package_evidence", "status": "open"},
            {"id": 5, "name": "submit_and_record", "status": "open"},
        ],
        "evidence": {},
        "package_progress": [],   # partial-progress for the multi-part step 4
        "receipt": None,
    }


def next_open_step(state: dict) -> dict | None:
    for step in state["plan"]:
        if step["status"] != "done":
            return step
    return None


def mark(state: dict, step_id: int, status: str) -> None:
    for step in state["plan"]:
        if step["id"] == step_id:
            step["status"] = status


class SessionCrash(Exception):
    """Simulates a process death mid-step (uncommitted work in flight)."""


# --------------------------------------------------------------------------- #
# A SESSION. Each call is a fresh instance: it holds no state except what it
# loads from the store. It runs steps until one is blocked, the task completes,
# or (in the crash demo) it dies mid-step.
# --------------------------------------------------------------------------- #
def run_session(store: Store, world: World, task_id: str, day: int,
                crash_before_recording: bool = False) -> str:
    # --- load + verify (or establish, on the first session) ---------------- #
    state = store.load(task_id)
    if state is None:
        state = new_investigation(task_id)
        store.save(task_id, state)        # establish the case file

    while True:
        step = next_open_step(state)
        if step is None:
            return "complete"

        name = step["name"]

        if name == "await_bank_reply":
            if not world.bank_reply_available(day):
                mark(state, step["id"], "blocked")
                store.save(task_id, state)
                return "waiting"          # session ends; a later day resumes
            state["evidence"]["bank_reply"] = world.bank_reply()

        elif name == "obtain_order_record":
            state["evidence"]["order"] = world.order_record()

        elif name == "obtain_carrier_scans":
            state["evidence"]["scans"] = world.carrier_scans()

        elif name == "package_evidence":
            # Multi-part step with partial-progress checkpointing, so a crash
            # mid-package resumes from the last attached part, not from scratch.
            parts = ["order", "scans", "policy_citation"]
            for part in parts:
                if part in state["package_progress"]:
                    continue              # already attached in a prior (crashed) session
                state["package_progress"].append(part)
                store.save(task_id, state)   # checkpoint each part

        elif name == "submit_and_record":
            key = f"{task_id}:submit"     # idempotency key (Ch. 7 write-tool caution)
            if crash_before_recording:
                # The side effect happens, then the process dies BEFORE recording
                # it. A naive resume would submit again — idempotency prevents it.
                world.submit_dispute(key, state["package_progress"])
                store.save(task_id, state)   # step still 'open' — not recorded!
                raise SessionCrash("died after submit, before recording")
            receipt = world.submit_dispute(key, state["package_progress"])
            state["receipt"] = receipt

        mark(state, step["id"], "done")
        store.save(task_id, state)        # compact result to durable state


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def run_demo() -> None:
    print("Chapter 11 - session continuity across a week-long investigation\n")

    store, world = Store(), World(bank_reply_day=3)
    task = "DISPUTE-91145"

    print("Each session below is a FRESH instance holding no prior context;")
    print("continuity comes entirely from the durable store.\n")

    r1 = run_session(store, world, task, day=1)   # Mon
    print(f"  day 1 (Mon): {r1:8}  plan={_plan(store, task)}")
    r2 = run_session(store, world, task, day=2)   # Tue - bank still silent
    print(f"  day 2 (Tue): {r2:8}  plan={_plan(store, task)}")
    r3 = run_session(store, world, task, day=4)   # Thu - bank has replied
    print(f"  day 4 (Thu): {r3:8}  plan={_plan(store, task)}")
    r4 = run_session(store, world, task, day=6)   # Sat - finish
    print(f"  day 6 (Sat): {r4:8}  plan={_plan(store, task)}")
    receipt = store.load(task)["receipt"]
    print(f"\n  completed: receipt={receipt}, bank submit calls={world.submit_calls}")

    # --- the fresh-instance test, run as a literal crash-and-resume -------- #
    print("\nFresh-instance / idempotency test: crash after the side effect but")
    print("before recording it, then resume from a brand-new instance.\n")
    store2, world2 = Store(), World(bank_reply_day=1)
    task2 = "DISPUTE-CRASH"
    run_session(store2, world2, task2, day=0)       # establish; waits at the bank
    try:
        # This session reaches submit_and_record, submits, then dies before the
        # step is recorded as done — the worst-case gap.
        run_session(store2, world2, task2, day=2, crash_before_recording=True)
    except SessionCrash as c:
        print(f"  crashed: {c}")
        print(f"           submit step still 'open' in the store; "
              f"bank submit calls so far: {world2.submit_calls}")
    # A stranger resumes with only the store — it will call submit AGAIN, because
    # the crash left the step unrecorded. Idempotency makes that replay safe.
    result = run_session(store2, world2, task2, day=2)
    submissions = len(world2.submissions)
    print(f"  resumed by fresh instance: {result}  "
          f"receipt={store2.load(task2)['receipt']}")
    print(f"           bank submit CALLS={world2.submit_calls} (crash + replay), "
          f"actual SUBMISSIONS={submissions} (idempotent: not doubled)")


def _plan(store: Store, task: str) -> str:
    return " ".join(f"{s['id']}:{s['status'][:4]}" for s in store.load(task)["plan"])


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
