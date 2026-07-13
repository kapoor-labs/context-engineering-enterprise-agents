# Ch15 Reference Architecture

> Accompanies the book — Chapter 15, "Reference Architectures on Azure and Power Platform"

## What this demonstrates

The full assembled system from Part V: dispatch agent, inspection agent, and compliance-reporting agent sharing a governed context layer on Dataverse.

## Prerequisites

- .NET 8 SDK
- Azure subscription with Foundry, Dataverse, and Power Platform access

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
