# Minimal Tiered Memory

> Accompanies the book — Chapter 6, "Memory Architectures for Agents" — build-it-yourself example

## What this demonstrates

The 'build it yourself first' OS-style tiered memory pattern: a small always-in-context core tier, a searchable recall tier, and a long-term archival tier, modeled on RAM/cache/disk.

## Prerequisites

- Python 3.11+
- SQLite (bundled, no external service needed)

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
