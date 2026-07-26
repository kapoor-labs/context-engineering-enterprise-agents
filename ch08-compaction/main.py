#!/usr/bin/env python3
"""
Compaction, tool-result clearing, and probe-question testing — companion code
for Chapter 8, "Compaction, Summarization, and Context Clearing."

Runs a simulated multi-hour Northwind customer-service session (the "tree-strand"
case: warranty -> shipping -> billing), then demonstrates the chapter's three
ideas, all offline with only the standard library:

  1. TOOL-RESULT CLEARING is where the tokens actually are. We show that the raw
     tool payloads dwarf the conversation, and that clearing them (with re-callable
     pointers) reclaims most of the window.
  2. COMPACTION distills the session into a small, structured CaseState — not prose.
  3. PROBE-QUESTION TESTING measures what a compaction dropped. We compact the same
     session two ways — a naive "summarize into prose" compactor and the chapter's
     field-naming compactor — and score each against a fixed probe set. The naive
     one leaks commitments and amounts; the field one preserves them. The score is
     the difference between "the summary looks good" and a number you can gate on.

The compactors here are DETERMINISTIC SIMULATIONS of what an LLM would do, so the
demo verifies offline. A production pipeline would call a model with the
field-naming COMPACTION_PROMPT and parse the structured result; the trigger logic,
the CaseState shape, the tool-result clearing, and the probe test are the parts
that carry over unchanged.

    python main.py            # or --demo
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Callable, TypedDict


# --------------------------------------------------------------------------- #
# The structured state a compaction must carry forward. Six fields, each
# independently checkable — the whole point of compacting into state, not prose.
# --------------------------------------------------------------------------- #
class CaseState(TypedDict):
    order_ids: list[str]
    case_id: str | None
    commitments: list[str]
    decisions: list[str]
    open_items: list[str]
    flags: list[str]


def empty_state() -> CaseState:
    return {"order_ids": [], "case_id": None, "commitments": [],
            "decisions": [], "open_items": [], "flags": []}


def state_tokens(state: CaseState) -> int:
    return approx_tokens(str(state))


# --------------------------------------------------------------------------- #
# Session model: a raw transcript plus tool results plus a structured event log.
# Real agents don't hand you a clean event log — the compactor's job is to
# recover state from the messy context. Here the log stands in for "what actually
# happened," so both compactors have the same source material and the only
# difference is what each chooses to preserve.
# --------------------------------------------------------------------------- #
def approx_tokens(text: str) -> int:
    # Rough, deterministic stand-in for a tokenizer: ~4 chars/token.
    return max(1, len(text) // 4)


@dataclass
class Message:
    role: str
    text: str

    @property
    def tokens(self) -> int:
        return approx_tokens(self.text)


@dataclass
class ToolResult:
    tool: str
    order_id: str
    tokens: int          # full serialized payload size
    used: bool = True    # still live in context?
    cleared_note: str = ""

    def context_tokens(self) -> int:
        # A cleared result costs only its one-line pointer, not the payload.
        return approx_tokens(self.cleared_note) if not self.used else self.tokens


@dataclass
class Event:
    kind: str            # identifier | commitment | decision | open_item | flag
    value: str


@dataclass
class Session:
    messages: list[Message] = field(default_factory=list)
    tools: list[ToolResult] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    def conversation_tokens(self) -> int:
        return sum(m.tokens for m in self.messages)

    def tool_tokens(self) -> int:
        return sum(t.context_tokens() for t in self.tools)

    def total_tokens(self) -> int:
        return self.conversation_tokens() + self.tool_tokens()

    # -- tool-result clearing --------------------------------------------- #
    def clear_tool_results(self, keep_pointers: bool = True) -> int:
        reclaimed = 0
        for t in self.tools:
            if t.used:
                before = t.context_tokens()
                t.used = False
                t.cleared_note = (
                    f"[{t.tool} result for {t.order_id} cleared; re-call to refetch]"
                    if keep_pointers else "")
                reclaimed += before - t.context_tokens()
        return reclaimed


# --------------------------------------------------------------------------- #
# The scenario: the tree-strand case, three phases, each adding dialogue, a
# couple of chunky tool results, and the structured facts that occurred.
# --------------------------------------------------------------------------- #
def build_tree_strand_session() -> Session:
    s = Session()

    def dialogue(*turns: tuple[str, str]) -> None:
        for role, text in turns:
            s.messages.append(Message(role, text))

    def tool(name: str, order_id: str, tokens: int) -> None:
        s.tools.append(ToolResult(name, order_id, tokens))

    def record(kind: str, value: str) -> None:
        s.events.append(Event(kind, value))

    # Realistic multi-sentence turns, so the conversation is a believable
    # fraction of the window (~1/8, matching the chapter) rather than a toy line.
    # -- Phase 1: warranty ------------------------------------------------- #
    dialogue(
        ("customer",
         "Hi, my pre-lit Christmas tree arrived today and one whole strand of "
         "lights is completely dead out of the box - none of them turn on. The "
         "order number is NW-4820193. This was supposed to be the centerpiece "
         "for a party this weekend so I'm pretty frustrated it arrived broken."),
        ("agent",
         "I'm really sorry the tree arrived with a faulty light strand, that's "
         "clearly not the experience you were expecting. Let me pull up order "
         "NW-4820193 and check the warranty and return eligibility for you now."),
        ("agent",
         "Thanks for your patience. I've reviewed the order and the product "
         "warranty. Because this is a defect present on arrival and you're well "
         "within the window, you're covered - I can approve a free replacement "
         "at no charge to you."))
    tool("lookup_order", "NW-4820193", 1500)
    tool("retrieve_policy", "NW-4820193", 500)
    record("identifier", "NW-4820193")
    record("identifier", "case:CS-77120")
    record("decision", "warranty applies (defect on arrival, within window)")
    record("commitment", "replacement approved at no charge (order NW-4820193)")

    # -- Phase 2: shipping ------------------------------------------------- #
    dialogue(
        ("customer",
         "Thank you, that's a relief. The problem is I really need the "
         "replacement before the 24th, otherwise it's useless for the holiday. "
         "Is there any way to get it here in time?"),
        ("agent",
         "Completely understand - the holiday deadline matters. Let me check "
         "fulfilment options and request an expedited shipment on the "
         "replacement so we can try to beat the 24th."),
        ("agent",
         "I've submitted the replacement order and requested an expedite on it. "
         "Shipping will confirm the delivery estimate; I've flagged this as "
         "time-sensitive so it's prioritized."))
    tool("check_fulfilment", "NW-4820193", 800)
    tool("issue_replacement", "NW-4820193", 600)
    record("commitment", "replacement expedited (requested)")
    record("open_item", "will replacement arrive before 24 Dec? - shipping owns")
    record("flag", "time-sensitive: holiday deadline")

    # -- Phase 3: billing -------------------------------------------------- #
    dialogue(
        ("customer",
         "One more thing while I have you - I was just looking at my card "
         "statement and I think I was actually charged twice for the original "
         "tree. Can you check that? I've already been transferred three times "
         "today and I just want it sorted."),
        ("agent",
         "I'm sorry about the repeated transfers, I'll take care of this now so "
         "you don't have to be moved again. Let me pull the billing history for "
         "the order and check for a duplicate charge."),
        ("agent",
         "You're right - there's a duplicate charge of $129.99 on this order. "
         "I've reversed it and you'll see the refund back on your card. You're "
         "all set on the billing side."))
    tool("lookup_order", "NW-4820193", 1500)
    tool("retrieve_policy", "NW-4820193", 500)
    record("decision", "duplicate charge confirmed ($129.99)")
    record("commitment", "duplicate charge of $129.99 reversed")
    record("flag", "transferred 3x; frustrated")

    return s


# --------------------------------------------------------------------------- #
# Compactors. Both read the same event log; they differ in what they preserve —
# a faithful stand-in for the difference between a generic "summarize this"
# prompt and the chapter's field-naming compaction prompt.
# --------------------------------------------------------------------------- #
class FieldCompactor:
    """The chapter's approach: extract every task-critical field, verbatim."""

    name = "field-naming"

    def extract(self, session: Session) -> CaseState:
        st = empty_state()
        for e in session.events:
            if e.kind == "identifier":
                if e.value.startswith("case:"):
                    st["case_id"] = e.value.split(":", 1)[1]
                else:
                    st["order_ids"].append(e.value)
            elif e.kind == "commitment":
                st["commitments"].append(e.value)
            elif e.kind == "decision":
                st["decisions"].append(e.value)
            elif e.kind == "open_item":
                st["open_items"].append(e.value)
            elif e.kind == "flag":
                st["flags"].append(e.value)
        return st


