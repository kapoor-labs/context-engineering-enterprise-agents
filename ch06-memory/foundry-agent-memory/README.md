# Foundry Agent Memory

> Accompanies the book — Chapter 6, "Memory Architectures for Agents" — Microsoft Foundry example

## What this demonstrates

The mapping from the chapter's memory taxonomy (working / episodic / semantic /
procedural) onto **Microsoft Foundry Agent Service's** native memory scopes (session /
user / procedural), including the gap the chapter's Azure sidebar warns about: Foundry's
*session memory* is a working-memory shadow within a session, **not** a per-customer
episodic contact history — if you need Chapter 6's episodic memory, you build and govern
that store yourself (see `../minimal-tiered-memory/` and the chapter's Dataverse
discussion). Also prints an illustrative agent-memory configuration shape, including
Northwind's decision to keep procedural self-update *disabled* in favor of a human
review gate (Chapters 4 and 6).

## Capability status — read this first

Foundry Agent Service agent memory was in **public preview** at the time of writing
(announced Build 2026). Preview APIs change. This folder therefore ships only what is
stable — the taxonomy mapping and configuration shape, printed locally and
deterministically — and deliberately contains **no preview SDK calls** that would rot
before you run them. For the live walkthrough, follow the current Microsoft Learn
quickstart for Foundry agent memory with your own Foundry project:
https://learn.microsoft.com/azure/foundry/ (search "agent memory"). Verify GA status
before relying on any of this in production.

## Prerequisites

- Python 3.11+ (the default run is standard-library only and needs no Azure resources)
- For the live walkthrough only: an Azure subscription with Microsoft Foundry access.
  Copy `.env.example` to `.env` and fill in your project endpoint; never commit a real
  `.env` file.

## How to run

```bash
python main.py
```

## Versions

| Package | Version | Last verified |
|---|---|---|
| Python (standard library only, default run) | 3.11+ (tested on 3.14.0) | 2026-07-19 |
| Foundry Agent Service agent memory | public preview | 2026-07-19 (status check) |

## Scope note

Per the book's repo conventions: this folder accompanies the chapter's "On Azure" sidebar
— it is a decision and mapping guide, not a hosted-service demo, because the underlying
feature was in preview at time of writing. The build-it-yourself counterpart the chapter's
inline snippet excerpts lives in `../minimal-tiered-memory/`.
