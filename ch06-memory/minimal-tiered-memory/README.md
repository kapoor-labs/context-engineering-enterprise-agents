# Minimal Tiered Memory

> Accompanies the book — Chapter 6, "Memory Architectures for Agents" — the build-it-yourself example

## What this demonstrates

The OS-style tiered memory pattern (MemGPT/Letta lineage) built by hand: a small,
word-budgeted, always-in-context **core** tier; a searchable **recall** tier; a durable
**archival** tier. The demo runs the chapter's blender customer through her four contacts
so you can watch entries demote out of core when the budget objects (`[evict]` lines) and
come back via recall on the fourth contact.

The chapter's teaching claim, made runnable: **a memory system is exactly three policies**
— write (what persists, with mandatory provenance fields), eviction (oldest episodic
demotes first; procedural rules never silently leave core), and retrieval (core always
rides along; recall is selected per turn — Chapter 5's select operation pointed at a new
corpus). Every memory framework you evaluate is a bundle of opinions about these three.

## Prerequisites

- Python 3.11+
- Nothing else — standard library only. Recall search is bag-of-words cosine standing in
  for an embedding index; the demo writes hand-authored entries so the tier mechanics
  stay visible (in production, the extraction step is usually a model call).

No keys are needed. `.env.example` is provided for the extension exercise of wiring in a
real embedding index or extraction model — copy it to `.env` and fill in your own values
if you do; never commit a real `.env` file.

## How to run

```bash
python main.py
```

The demo uses a deliberately small core budget (60 words) so eviction is visible within
four contacts; the mechanics don't change with scale, only the timescale does.

## Versions

| Package | Version | Last verified |
|---|---|---|
| Python (standard library only) | 3.11+ (tested on 3.14.0) | 2026-07-19 |

## Scope note

Per the book's repo conventions: this folder is the full version of the chapter's inline
snippet (the write-with-eviction loop). The book prints the ~20 most illustrative lines;
this is the "make it actually run" version, with the provenance-required write path and
the procedural-entries-never-demote guard implemented rather than implied.
