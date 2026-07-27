# Ch10 — minimal orchestrator (build it yourself first)

> Accompanies the book — Chapter 10, "Orchestration Frameworks in Practice."

## What this demonstrates

The chapter's central argument, made runnable: a multi-agent workflow **has**
state management, checkpointing/resume, retry semantics, handoff routing, and a
human-in-the-loop approval gate whether you design them or let them accrete in a
script. This is the "build it yourself first" version — a tiny stdlib workflow
engine that implements all five on purpose, so you can see exactly what
Microsoft Agent Framework or LangGraph gives you (and why Priya's hand-rolled
script kept reinventing it, badly).

It runs the Northwind **triage → resolution → approval → QA** flow and shows:

- **Handoff routing** as declared edges — including QA-fail routing *back* to
  resolution with the specific objection, so the second pass fixes the named
  defect instead of re-guessing the case.
- **Durable state + checkpoints** so a mid-workflow failure *resumes* instead of
  restarting — and the refund is issued **exactly once** across an interruption
  (the idempotency a hand-rolled retry loop usually fails to get right).
- **Retry** semantics — a transient resolution failure retries and succeeds; a
  non-retryable interruption checkpoints and resumes.
- **Human-in-the-loop** as a first-class `awaiting_approval` pause with an audit
  record — not a prompt instruction.
- The **deterministic/generative split** — judgment steps (triage, resolution,
  QA verdict) are generative; the promise steps (approval, refund execution) are
  deterministic and guaranteed.

See the sibling `../microsoft-agent-framework/` folder for the same flow
expressed against Microsoft Agent Framework's Python API.

## Dependency-free by design

Deterministic, stdlib-only, runs offline with no API key and no `pip install`.
The agents are mocks; a production version runs the same declared graph on a real
framework and real model calls. The engine here is intentionally ~90 lines so the
five features are legible — it is a teaching engine, not a framework.

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

## How to run

```bash
python main.py                 # the guided demonstration (two scenarios)
python -m unittest -v          # the orchestration tests (6 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

This chapter's workflows complete within a day. Week-long, long-horizon
execution (durable multi-day state, mid-run recovery over days) is Chapter 11.
The approval gate here is the `issue_refund` human-confirmation rule from
Chapter 7, promoted to a first-class orchestrated state.
