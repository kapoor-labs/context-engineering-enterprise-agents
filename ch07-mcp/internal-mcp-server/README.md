# Internal OrderCore MCP server

> Accompanies the book — Chapter 7, "Tools, Function-Calling, and MCP" — the OrderCore worked example.

## What this demonstrates

An internal **Model Context Protocol (MCP)** server that wraps Northwind's
fictional legacy order-management system, **OrderCore**, and exposes it to agents
as a small set of governed tools. It is the "wrap the legacy system once, behind
a standard interface" pattern from the chapter, and it shows the four design
decisions the chapter argues for:

1. **Expose the fewest operations that do the job** — five customer-service tools
   (`lookup_order`, `check_fulfilment`, `add_order_note`, `issue_replacement`,
   `issue_refund`, plus the human `confirm_refund` step), not OrderCore's ~40
   operations. Everything not exposed can't be misused, can't consume the context
   budget, and can't be selected in error.
2. **Scope access by role** — seniority tiers (`csa.read` first-line →
   `csa.write` senior → `csa.refund` lead) survive the move to tools. The agent
   inherits the operator's permissions, not the union of everyone's.
3. **Separate read from write** — read tools are free to retry; write tools change
   the world. The split is visible in the names, enforced in the permission check,
   and stated in each tool's description.
4. **Gate consequential writes behind human confirmation** — `issue_refund` only
   *proposes*; it never moves money on the model's say-so. A human commits the
   proposal via `confirm_refund`. (This rule is canon for Chapters 10 and 13.)

The tool **descriptions** are written the way the chapter argues for: each says
what the tool returns, when to reach for it, and — crucially — what it will *not*
do. They are context the model reads, not API docs.

## Dependency-free by design

This server speaks MCP's JSON-RPC 2.0 wire protocol over stdio using **only the
Python standard library**, so it runs offline with no `pip install`. A production
server would build on the official `mcp` Python SDK (or the C#/TypeScript SDKs)
rather than hand-rolling the transport — but the tool *designs* above are what
carry over, not the transport plumbing.

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

Copy `.env.example` to `.env` if you want to set a session role for `--serve`;
never commit a real `.env`.

## How to run

Guided demonstration (no MCP client needed — prints role scoping, read/write
separation, the refund confirmation gate, and the audit log):

```bash
python main.py --demo
```

As a real MCP stdio server, with the session's CSA role supplied by the
environment (as a gateway would inject it):

```bash
ORDERCORE_CSA_ROLE=csa.write python main.py --serve
```

Then send newline-delimited JSON-RPC on stdin, e.g.:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"lookup_order","arguments":{"order_id":"NW-4820193"}}}
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

Per the book's repo conventions, this folder contains the runnable version,
including the JSON-RPC transport and audit logging that the manuscript's inline
snippet omits for brevity. The book's printed code block is a single
well-described, role-scoped tool definition — the short version that matches it
is the `lookup_order` tool in `main.py`.
