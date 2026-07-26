# Agentic RAG

> Accompanies the book — Chapter 5, "Retrieval Architectures" — the agentic pattern

## What this demonstrates

RAG with the judgment moved inside: a **plan → retrieve → critique → re-retrieve** loop,
instrumented so you can watch what each iteration adds. It runs the chapter's composition
question — "Can I still return my delayed espresso machine?" — which no single retrieval
can answer, because the answer is a join of a Tier 1 order record and Tier 2 policy
articles. The critique step notices that a retrieved article *references* an addendum not
yet in evidence and re-retrieves it; the loop ends by declaring sufficiency (or, on budget
exhaustion, escalating instead of guessing).

## Prerequisites

- Python 3.11+
- Nothing else — the default run is standard-library only. The planner and critic are
  deterministic functions standing in for model calls, so the loop's mechanics run
  without API keys. In production, `plan()` and `critique()` are where the model reasons;
  the loop structure, evidence ledger, and sufficiency gate stay as shown.

No keys are needed for the default run. `.env.example` is provided for the extension
exercise of replacing the stand-ins with real model calls — copy it to `.env` and fill in
your own values if you do; never commit a real `.env` file.

## How to run

```bash
python main.py
```

Each `--- iteration N ---` block shows the plan/critique output and the retrievals it
triggered. See the inline comments for the concept-to-code mapping referenced from the
manuscript.

## Versions

| Package | Version | Last verified |
|---|---|---|
| Python (standard library only) | 3.11+ (tested on 3.14.0) | 2026-07-19 |

## Scope note

Per the book's repo conventions: this folder is the runnable counterpart to the chapter's
agentic RAG section. The chapter's single inline snippet is the query router; the three
architecture implementations, including this one, live here in the repo.
