# GraphRAG

> Accompanies the book — Chapter 5, "Retrieval Architectures" — the graph pattern

## What this demonstrates

The chapter's recall question — "Which customers with open chargebacks bought from the
recalled batch?" — answered two ways on the same data:

1. **Similarity search** over prose renderings of the records: every retrieved chunk is
   true, none is the answer, because the answer is an intersection across records and no
   single passage contains it. This is the "structurally cannot answer" claim from the
   chapter, made runnable.
2. **Graph traversal**: batch → SKUs → orders → customers, intersected with chargeback
   status — the answer is a path, not a passage.

It also encodes the chapter's caveat in its comments: when your entities already live in
tables (as Northwind's do, in Dataverse/OrderCore), this traversal is a database join —
route relational questions to the structured store before building a knowledge graph.

## Prerequisites

- Python 3.11+
- Nothing else — the default run is standard-library only. The graph is in-memory dicts
  and the "embedding" is bag-of-words cosine, standing in for a graph store and an
  embedding model; the passages-versus-paths point is unchanged by the simplification.

No keys are needed for the default run. `.env.example` is provided for the extension
exercise of wiring in a real graph/embedding backend — copy it to `.env` and fill in your
own values if you do; never commit a real `.env` file.

## How to run

```bash
python main.py
```

Attempt 1 prints the top similarity chunks (true but useless); attempt 2 prints each hop
of the traversal and the answer. See the inline comments for the concept-to-code mapping
referenced from the manuscript.

## Versions

| Package | Version | Last verified |
|---|---|---|
| Python (standard library only) | 3.11+ (tested on 3.14.0) | 2026-07-19 |

## Scope note

Per the book's repo conventions: this folder is the runnable counterpart to the chapter's
GraphRAG section. The chapter's single inline snippet is the query router; the three
architecture implementations, including this one, live here in the repo.
