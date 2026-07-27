# Ch15 Reference Architecture

> Accompanies the book — Chapter 15, "Reference Architectures on Azure and Power Platform."

## What this demonstrates

The book's promise, kept in code: this folder **composes** the prior chapters'
runnable modules into the governed reference architecture — it does **not**
re-implement anything.

- It prints the **three architectures** (single-agent grounded copilot →
  multi-agent operations system → governed enterprise platform) as
  **component → chapter maps**: every box names the write/select/compress/isolate
  operation it serves and the chapter that taught it. If a component can't trace
  to a chapter, it doesn't belong — the map is the build audit.
- It runs one **governed contact through Architecture 3**, wired from three prior
  chapters' *actual* modules:
  - **Ch. 14** (`ch14-evaluation`) — the golden-set eval gate that must pass to deploy.
  - **Ch. 13** (`ch13-governance/dataverse-retrieval-acl`) — governed, on-behalf-of
    retrieval (the first-line CSA sees status/line-items/shipping, not payment).
  - **Ch. 10** (`ch10-orchestration/minimal-orchestrator`) — the
    triage → resolution → approval → QA flow (refund issued exactly once).

The composition *is* the reference architecture. Nothing is duplicated; the
modules are imported and run.

## Dependency-free by design

Deterministic, stdlib-only; runs offline with no API key and no `pip install`. The
assembly loads the sibling chapter modules by path, so run it from within a clone
of the repo (the sibling `ch10-…`, `ch13-…`, `ch14-…` folders must be present).

## Where the map points

| Architecture | Northwind reached it after | Source chapters |
|---|---|---|
| 1 — single-agent grounded copilot | Chapter 5 | Ch. 4, 5, 7, 10 |
| 2 — multi-agent operations system | Chapter 11 | Ch. 5–11 |
| 3 — governed enterprise platform | Chapter 13 (end state) | Ch. 4–14 |

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages. Run from within the repo (sibling chapter folders present).

## How to run

```bash
python main.py                 # the three maps + the assembled governed contact
python -m unittest -v          # the assembly tests (5 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

Most organizations must *earn* Architecture 3 — starting there fails (see the
chapter). This assembly is the destination; the retrospective in Chapter 16 looks
back over the whole journey that reached it.
