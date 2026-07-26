# Ch09 Subagents

> Accompanies the book — Chapter 9, "Context Isolation and Sub-Agents."

## What this demonstrates

The chapter's central claim, made runnable: the triage → resolution
contamination bug is fixed **structurally** by isolation, not by better
prompting. The same Northwind contact is orchestrated two ways:

- **Shared context** (the single-agent baseline): the triage step deliberates at
  length — including a page of "maybe it's a shipping delay" musing — before
  concluding *billing*. All of that reasoning stays in the one window the
  resolution step then reads, so the resolution agent opens on a shipping delay
  the customer's issue isn't about. **Contaminated.**
- **Isolated sub-agents**: triage runs in its own context and returns a small
  structured `TriageResult`; only the *conclusion* (`category=billing`) crosses
  the boundary. The resolution agent starts from a clean window holding just
  that, and opens on billing. **Clean** — and its context is a fraction of the
  size (20 vs 159 tokens in the demo).

The point of the mock: contamination is a function of *what's in the window*, so
isolation — which controls what's in the window — prevents it by construction.

## Dependency-free by design

Deterministic and stdlib-only; runs offline with no API key and no `pip install`.
The sub-agents are mocks whose behaviour depends on their context contents. A
production version would run real model calls behind the same structured
`TaskSpec` → `TriageResult` handoff; the isolation boundary and the
transcript-vs-structured-result discipline are what carry over.

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

## How to run

```bash
python main.py            # the guided demonstration
python -m unittest -v     # the isolation tests (4 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

Per the book's repo conventions, this is the runnable version. The manuscript's
inline snippet is the orchestrator delegating with a structured task spec and
receiving a structured result. This chapter is **pattern-only**: the frameworks
that actually orchestrate these handoffs (Microsoft Agent Framework, LangGraph)
are Chapter 10's subject. The structured-handoff shape here is reused in
Chapters 10–11.
