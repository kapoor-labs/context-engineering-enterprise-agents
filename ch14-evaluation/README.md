# Ch14 Evaluation

> Accompanies the book — Chapter 14, "Evaluating and Observing Context Quality"

## What this demonstrates

A small evaluation harness implementing the chapter's diagnostic rubric: distinguishing model failure vs. context failure vs. tool failure vs. orchestration failure.

## Prerequisites

- Python 3.11+

Copy `.env.example` to `.env` in this folder and fill in your own values before running
anything. Never commit a real `.env` file.

## How to run

```bash
pip install -r requirements.txt --break-system-packages
python main.py
```

See the inline comments in the code for the concept-to-code mapping referenced from the
manuscript.

## Versions

| Package | Version | Last verified |
|---|---|---|
| _(fill in before publishing)_ | | 2026-07 |

## Scope note

Per the book's repo conventions: this folder contains the full runnable implementation,
including error handling, retries, and logging that the manuscript's inline snippet omits
for brevity. If you're looking for the short version that matches the book's printed code
block, check that chapter's text first — this is the "make it actually run" version.