class NaiveCompactor:
    """
    A generic 'summarize into a readable narrative' compactor. Simulated failure
    mode (the one the chapter warns about): it captures identifiers and decisions
    but smooths commitments and drops the exact amounts — the fluent-but-useless
    summary. This is the deterministic model of a real prose-summary regression.
    """

    name = "naive prose"

    def extract(self, session: Session) -> CaseState:
        st = empty_state()
        for e in session.events:
            if e.kind == "identifier":
                if e.value.startswith("case:"):
                    st["case_id"] = e.value.split(":", 1)[1]
                else:
                    st["order_ids"].append(e.value)
            elif e.kind == "decision":
                # amounts smoothed out of the narrative
                st["decisions"].append(e.value.split("(")[0].strip())
            elif e.kind == "flag":
                st["flags"].append(e.value)
            # commitments and open_items: lost in the prose
        return st


# --------------------------------------------------------------------------- #
# Probe questions: what task-critical MEANS for this workload, as testable
# queries. Each returns an answer from a CaseState; we score against ground truth.
# --------------------------------------------------------------------------- #
@dataclass
class Probe:
    question: str
    answer: Callable[[CaseState], object]
    expected: object


def probe_set() -> list[Probe]:
    return [
        Probe("What order IDs are in play?",
              lambda s: sorted(s["order_ids"]), ["NW-4820193"]),
        Probe("What is the case ID?",
              lambda s: s["case_id"], "CS-77120"),
        Probe("Was a no-charge replacement promised?",
              lambda s: any("replacement" in c and "no charge" in c
                            for c in s["commitments"]), True),
        Probe("Was a refund/reversal promised, and for how much?",
              lambda s: any("$129.99" in c for c in s["commitments"]), True),
        Probe("Is there an open item with an owner?",
              lambda s: len(s["open_items"]) > 0, True),
        Probe("Is there a handling flag the agent must know?",
              lambda s: any("frustrated" in f for f in s["flags"]), True),
    ]


