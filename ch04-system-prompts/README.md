# Ch04 System Prompts

> Accompanies the book — Chapter 4, "System Prompts and Instructions at Enterprise Scale"

## What this demonstrates

Rewriting a brittle, 2,000-word system prompt into an altitude-calibrated instruction set, with before/after examples and a small harness for comparing behavior across variants.

## Prerequisites

- Python 3.11+
- An API key for your model provider of choice

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
