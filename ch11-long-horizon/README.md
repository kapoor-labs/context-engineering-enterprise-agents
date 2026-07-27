# Ch11 Long Horizon

> Accompanies the book — Chapter 11, "Long-Horizon Agents and Session Continuity."

## What this demonstrates

The week-long chargeback dispute investigation, run as a series of separate
**sessions** that survive across boundaries because all task-critical state lives
in a durable store — never in a session's context. It composes the earlier
chapters into one **continuity stack**:

- durable task state (write, Ch. 6) → the `Store` (stands in for Dataverse)
- per-session working set (select, Ch. 5) → each step loads only what it needs
- session-boundary compaction (Ch. 8) → each step commits a compact result
- checkpointed workflow position (Ch. 10) → the plan's per-step statuses

And it makes the chapter's two canonical ideas runnable:

- **The fresh-instance test.** Every session is a brand-new instance holding *no*
  context from prior sessions; it continues purely from the persisted state. The
  demo also runs it as a literal "kill mid-task and resume from a stranger" check.
- **Idempotent write tools.** The submit step carries an idempotency key, so a
  crash in the gap between "the side effect happened" and "we recorded it" is
  replay-safe: on resume the submit is *called* again but *submitted* only once.

## Dependency-free by design

Deterministic and stdlib-only; runs offline with no API key and no `pip install`.
Sessions carry no state between calls — continuity is entirely via the `Store`,
which is exactly the property the fresh-instance test checks. A production version
persists the store to Dataverse and wakes sessions on a schedule (see the
chapter's On Azure sidebar).

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

## How to run

```bash
python main.py                 # the week-long investigation + crash/idempotency test
python -m unittest -v          # the continuity tests (6 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

This is composition, not new mechanics — memory, compaction, and orchestration
are taught in Chapters 6, 8, and 10 respectively. Persistent state as an *attack
surface* is deliberately out of scope here; that's Chapter 12.
