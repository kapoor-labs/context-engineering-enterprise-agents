# Ch10 — the Northwind flow on Microsoft Agent Framework

> Accompanies the book — Chapter 10, "Orchestration Frameworks in Practice."

## What this is

The same triage → resolution → approval → QA flow that
`../minimal-orchestrator/` builds from scratch, expressed against **Microsoft
Agent Framework** — the convergence of Semantic Kernel and AutoGen (SK is *not*
deprecated; it is the enterprise orchestration layer inside the unified
framework). In production you would run this on a managed runtime such as
Foundry Agent Service, which supplies identity, hosted execution, and the
observability the Chapter 14 dashboard reads.

## Two parts, one honest split

- **`describe_mapping()` runs offline** (stdlib only): it prints how the Northwind
  flow maps onto Agent Framework's orchestration patterns (handoff, sequential),
  what the framework owns (state, checkpointing, retries, the approval state,
  observability), and how the Chapter 9 structured handoffs ride the edges. This
  is what verifies in a clean environment.

- **`ILLUSTRATIVE_AGENT_FRAMEWORK_CODE`** (a string constant in the file) is an
  explicitly-labelled **sketch** of the real SDK wiring. It is **not executed**
  and **not guaranteed to match the current package API** — Agent Framework is
  the fastest-moving naming area in the book (see the book's §5 naming caveats).
  Treat it as a shape to adapt.

The runnable `minimal-orchestrator/` is the source of truth for *what the
patterns do*; this folder is the source of truth for *how they map onto the
Microsoft stack*. Neither pretends the fast-moving SDK surface is frozen.

## Prerequisites

- To run the mapping: Python 3.11+ (tested 3.14.0), no packages.
- To adapt the illustrative sketch into a real workflow: the `agent-framework`
  Python package and access to a model endpoint (e.g. Foundry Agent Service).
  **Verify the SDK's current class and method names before relying on the
  sketch** — copy `.env.example` to `.env` for endpoint/credentials.

## How to run

```bash
python agent_framework_flow.py     # prints the offline mapping
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (mapping, stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |
| `agent-framework` (for the sketch) | _verify current — fast-moving_ | 2026-07 |

## Scope note

Pattern-to-platform mapping only. The runnable, tested engine is in
`../minimal-orchestrator/`. Week-long durable execution is Chapter 11.
