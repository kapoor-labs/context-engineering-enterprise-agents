#!/usr/bin/env python3
"""
The Northwind flow on Microsoft Agent Framework — companion code for Chapter 10.

Microsoft Agent Framework is the convergence of Semantic Kernel + AutoGen (SK is
NOT deprecated — it is the enterprise orchestration layer inside the unified
framework). Its Python SDK runs the same triage -> resolution -> approval -> QA
graph the sibling `minimal-orchestrator/` builds from scratch — but on a real,
maintained engine with real model calls, and (typically) a managed runtime such
as Foundry Agent Service underneath.

This file is split in two, deliberately:

  * `describe_mapping()` RUNS offline (stdlib only): it prints how the Northwind
    flow maps onto Agent Framework's orchestration patterns, so the folder
    verifies in a clean environment with no SDK and no endpoint.

  * `ILLUSTRATIVE_AGENT_FRAMEWORK_CODE` is an explicitly-labelled SKETCH of the
    real SDK wiring. It is NOT executed here and is NOT guaranteed to match the
    current package API — Agent Framework is the fastest-moving naming area in
    the book. Treat it as a shape to adapt, and verify class/method names against
    the installed `agent-framework` package (see README) before relying on it.

    python agent_framework_flow.py       # prints the mapping (offline)
"""

from __future__ import annotations


# --------------------------------------------------------------------------- #
# Runnable, offline: the concept-to-framework mapping.
# --------------------------------------------------------------------------- #
def describe_mapping() -> None:
    print("Northwind flow on Microsoft Agent Framework (SK + AutoGen, unified)\n")

    print("Agents (each isolated, Ch. 9), carried on the workflow's edges:")
    for name, role, kind in [
        ("triage",     "classify + route",              "generative"),
        ("resolution", "handle the case, propose refund", "generative"),
        ("approval",   "human confirms refund",         "deterministic"),
        ("qa",         "sample + check against policy",  "generative verdict / deterministic sample"),
    ]:
        print(f"  - {name:11} [{kind:>42}]  {role}")

    print("\nOrchestration patterns used:")
    print("  - handoff   : triage routes -> resolution (>=0.6 conf) | human_review")
    print("  - sequential: resolution -> approval -> qa")
    print("  - handoff   : qa -> done (pass) | back to resolution (fail, w/ objection)")

    print("\nWhat the framework owns (so a script doesn't accrete it):")
    print("  - durable workflow STATE (TriageResult/ResolutionResult carried on edges)")
    print("  - CHECKPOINT after each agent -> resume, not restart, on failure")
    print("  - per-edge RETRY policy (transient vs terminal)")
    print("  - approval as a first-class awaiting-input STATE (timeout + escalation + audit)")
    print("  - OBSERVABILITY hooks feeding the end-to-end dashboard (Ch. 14)")

    print("\nStructured handoffs (Ch. 9 canon) cross the edges - conclusions, not")
    print("transcripts - so isolation survives orchestration.")


# --------------------------------------------------------------------------- #
# ILLUSTRATIVE ONLY — not executed, not guaranteed against the current SDK.
# Verify names against the installed `agent-framework` package before use.
# --------------------------------------------------------------------------- #
ILLUSTRATIVE_AGENT_FRAMEWORK_CODE = r'''
# --- SKETCH: the same graph on Microsoft Agent Framework (Python). ----------
# Names are illustrative; confirm against the current `agent-framework` SDK.
from agent_framework import ChatAgent, Workflow, HandoffPattern, SequentialPattern
from agent_framework.azure import AzureAIAgentClient   # Foundry Agent Service runtime

client = AzureAIAgentClient(endpoint=..., credential=...)

triage      = ChatAgent(client, name="triage",      instructions=TRIAGE_PROMPT,
                        tools=[lookup_customer, lookup_order])        # read-only (Ch. 7)
resolution  = ChatAgent(client, name="resolution",  instructions=RESOLUTION_PROMPT,
                        tools=RESOLUTION_TOOLS)                       # scoped OrderCore
qa          = ChatAgent(client, name="qa",          instructions=QA_PROMPT)

wf = Workflow()
# handoff: triage decides the next hop from its structured result
wf.add(HandoffPattern(source=triage,
                      route=lambda r: "human_review" if r.confidence < 0.6 else "resolution"))
# sequential spine with a first-class human approval gate before the refund executes
wf.add(SequentialPattern([resolution, approval_gate(timeout="4h", escalate_to="lead_queue"),
                          qa]))
# qa routes back to resolution on a policy fail, forward on a pass
wf.add(HandoffPattern(source=qa,
                      route=lambda r: None if r.verdict == "pass" else "resolution"))

result = wf.run(contact)   # framework owns state, checkpointing, retries, tracing
# ---------------------------------------------------------------------------
'''


def main() -> None:
    describe_mapping()
    print("\n(See ILLUSTRATIVE_AGENT_FRAMEWORK_CODE in this file for the real-SDK "
          "shape - labelled illustrative, verify against the current package.)")


if __name__ == "__main__":
    main()
