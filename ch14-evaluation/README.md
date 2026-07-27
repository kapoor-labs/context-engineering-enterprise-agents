# Ch14 Evaluation

> Accompanies the book — Chapter 14, "Evaluating and Observing Context Quality."

## What this demonstrates

Three of the chapter's instruments, made runnable:

1. **The failure-classification rubric** as code — `classify_failure()` routes a
   failure to **model / context / tool / orchestration** from a few signals.
   Running the book's four prior failures through it lands all four in
   **context**, which is the chapter's thesis: context failure is the dominant
   production mode and it masquerades as model failure. (Tool and orchestration
   failures are routed *out* of the model column too — the misdiagnosis that
   wastes the most time.)
2. **A retrieval golden-set eval** with the chapter's payoff scenario — a golden
   query set passes against the current corpus; then a policy article is edited
   badly and the eval **fails on that change**, catching the Chapter 1 failure
   class (a wrong return-window answer) *before a customer sees it*. The archived
   2019 policy is never retrieved (freshness filter).
3. **A compaction probe eval** — Chapter 8's probe-question methodology as a
   standing regression: score a compaction by the fraction of task-critical probes
   its output still answers. A naive prose compactor regresses (50%); a
   field-naming one holds (100%).

The pattern across all three is the chapter's core move: turn "it seems fine" into
a number that can regress and gate a deploy.

## Dependency-free by design

Deterministic, stdlib-only; runs offline with no API key and no `pip install`.

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

## How to run

```bash
python main.py                 # the three instruments, demonstrated
python -m unittest -v          # the evaluation tests (10 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

A minimal harness to make the concepts concrete. A production practice adds
per-subsystem golden sets at scale, memory and resumability (fresh-instance)
evals, and OpenTelemetry-based tracing across the multi-agent flow — see the
chapter's On Azure sidebar. This is Part IV's close; Chapter 15 assembles
everything into one reference architecture.
