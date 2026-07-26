"""Agentic RAG — companion code for Chapter 5, "Retrieval Architectures".

The plan -> retrieve -> critique -> re-retrieve loop, instrumented so you can
watch what each iteration adds. The chapter's composition question is used:
"Can I still return my delayed espresso machine?" — which no single retrieval
answers, because the answer is a join of a Tier 1 order record and a Tier 2
policy article.

Self-contained by design: the planner and critic here are deterministic
functions standing in for model calls, so the loop's *mechanics* — the part the
chapter teaches — run without API keys. In production, plan() and critique()
are where the model reasons; the loop structure, the evidence ledger, and the
sufficiency gate stay exactly as shown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

# --------------------------------------------------------------------------
# Sources: Tier 1 structured records, Tier 2 curated documents.
# --------------------------------------------------------------------------

ORDERS = {  # Tier 1: the system of record (Dataverse/OrderCore in the book)
    "88214": {
        "sku": "GR-2200 burr espresso machine",
        "sku_category": "small-kitchen-electronics",
        "ordered": date(2026, 6, 22),
        "promised_delivery": date(2026, 7, 3),
        "delivered": date(2026, 7, 14),  # 11 days late
        "opened": False,
    }
}

POLICY_ARTICLES = {  # Tier 2: curated, current, owned documents
    "returns-policy-core": (
        "Standard merchandise may be returned within 30 days of delivery. "
        "Small kitchen electronics must be unopened unless defective. "
        "Seasonal windows: see the Holiday Returns Addendum."
    ),
    "holiday-returns-addendum": (
        "Orders placed between November 1 and December 24 may be returned "
        "through January 31. Outside that window, no seasonal extension applies."
    ),
}


@dataclass
class Evidence:
    """The loop's ledger: everything retrieved so far, by source."""
    order: dict | None = None
    articles: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------
# The loop. plan() and critique() are deterministic stand-ins for model calls.
# --------------------------------------------------------------------------

def plan(question: str, evidence: Evidence) -> list[str]:
    needs = []
    if evidence.order is None:
        needs.append("order-record:88214")
    if "returns-policy-core" not in evidence.articles:
        needs.append("article:returns-policy-core")
    return needs


def retrieve(need: str, evidence: Evidence) -> str:
    kind, _, key = need.partition(":")
    if kind == "order-record":
        evidence.order = ORDERS[key]
        return f"Tier 1 lookup -> order {key} ({evidence.order['sku']})"
    evidence.articles[key] = POLICY_ARTICLES[key]
    return f"Tier 2 retrieval -> article '{key}'"


def critique(question: str, evidence: Evidence) -> list[str]:
    """Judge sufficiency; return further retrievable needs. Empty = answer.

    This is the step pipeline RAG structurally lacks: it can notice that the
    evidence *references* something it doesn't yet contain.
    """
    gaps = []
    for text in evidence.articles.values():
        if "Addendum" in text and "holiday-returns-addendum" not in evidence.articles:
            gaps.append("article:holiday-returns-addendum")  # cited but not in hand
    return gaps


def compose_answer(evidence: Evidence, today: date) -> str:
    order = evidence.order
    window_ends = order["delivered"] + timedelta(days=30)
    seasonal = date(2026, 11, 1) <= order["ordered"] <= date(2026, 12, 24)
    verdict = "OPEN" if today <= window_ends else "CLOSED"
    return (
        f"Window runs from delivery ({order['delivered']}), not order date "
        f"({order['ordered']}). 30-day window ends {window_ends} -> {verdict}. "
        f"Seasonal extension applies: {seasonal}. "
        f"Cited: order record 88214 (Tier 1); "
        f"{', '.join(evidence.articles)} (Tier 2)."
    )


def main() -> None:
    question = "Can I still return my delayed espresso machine? Order 88214."
    print(f"question: {question}\n")

    evidence = Evidence()
    for iteration in range(1, 5):
        needs = plan(question, evidence) or critique(question, evidence)
        print(f"--- iteration {iteration} ---")
        if not needs:
            print("critique: evidence sufficient — stop retrieving, answer.\n")
            break
        print(f"plan/critique produced needs: {needs}")
        for need in needs:
            print(f"  {retrieve(need, evidence)}")
        print()
    else:
        raise SystemExit("loop budget exhausted — escalate instead of guessing")

    print("answer:")
    # In the book's timeline "today" is the demo day; pinned so output is stable.
    print(f"  {compose_answer(evidence, today=date(2026, 7, 19))}")


if __name__ == "__main__":
    main()
