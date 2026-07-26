# Ch08 Compaction

> Accompanies the book — Chapter 8, "Compaction, Summarization, and Context Clearing."

## What this demonstrates

A simulated multi-hour Northwind session (the "tree-strand" case: warranty →
shipping → billing) run through the chapter's three ideas:

1. **Tool-result clearing is where the tokens are.** The raw tool payloads are
   ~90% of the window; the conversation is a small fraction. Clearing them
   (clear-after-use, with a re-callable pointer left behind) reclaims most of the
   window.
2. **Compaction distills into structured `CaseState`, not prose** — six
   independently checkable fields (order IDs, case ID, commitments, decisions,
   open items, flags).
3. **Probe-question testing measures what a compaction dropped.** The same
   session is compacted two ways — a naive "summarize into prose" compactor and
   the chapter's field-naming compactor — and each is scored against a fixed probe
   set. The naive one silently leaks the commitments and the exact dollar amount
   (50%); the field one preserves everything (100%). That gap is the difference
   between "the summary looks good" and a number you can gate a deploy on.

## Dependency-free by design

The compactors are **deterministic simulations** of what an LLM would do, so the
demo and tests run offline with only the Python standard library — no API key, no
`pip install`. A production pipeline would call a model with the field-naming
compaction prompt and parse the structured result; the trigger logic, the
`CaseState` shape, the tool-result clearing, and the probe test are the parts that
carry over unchanged.

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

## How to run

```bash
python main.py            # the guided demonstration
python -m unittest -v     # the probe-question tests (5 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

Per the book's repo conventions, this folder is the runnable version. The
manuscript's inline snippet is the `maybe_compact` trigger-and-carry-forward
skeleton; here it is fleshed out with the scenario, the two compactors, the
tool-result clearing, and the probe-question tests referenced from the chapter.
This example covers **within-session** health only — cross-session and multi-day
continuity are Chapters 6 and 11.
