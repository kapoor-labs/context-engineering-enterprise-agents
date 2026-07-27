# Dataverse Retrieval ACL

> Accompanies the book — Chapter 13, "Governance, Provenance, and the Enterprise Context Layer."

## What this demonstrates

Governance built into the context layer, not bolted on:

- **Provenance** on every retrievable item (source, owner, validation status,
  freshness) — so the archived "2019 policy" from Chapter 5 is a *filterable
  condition*, never served as canonical.
- **Retrieval-time access control** under **on-behalf-of identity** — the same
  query returns different context to a first-line CSA vs a fraud investigator
  (row-level and column-level security), enforced at the data layer, not by the
  agent or the prompt.
- **The Chapter 12 attack replayed** — an injected instruction that asks a
  first-line CSA's session for payment data or a fabricated "priority policy"
  returns nothing: the identity (not the prompt) is what the data layer checks,
  and the fake policy has no registered source. The attack dies at retrieval.
- **The super-identity pitfall by contrast** — running retrieval as an all-seeing
  agent identity leaks exactly what on-behalf-of withholds.
- **An audit trail** — every retrieval is recorded with the identity it acted as
  and what it returned.

## Python here; C# on Dataverse in production

The idiomatic production call is C# against the Dataverse SDK, flowing the user
identity so Dataverse row/column security applies. This folder implements the same
*design* in dependency-free Python so it verifies offline (all companion code in
this book is Python; see the repo conventions). The security model — on-behalf-of
identity, row/column filtering at the data layer, provenance, audit — is what
carries over, not the transport.

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

## How to run

```bash
python main.py                 # the governed retrieval demo (5 parts)
python -m unittest -v          # the access-control tests (6 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

Governance defines what's *allowed* and records what *happened*. Measuring whether
the agent is actually doing well — evaluating context quality, catching the
in-policy-but-wrong failure — is Chapter 14. This governed architecture is also
the foundation Chapter 15 assembles.
