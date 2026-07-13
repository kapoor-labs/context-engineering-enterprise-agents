# Dataverse Retrieval Acl

> Accompanies the book — Chapter 13, "Governance, Provenance, and the Enterprise Context Layer"

## What this demonstrates

Retrieval-time access control enforced against Dataverse, plus provenance metadata attached to retrieved context, so a compromised prompt can't cause retrieval of data the agent isn't authorized to access.

## Prerequisites

- .NET 8 SDK
- Azure subscription with Dataverse access

Copy `.env.example` to `.env` in this folder and fill in your own values before running
anything. Never commit a real `.env` file.

## How to run

```bash
dotnet restore
dotnet run
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
