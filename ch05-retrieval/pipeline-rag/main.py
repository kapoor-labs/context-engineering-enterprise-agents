"""Pipeline RAG — companion code for Chapter 5, "Retrieval Architectures".

The baseline pattern: chunk -> embed -> top-k -> generate. This demo reproduces
the chapter's 2019-policy incident (a naive "index everything" corpus retrieves
a stale, superseded policy with full confidence), then applies the two fixes the
chapter prescribes: an editorial gate on what enters the index, and metadata
carried on every chunk.

Self-contained by design: the "embedding" is a bag-of-words vector and the
"generate" step prints the assembled context instead of calling a model, so the
retrieval behavior — the point of the chapter — is observable without API keys.
The pipeline shape (index, embed, top_k, assemble) is the same one you'd keep
when swapping in a real embedding model and a real model call via .env.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Toy embedding: bag-of-words + cosine similarity. Stands in for a real
# embedding model; the failure it demonstrates (similarity is not authority)
# is a property of similarity search itself, not of this simplification.
# --------------------------------------------------------------------------

def embed(text: str) -> Counter:
    return Counter(re.findall(r"[a-z0-9']+", text.lower()))


def cosine(a: Counter, b: Counter) -> float:
    dot = sum(a[t] * b[t] for t in a)
    norm = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return dot / norm if norm else 0.0


@dataclass(frozen=True)
class Doc:
    title: str
    status: str          # "current" | "archived" | "draft"
    effective: str
    owner: str
    text: str


# One SharePoint library, a decade of sediment: current policy, dead policy,
# and an FAQ, all deposited in the same place.
LIBRARY = [
    Doc(
        title="Returns and Refunds Policy — FINAL v3",
        status="archived", effective="2019-03-01", owner="(unowned)",
        text=(
            "How long do you have to return an item? You have 45 days from "
            "delivery to send back any item, including coffee makers, grinders, "
            "and other small kitchen electronics. Just start a return and we "
            "will email you a label."
        ),
    ),
    Doc(
        title="Returns and Refunds Policy",
        status="current", effective="2026-02-01", owner="policy-team",
        text=(
            "You may return standard merchandise within 30 days of delivery. "
            "To start a return, use the returns portal. Small kitchen "
            "electronics, including coffee makers and grinders, must be "
            "unopened unless defective. Seasonal and category-specific windows "
            "are listed in the category appendix of this policy."
        ),
    ),
    Doc(
        title="Shipping Delays FAQ",
        status="current", effective="2025-11-10", owner="logistics-team",
        text=(
            "If your order is delayed, you will receive an updated delivery "
            "estimate by email. Delays do not require any action from you."
        ),
    ),
]


def build_index(docs: list[Doc], with_metadata: bool) -> list[tuple[str, Counter]]:
    """Chunk (one chunk per doc at this corpus size) and embed.

    with_metadata=False is the naive pipeline: the chunk is bare text, exactly
    what a length-based splitter that dropped the headings would produce.
    """
    chunks = []
    for doc in docs:
        header = f"[{doc.title} | status: {doc.status} | effective: {doc.effective}]\n"
        chunk = (header + doc.text) if with_metadata else doc.text
        chunks.append((chunk, embed(doc.text)))  # similarity is over text either way
    return chunks


def top_k(index: list[tuple[str, Counter]], query: str, k: int = 2) -> list[tuple[float, str]]:
    q = embed(query)
    scored = sorted(((cosine(q, vec), chunk) for chunk, vec in index), reverse=True)
    return scored[:k]


def run(label: str, docs: list[Doc], with_metadata: bool, query: str) -> None:
    print(f"\n=== {label} ===")
    print(f"query: {query!r}")
    for score, chunk in top_k(build_index(docs, with_metadata), query):
        print(f"\n  score {score:.3f}:")
        for line in chunk.splitlines():
            print(f"    {line}")


def main() -> None:
    query = "How long do I have to return a coffee grinder?"

    # Naive pipeline: index everything, chunks without metadata. The 2019
    # policy wins the similarity contest — older, chattier prose resembles the
    # customer's phrasing better than the current policy's legal register, and
    # nothing in a vector encodes "superseded".
    run("Naive: index everything, no metadata (the 2019 incident)",
        LIBRARY, with_metadata=False, query=query)

    # The fix is editorial, not algorithmic: only current, owned documents
    # enter the index, and every chunk carries its provenance with it.
    curated = [d for d in LIBRARY if d.status == "current" and d.owner != "(unowned)"]
    run("Fixed: editorial gate (current docs only) + metadata on every chunk",
        curated, with_metadata=True, query=query)

    print(
        "\nIn production, the top chunks above are inserted into the model's "
        "context for generation.\nNote what changed between runs: not the "
        "similarity math — the corpus and the chunk contract."
    )


if __name__ == "__main__":
    main()
