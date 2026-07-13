# Context Engineering for Enterprise Agents — Companion Repo

This repository holds the full, runnable code that accompanies *Context Engineering for
Enterprise Agents: Designing the Information Systems Behind Production AI*.

Inline code in the book is intentionally short and illustrative (≤ ~30 lines). This repo is
the source of truth for anything a reader would actually copy, run, and modify. Every folder
here corresponds to a chapter or chapter section, and every inline snippet in the manuscript
that has a repo counterpart is marked with a callout pointing back here.

## How this repo is organized

Each `chXX-<topic>/` folder is self-contained: its own dependencies, its own `.env.example`,
its own README. You do **not** need to set up the whole repo to run one chapter's example —
just `cd` into the folder you care about and follow its README.

| Folder | Chapter | What it demonstrates |
|---|---|---|
| `ch04-system-prompts/` | 4 | Altitude-calibrated system prompt design |
| `ch05-retrieval/pipeline-rag/` | 5 | Baseline pipeline RAG |
| `ch05-retrieval/agentic-rag/` | 5 | RAG with a planning/critique loop |
| `ch05-retrieval/graphrag/` | 5 | Knowledge-graph retrieval for multi-hop queries |
| `ch06-memory/minimal-tiered-memory/` | 6 | Build-it-yourself OS-style tiered memory (core/recall/archival) |
| `ch06-memory/foundry-agent-memory/` | 6 | Memory using Microsoft Foundry Agent Service |
| `ch07-mcp/internal-mcp-server/` | 7 | Internal MCP server (the TixCore/CRM worked example) |
| `ch08-compaction/` | 8 | Compaction and tool-result clearing |
| `ch09-subagents/` | 9 | Context isolation via sub-agents |
| `ch10-orchestration/semantic-kernel/` | 10 | Orchestration with Semantic Kernel |
| `ch10-orchestration/microsoft-agent-framework/` | 10 | Orchestration with Microsoft Agent Framework |
| `ch11-long-horizon/` | 11 | Session continuity across long-horizon runs |
| `ch12-security/injection-detection-demo/` | 12 | Defensive injection-detection demo (no working exploit code) |
| `ch13-governance/dataverse-retrieval-acl/` | 13 | Retrieval-time access control on Dataverse |
| `ch14-evaluation/` | 14 | Context-quality evaluation harness |
| `ch15-reference-architecture/` | 15 | The full assembled reference architecture from Part V |

## Prerequisites

- Python 3.11+ for all Python folders (see root `requirements.txt` for shared baseline
  packages; each folder pins its own exact versions on top of this)
- .NET 8 SDK for the C# / Semantic Kernel / Microsoft Agent Framework folders
- An Azure subscription with access to Microsoft Foundry, Dataverse, and Power Platform for
  the Azure-native chapters (Ch. 6 Foundry example, Ch. 7, Ch. 10, Ch. 13, Ch. 15)
- Copy each folder's `.env.example` to `.env` and fill in your own endpoint/key values —
  never commit a real `.env` file

## Versioning note

This is a fast-moving stack. Every folder pins **exact** dependency versions in its own
`requirements.txt` or `.csproj`, and every folder's README carries a "Last verified working"
date and SDK version table. The manuscript itself never states a specific SDK version number
in prose — always check the folder README here for the tested versions as of the date shown,
not the book text.

## Releases

Git tags mark major manuscript milestones (e.g. `v0.1-draft-part1`, `v1.0-final`) so a given
tag's code matches a specific manuscript state. If you're reading a physical or PDF copy of
the book, check the tag that corresponds to your edition rather than assuming `main`.

## License

TBD — add your chosen license before making this repo public.
