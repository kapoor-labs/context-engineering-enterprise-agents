#!/usr/bin/env python3
"""
A minimal orchestrator, built from scratch — companion code for Chapter 10,
"Orchestration Frameworks in Practice."

The chapter's argument is that a multi-agent workflow HAS state management,
checkpointing/resume, retry semantics, handoff routing, and a human-in-the-loop
approval gate whether you design them or let them accrete in a script. This is
the "build it yourself first" version: a tiny, stdlib-only workflow engine that
implements all five deliberately, so you can see exactly what a real framework
(Microsoft Agent Framework, LangGraph) provides — and why Priya's hand-rolled
script kept reinventing it, badly.

It runs the Northwind triage -> resolution -> approval -> QA flow and demonstrates:

  * HANDOFF ROUTING as declared edges (including QA-fail routing back to
    resolution with the specific objection).
  * DURABLE STATE + CHECKPOINTS so a mid-workflow failure resumes instead of
    restarting — and the refund is issued exactly once across an interruption.
  * RETRY semantics (a transient resolution failure retries and succeeds).
  * HUMAN-IN-THE-LOOP as a first-class `awaiting_approval` state with an audit
    record — not a prompt instruction.
  * The DETERMINISTIC/GENERATIVE split: judgment steps are generative, the
    promise steps (approval, refund execution) are deterministic and guaranteed.

Everything is deterministic and stdlib-only, so it verifies offline. The agents
are mocks; a production version runs the same graph on a real framework and real
model calls.

    python main.py            # or --demo
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Callable


class AwaitingApproval(Exception):
    """First-class pause: the workflow is durably waiting on a human decision."""
    def __init__(self, pending: dict):
        super().__init__("awaiting human approval")
        self.pending = pending


class WorkflowInterrupted(Exception):
    """A node exhausted its retries; the (checkpointed) state can be resumed."""
    def __init__(self, state: dict, at: str):
        super().__init__(f"interrupted at {at}")
        self.state = state
        self.at = at


class TransientError(Exception):
    """A retryable failure (e.g. a flaky OrderCore/model call)."""


@dataclass
class Node:
    name: str
    run: Callable[[dict], dict]        # returns state updates
    kind: str                          # "generative" | "deterministic"
    route: Callable[[dict], str | None]  # next node name, or None for done
    max_attempts: int = 1


class Workflow:
    def __init__(self, entry: str):
        self.entry = entry
        self.nodes: dict[str, Node] = {}

    def add(self, node: Node) -> None:
        self.nodes[node.name] = node

    def run(self, state: dict, fail: dict[str, int] | None = None) -> dict:
        """Drive the graph. `fail` injects N transient failures at a node."""
        fail = fail or {}
        state.setdefault("completed", set())
        state.setdefault("audit", [])
        state.setdefault("checkpoints", [])
        state.setdefault("refund_issued_count", 0)
        current = state.get("_next", self.entry)

        while current is not None:
            node = self.nodes[current]
            if current not in state["completed"]:
                for attempt in range(1, node.max_attempts + 1):
                    try:
                        if fail.get(current, 0) > 0:
                            fail[current] -= 1
                            raise TransientError(f"{current} transient failure")
                        updates = node.run(state)      # may raise AwaitingApproval
                        state.update(updates)
                        state["completed"].add(current)
                        state["checkpoints"].append(current)   # persist progress
                        break
                    except TransientError:
                        if attempt == node.max_attempts:
                            state["_next"] = current           # resume here
                            raise WorkflowInterrupted(state, current)
                        # else: retry
            nxt = node.route(state)                            # handoff routing
            state["_next"] = nxt
            current = nxt
        return state


# --------------------------------------------------------------------------- #
# The Northwind agents (mocks). Generative steps stand in for model judgment;
# deterministic steps are guaranteed transitions.
# --------------------------------------------------------------------------- #
def triage_run(state: dict) -> dict:
    return {"category": "billing", "confidence": 0.9}


def resolution_run(state: dict) -> dict:
    # Generative judgment: decide a refund is warranted, and address any QA
    # objection from a previous pass (the loop-back case).
    updates = {"refund_proposed": True, "amount": 129.99}
    if state.get("qa_objection") == "missing_disclosure":
        updates["disclosure_given"] = True     # fix the NAMED defect, not the world
    else:
        updates.setdefault("disclosure_given", state.get("disclosure_given", False))
    return updates


def approval_run(state: dict) -> dict:
    # Deterministic gate: pause until a human approves; then issue the refund
    # exactly once (idempotent via the `completed` set — resume never re-issues).
    if not state.get("approved"):
        raise AwaitingApproval({"amount": state["amount"], "order": "NW-4820193"})
    return {
        "refund_issued": True,
        "refund_issued_count": state["refund_issued_count"] + 1,
        "audit": state["audit"] + [
            f"refund ${state['amount']} approved by {state['approver']}"],
    }


def qa_run(state: dict) -> dict:
    # Generative judgment (did the case meet policy?) + deterministic check
    # (was the refund approved by an entitled role?). Records the verdict.
    disclosure_ok = state.get("disclosure_given", False)
    verdict = "pass" if disclosure_ok else "fail"
    objection = None if disclosure_ok else "missing_disclosure"
    return {"qa_verdict": verdict, "qa_objection": objection}


# -- routing (declared edges) ---------------------------------------------- #
def route_triage(state: dict) -> str:
    return "resolution" if state["confidence"] >= 0.6 else "human_review"


def route_resolution(state: dict) -> str:
    return "approval"


def route_approval(state: dict) -> str:
    return "qa"


def route_qa(state: dict) -> str | None:
    if state["qa_verdict"] == "pass":
        return None                                # done
    # QA fail: route BACK to resolution to fix the named objection. Clear only
    # the downstream nodes' completed-flags; approval stays done so the refund
    # is NOT re-issued on the second pass.
    state["completed"].discard("resolution")
    state["completed"].discard("qa")
    return "resolution"


def build_workflow() -> Workflow:
    wf = Workflow(entry="triage")
    wf.add(Node("triage", triage_run, "generative", route_triage))
    wf.add(Node("resolution", resolution_run, "generative", route_resolution,
                max_attempts=3))           # transient failures retry
    wf.add(Node("approval", approval_run, "deterministic", route_approval))
    wf.add(Node("qa", qa_run, "generative", route_qa))
    return wf


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def scenario_approval_and_resume() -> dict:
    """Approval pause + a transient resolution retry + a QA interruption/resume,
    proving the refund is issued exactly once across the interruption."""
    wf = build_workflow()
    state: dict = {"disclosure_given": True}     # this case is compliant
    # Inject: 1 transient failure at resolution (retries), 1 at QA (interrupts).
    fail = {"resolution": 1, "qa": 1}

    # Pass 1: pauses at approval (human hasn't approved yet).
    try:
        wf.run(state, fail)
    except AwaitingApproval as a:
        print(f"   paused: awaiting approval of ${a.pending['amount']} "
              f"on {a.pending['order']}")

    # Human approves out-of-band; resume.
    state["approved"] = True
    state["approver"] = "lead:ravi"
    try:
        wf.run(state, fail)                       # QA injection fires -> interrupt
    except WorkflowInterrupted as w:
        print(f"   interrupted at '{w.at}' (transient) - state checkpointed, "
              f"refund already issued: {state['refund_issued_count']}x")

    # Resume from checkpoint; QA now succeeds. Refund must NOT be re-issued.
    wf.run(state, fail)
    return state


def scenario_qa_fail_loops_back() -> dict:
    """QA finds a policy defect and routes the case back to resolution, which
    fixes the NAMED objection; the refund is not re-issued on the loop."""
    wf = build_workflow()
    state: dict = {"disclosure_given": False,     # non-compliant on first pass
                   "approved": True, "approver": "lead:ravi"}
    wf.run(state)
    return state


def run_demo() -> None:
    print("Chapter 10 - a minimal orchestrator (state, checkpoint, retry, "
          "routing, HITL)\n")

    print("1. Approval gate + retry + interruption/resume (idempotent refund):")
    s1 = scenario_approval_and_resume()
    print(f"   final: qa_verdict={s1['qa_verdict']}, "
          f"refund_issued_count={s1['refund_issued_count']} (exactly once)")
    print(f"   checkpoints: {s1['checkpoints']}")
    print(f"   audit: {s1['audit']}")

    print("\n2. QA policy-fail routes back to resolution (fix named defect, "
          "no double refund):")
    s2 = scenario_qa_fail_loops_back()
    print(f"   path retraced resolution->qa after fail; final verdict="
          f"{s2['qa_verdict']}, disclosure_given={s2['disclosure_given']}")
    print(f"   refund_issued_count={s2['refund_issued_count']} (exactly once)")
    print(f"   checkpoints: {s2['checkpoints']}")

    print("\n   None of this is special-case branching: it's declared edges,")
    print("   durable state, and per-node retry - the five things a framework")
    print("   gives you by design and a hand-rolled script accretes by accident.")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
