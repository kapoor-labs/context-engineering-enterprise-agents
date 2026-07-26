"""GraphRAG — companion code for Chapter 5, "Retrieval Architectures".

The chapter's recall question — "Which customers with open chargebacks bought
from the recalled batch?" — answered two ways on the same data:

  1. similarity search over prose renderings of the records (the wrong tool:
     no single passage contains the answer, so the top-k chunks can't either);
  2. traversal over an entity-relationship graph (the answer is a path:
     batch -> SKUs -> orders -> customers, intersected with chargeback status).

Self-contained by design: the graph is in-memory dicts and the "embedding" is
bag-of-words cosine, standing in for a graph store and an embedding model. The
structural point — passages vs. paths — is unchanged by the simplification.
Note the chapter's caveat: when entities already live in tables (as they do at
Northwind, in Dataverse/OrderCore), this traversal is a database join, and you
should route to the structured store rather than build a knowledge graph.
"""

from __future__ import annotations

import math
import re
from collections import Counter

# --------------------------------------------------------------------------
# The entity-relationship data. In a real system: Dataverse/OrderCore tables
# or a graph store; here, plain dicts so the traversal logic is fully visible.
# --------------------------------------------------------------------------

BATCHES = {"B-1189": {"recalled": True}, "B-1204": {"recalled": False}}

SKUS = {
    "GR-2200": {"name": "burr espresso machine", "batches": ["B-1189"]},
    "KT-0450": {"name": "electric kettle", "batches": ["B-1204"]},
    "SB-0031": {"name": "subscription box: home", "batches": []},
}

ORDERS = {
    "88214": {"customer": "C-301", "sku": "GR-2200"},
    "88377": {"customer": "C-318", "sku": "KT-0450"},
    "88401": {"customer": "C-322", "sku": "GR-2200"},
    "88455": {"customer": "C-301", "sku": "SB-0031"},
}

CUSTOMERS = {"C-301": "M. Okafor", "C-318": "D. Reyes", "C-322": "S. Lindqvist"}

CHARGEBACKS = {
    "CB-77": {"customer": "C-301", "status": "open"},
    "CB-81": {"customer": "C-318", "status": "open"},
    "CB-84": {"customer": "C-322", "status": "resolved"},
}

QUESTION = "Which customers with open chargebacks bought from the recalled batch?"


# --------------------------------------------------------------------------
# Attempt 1: similarity search over prose renderings of the same records.
# --------------------------------------------------------------------------

def record_passages() -> list[str]:
    passages = [
        f"Batch {b} {'has been recalled' if info['recalled'] else 'passed inspection'}."
        for b, info in BATCHES.items()
    ]
    passages += [
        f"Order {o} was placed by customer {CUSTOMERS[i['customer']]} for the {SKUS[i['sku']]['name']}."
        for o, i in ORDERS.items()
    ]
    passages += [
        f"Chargeback {c} for customer {CUSTOMERS[i['customer']]} is {i['status']}."
        for c, i in CHARGEBACKS.items()
    ]
    return passages


def embed(text: str) -> Counter:
    return Counter(re.findall(r"[a-z0-9']+", text.lower()))


def cosine(a: Counter, b: Counter) -> float:
    dot = sum(a[t] * b[t] for t in a)
    norm = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return dot / norm if norm else 0.0


def similarity_attempt() -> None:
    print("--- attempt 1: similarity search over the records as prose ---")
    q = embed(QUESTION)
    ranked = sorted(record_passages(), key=lambda p: cosine(q, embed(p)), reverse=True)
    for passage in ranked[:3]:
        print(f"  top chunk: {passage}")
    print(
        "  -> every chunk is true, none is the answer: the answer is an\n"
        "     intersection across records, and no single passage contains it.\n"
    )


# --------------------------------------------------------------------------
# Attempt 2: traverse the relationships. The answer is a path.
# --------------------------------------------------------------------------

def traversal_attempt() -> None:
    print("--- attempt 2: graph traversal ---")
    recalled = {b for b, info in BATCHES.items() if info["recalled"]}
    affected_skus = {s for s, info in SKUS.items() if set(info["batches"]) & recalled}
    buyers = {i["customer"] for i in ORDERS.values() if i["sku"] in affected_skus}
    open_cb = {i["customer"] for i in CHARGEBACKS.values() if i["status"] == "open"}

    print(f"  recalled batches: {sorted(recalled)}")
    print(f"  -> affected SKUs: {sorted(affected_skus)}")
    print(f"  -> customers who bought them: {sorted(buyers)}")
    print(f"  -> of those, with open chargebacks: {sorted(buyers & open_cb)}")
    for c in sorted(buyers & open_cb):
        print(f"\n  answer: {CUSTOMERS[c]} ({c})")


def main() -> None:
    print(f"question: {QUESTION}\n")
    similarity_attempt()
    traversal_attempt()


if __name__ == "__main__":
    main()
