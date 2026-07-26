# Pipeline RAG

> Accompanies the book — Chapter 5, "Retrieval Architectures" — the baseline pattern

## What this demonstrates

The baseline pipeline RAG pattern (chunk → embed → top-k → generate), including a
reproduction of the chapter's **2019-policy incident**: a naive "index everything" corpus
confidently retrieves a stale, superseded policy. The demo then applies the chapter's two
fixes — an editorial gate on what enters the index, and metadata carried on every chunk —
and shows the same query retrieving the current policy with its provenance attached.

## Prerequisites

- Python 3.11+
- Nothing else — the default run is standard-library only. The "embedding" is a
  bag-of-words vector standing in for a real embedding model; the stale-retrieval failure
  it demonstrates is a property of similarity search itself, not of the simplification.

No keys are needed for the default run. `.env.example` is provided for the extension
exercise of wiring in a real embedding model and model call — copy it to `.env` and fill
in your own values if you do; never commit a real `.env` file.

## How to run

```bash
python main.py
```

The first block of output is the incident (the 2019 policy wins the similarity contest);
the second block is the fixed pipeline. See the inline comments for the concept-to-code
mapping referenced from the manuscript.

## Versions

| Package | Version | Last verified |
|---|---|---|
| Python (standard library only) | 3.11+ (tested on 3.14.0) | 2026-07-19 |

## Scope note

Per the book's repo conventions: this folder is the runnable counterpart to the chapter's
pipeline RAG section. The chapter's single inline snippet is the query router; the three
architecture implementations, including this one, live here in the repo.
