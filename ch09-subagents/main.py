#!/usr/bin/env python3
"""
Context isolation and sub-agents — companion code for Chapter 9,
"Context Isolation and Sub-Agents."

Demonstrates the chapter's central claim: the triage->resolution contamination
bug is fixed *structurally* by isolation, not by better prompting. Two runs of
the same Northwind contact:

  * SHARED context (the single-agent baseline): triage deliberates at length -
    including a page of "maybe it's a shipping problem" musing - before concluding
    "billing." All of that reasoning stays in the one window the resolution step
    then reads, and the resolution agent latches onto the most prominent signal
    in its context (shipping) and opens on a delay the customer never mentioned.
    Contaminated.

  * ISOLATED sub-agents: triage runs in its own context and returns a small
    structured TriageResult; only the CONCLUSION (category=billing) crosses the
    boundary. The resolution agent starts from a clean window holding just that,
    and opens on billing. Uncontaminated - and its context is a fraction of the
    size.

Everything is deterministic and stdlib-only, so it verifies offline. The
sub-agents here are mocks whose behaviour is a function of their context
contents - which is exactly the point: contamination is caused by what's in the
window, and isolation controls what's in the window.

    python main.py            # or --demo
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


TOPICS = ("billing", "shipping", "warranty", "returns")


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# --------------------------------------------------------------------------- #
# Structured messages that cross agent boundaries (Ch. 8's field-naming
# discipline, applied to inter-agent handoff). The transcript never crosses;
# these objects do.
# --------------------------------------------------------------------------- #
@dataclass
class TaskSpec:
    goal: str
    inputs: dict
    tools: tuple[str, ...]


@dataclass
class TriageResult:
    category: str            # billing | shipping | warranty | returns
    route: str
    confidence: float
    note: str


@dataclass
class Contact:
    customer_id: str
    first_message: str


# --------------------------------------------------------------------------- #
# The triage sub-agent. It deliberates - heavily discussing shipping before
# concluding billing - and that deliberation is what pollutes a shared context.
# The structured TriageResult is the only thing meant to leave.
# --------------------------------------------------------------------------- #
def triage(spec: TaskSpec) -> tuple[str, TriageResult]:
    msg = spec.inputs["opening_message"]
    # The page of reasoning (note how many times it says "shipping"/"delay"):
    deliberation = (
        "Let me classify this contact. The customer mentions a delay, which "
        "could indicate a fulfilment or shipping issue - shipping problems often "
        "present as delays, and a delayed shipment would route to shipping. "
        "But the phrase 'charged twice' points to billing. It's possible the "
        "shipping delay and the charge are related, e.g. a re-ship triggered a "
        "second charge, which would still be a shipping-driven billing artifact. "
        "Weighing it: the concrete, actionable signal is the duplicate charge. "
        "Despite the shipping/delay language, this is a billing case."
    )
    result = TriageResult(
        category="billing",
        route="resolution",
        confidence=0.9,
        note="duplicate-charge suspected on NW-4820193; customer frustrated",
    )
    return deliberation, result


# --------------------------------------------------------------------------- #
# The resolution agent opens on whatever topic is most salient IN ITS CONTEXT.
# This is the mechanism of mid-context contamination: a long deliberation that
# keeps saying "shipping" makes shipping the most salient token, even though the
# concluded category is billing.
# --------------------------------------------------------------------------- #
def resolution_open_topic(context_texts: list[str]) -> str:
    blob = " ".join(context_texts).lower()
    salience = {t: blob.count(t) for t in TOPICS}
    # "delay" reinforces shipping, the way it would pull a model's attention.
    salience["shipping"] += blob.count("delay")
    return max(TOPICS, key=lambda t: salience[t])


# --------------------------------------------------------------------------- #
# Two orchestrations of the same contact.
# --------------------------------------------------------------------------- #
def run_shared(contact: Contact) -> dict:
    """Single agent, one shared context: triage reasoning bleeds into resolution."""
    spec = TaskSpec("Classify then resolve.",
                    {"opening_message": contact.first_message,
                     "customer_id": contact.customer_id},
                    ("lookup_customer", "lookup_order", "issue_refund"))
    deliberation, result = triage(spec)
    # Everything stays in ONE context the resolution step then reads:
    context = [contact.first_message, deliberation,
               f"conclusion: {result.category}"]
    topic = resolution_open_topic(context)
    return {"mode": "shared", "opened_on": topic,
            "context_tokens": sum(approx_tokens(t) for t in context),
            "contaminated": topic != result.category,
            "concluded": result.category}


def run_isolated(contact: Contact) -> dict:
    """Sub-agents: triage runs in its own context; only the conclusion crosses."""
    triage_spec = TaskSpec("Classify this contact and route it.",
                           {"opening_message": contact.first_message,
                            "customer_id": contact.customer_id},
                           ("lookup_customer", "lookup_order"))  # read-only
    deliberation, result = triage(triage_spec)   # deliberation dies here
    _ = deliberation

    # The resolution agent's context starts CLEAN and holds only the structured
    # conclusion - not the transcript, not the deliberation.
    resolution_context = [f"category: {result.category}", f"note: {result.note}"]
    topic = resolution_open_topic(resolution_context)
    return {"mode": "isolated", "opened_on": topic,
            "context_tokens": sum(approx_tokens(t) for t in resolution_context),
            "contaminated": topic != result.category,
            "concluded": result.category}


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def run_demo() -> None:
    contact = Contact(
        customer_id="C-4471",
        first_message=("My replacement is delayed and I think I was charged "
                       "twice for order NW-4820193."))

    print("Chapter 9 - context isolation and sub-agents\n")
    print("Same contact, two orchestrations. Triage concludes 'billing' in both;")
    print("the question is what the RESOLUTION agent opens on.\n")

    for run in (run_shared(contact), run_isolated(contact)):
        flag = "CONTAMINATED" if run["contaminated"] else "clean"
        print(f"  {run['mode']:>8} context: resolution opened on "
              f"'{run['opened_on']}' (triage concluded '{run['concluded']}')  "
              f"-> {flag}")
        print(f"           resolution context size: {run['context_tokens']} tokens")

    print("\n  Shared context: the page of shipping deliberation is the most")
    print("  salient thing in the window, so resolution opens on a shipping delay")
    print("  the customer's issue isn't about. Isolated: only 'billing' crosses,")
    print("  the resolution window is tiny, and the misrouting can't happen.")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
