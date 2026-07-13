# Ch11 Long Horizon

> Accompanies the book — Chapter 11, "Long-Horizon Agents and Session Continuity"

## What this demonstrates

Combining memory (Ch. 6), compaction (Ch. 8), and orchestration (Ch. 10) into one session-continuity pattern for agents that run across days, not single sessions. Shown here in Python for portability; a C# equivalent using Microsoft Agent Framework follows the same structure — see ch10-orchestration/ for that SDK's idioms.

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