def score(state: CaseState, probes: list[Probe]) -> tuple[int, list[str]]:
    passed, failures = 0, []
    for p in probes:
        if p.answer(state) == p.expected:
            passed += 1
        else:
            failures.append(p.question)
    return passed, failures


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def run_demo() -> None:
    print("Chapter 8 - compaction, tool-result clearing, and probe testing\n")

    session = build_tree_strand_session()
    conv = session.conversation_tokens()
    tools = session.tool_tokens()
    print("1. The real bloat is tool results, not conversation:")
    print(f"   conversation: {conv:>6} tokens")
    print(f"   tool results: {tools:>6} tokens   "
          f"({tools / (conv + tools):.0%} of the window)")

    before = session.total_tokens()
    reclaimed = session.clear_tool_results(keep_pointers=True)
    after_clear = session.total_tokens()
    print("\n2. Tool-result clearing (clear-after-use, keep pointers):")
    print(f"   before: {before} tokens  ->  after: {after_clear} tokens  "
          f"(reclaimed {reclaimed})")

    probes = probe_set()
    print("\n3. Compact into structured state, then PROBE it. Same session,")
    print("   two compactors, one fixed probe set:\n")
    for compactor in (NaiveCompactor(), FieldCompactor()):
        st = compactor.extract(session)
        passed, failures = score(st, probes)
        pct = passed / len(probes)
        print(f"   {compactor.name:>12} compactor: {passed}/{len(probes)} "
              f"probes pass ({pct:.0%})  state={state_tokens(st)} tokens")
        for q in failures:
            print(f"                 FAILED: {q}")
        print()

    print("   The naive compactor reads fine and silently drops the commitments")
    print("   and the $129.99 - exactly the failure a probe set catches and a")
    print("   'looks good' review does not.")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
