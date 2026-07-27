#!/usr/bin/env python3
"""
Evaluating context quality — companion code for Chapter 14, "Evaluating and
Observing Context Quality."

Three of the chapter's instruments, made runnable and offline:

  1. THE FAILURE-CLASSIFICATION RUBRIC as code: given a few signals, route a
     failure to model / context / tool / orchestration. Walking the book's four
     prior failures through it lands all four in "context" — the chapter's thesis
     that context failure is the dominant mode and masquerades as model failure.

  2. A RETRIEVAL GOLDEN-SET eval with the chapter's payoff scenario: a golden
     query set passes against the current corpus, then someone edits a policy
     article badly, and the eval FAILS on that change — catching the Chapter 1
     failure class (a wrong return-window answer) before a customer ever sees it.

  3. A COMPACTION PROBE eval (Chapter 8's methodology, now a standing regression):
     score a compaction by the fraction of task-critical probes its output still
     answers; a naive compactor regresses, a field-naming one holds.

Everything is deterministic and stdlib-only, so it verifies offline.

    python main.py            # or --demo
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# 1. The failure-classification rubric as code.
# --------------------------------------------------------------------------- #
@dataclass
class FailureSignals:
    needed_context_present_and_correct: bool   # was the right context in the window?
    tool_errored_or_wrong: bool                # did a tool fail / return wrong data?
    handoff_dropped_state: bool                # did coordination lose something?
    reproduces_with_correct_context: bool      # same error even given correct context?


def classify_failure(s: FailureSignals) -> str:
    """Ask the rubric's questions in order; return the failure class. Order
    matters: rule out tool/orchestration/context before blaming the model."""
    if s.tool_errored_or_wrong:
        return "tool"
    if s.handoff_dropped_state:
        return "orchestration"
    if not s.needed_context_present_and_correct:
        return "context"
    if s.reproduces_with_correct_context:
        return "model"          # correct context, still wrong -> genuinely the model
    return "context"            # default: the context was the variable


# The book's four prior failures, as signals. All should classify as "context".
BOOK_FAILURES = {
    "Ch1 wrong policy (no retrieval)": FailureSignals(False, False, False, False),
    "Ch5 stale chunk retrieved":       FailureSignals(False, False, False, False),
    "Ch8 hour-three amnesia":          FailureSignals(False, False, False, False),
    "Ch12 attachment injection":       FailureSignals(False, False, False, False),
}


# --------------------------------------------------------------------------- #
# 2. Retrieval golden-set eval + the bad-policy-edit regression scenario.
# --------------------------------------------------------------------------- #
@dataclass
class Article:
    text: str
    validation_status: str      # current | archived


@dataclass
class GoldenCase:
    query: str
    must_retrieve: str
    must_not_retrieve: str
    expected_contains: str


def build_corpus() -> dict[str, Article]:
    return {
        "standard-returns": Article("Returns accepted within 30 days of delivery.",
                                    "current"),
        "returns-archive-2019": Article("Returns accepted within 45 days.",
                                        "archived"),   # the Ch. 5 trap
    }


def retrieve(query: str, corpus: dict[str, Article]) -> list[tuple[str, str]]:
    """Naive retriever: keyword match, current articles only (freshness filter)."""
    q = query.lower()
    hits = []
    for art_id, art in corpus.items():
        if art.validation_status != "current":
            continue                                   # freshness (Ch. 5/13)
        if "return" in q and "return" in art.text.lower():
            hits.append((art_id, art.text))
    return hits


GOLDEN_SET = [
    GoldenCase(
        query="What's the return window for a delayed electronics order?",
        must_retrieve="standard-returns",
        must_not_retrieve="returns-archive-2019",
        expected_contains="30 days"),
]


def retrieval_eval(cases: list[GoldenCase],
                   corpus: dict[str, Article]) -> tuple[float, list[str]]:
    passed, failures = 0, []
    for c in cases:
        hits = retrieve(c.query, corpus)
        hit_ids = [h[0] for h in hits]
        hit_text = " ".join(h[1] for h in hits)
        ok = (c.must_retrieve in hit_ids
              and c.must_not_retrieve not in hit_ids
              and c.expected_contains in hit_text)
        if ok:
            passed += 1
        else:
            failures.append(c.query)
    return passed / len(cases), failures


# --------------------------------------------------------------------------- #
# 3. Compaction probe eval (Chapter 8's methodology as a standing regression).
# --------------------------------------------------------------------------- #
@dataclass
class Probe:
    question: str
    expected: object
    answer_from: str            # which state field answers it


GROUND_TRUTH = {"order_id": "NW-4820193", "commitment": "$129.99 reversed"}
PROBES = [
    Probe("order id?", "NW-4820193", "order_id"),
    Probe("what was promised?", "$129.99 reversed", "commitment"),
]


def field_compactor(truth: dict) -> dict:
    return dict(truth)                          # keeps every task-critical field


def naive_compactor(truth: dict) -> dict:
    return {"order_id": truth["order_id"]}      # smooths away the commitment


def compaction_probe_eval(compactor, probes: list[Probe]) -> float:
    compacted = compactor(GROUND_TRUTH)
    passed = sum(1 for p in probes if compacted.get(p.answer_from) == p.expected)
    return passed / len(probes)


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def run_demo() -> None:
    print("Chapter 14 - evaluating context quality\n")

    print("1. The failure-classification rubric (the book's four failures):")
    for label, sig in BOOK_FAILURES.items():
        print(f"   {label:34} -> {classify_failure(sig)}")
    print("   ...and the other two columns, for contrast:")
    print(f"   {'tool returned a stale record':34} -> "
          f"{classify_failure(FailureSignals(True, True, False, False))}")
    print(f"   {'handoff dropped the case ID':34} -> "
          f"{classify_failure(FailureSignals(True, False, True, False))}")
    print(f"   {'wrong even with correct context':34} -> "
          f"{classify_failure(FailureSignals(True, False, False, True))}")

    print("\n2. Retrieval golden set (the payoff scenario):")
    corpus = build_corpus()
    score, fails = retrieval_eval(GOLDEN_SET, corpus)
    print(f"   baseline: {score:.0%} pass")
    # Someone edits the current policy article badly, garbling the window.
    corpus["standard-returns"] = Article("Returns accepted within 3 dys.", "current")
    score2, fails2 = retrieval_eval(GOLDEN_SET, corpus)
    print(f"   after a bad policy-article edit: {score2:.0%} pass  "
          f"(FAILED: {fails2})")
    print("   -> the Ch. 1 failure class, caught by a regression before it ships.")

    print("\n3. Compaction probe eval (Ch. 8 methodology as a regression):")
    print(f"   naive prose compactor:  {compaction_probe_eval(naive_compactor, PROBES):.0%} "
          "of probes survive")
    print(f"   field-naming compactor: {compaction_probe_eval(field_compactor, PROBES):.0%} "
          "of probes survive")

    print("\n   Each instrument turns 'it seems fine' into a number that regresses.")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
