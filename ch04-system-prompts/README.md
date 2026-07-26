# ch04-system-prompts

> Accompanies the book — Chapter 4, "System Prompts and Instructions at Enterprise Scale"
> (sections "Structure for Tool-Heavy Agents" and "Prompts as Code")

## What this demonstrates

- A **sectioned system prompt** stored as versioned files (`prompts/northwind_agent/`):
  `role`, `constraints`, `tool_guidance`, `output_contract` — one job per section, so
  every future edit has an address.
- A **loader** (`prompt_loader.py`) that assembles the prompt and fails loudly if a
  required section is missing.
- **CI regression tests** (`test_prompt_structure.py`): structure enforced, an 800-word
  budget enforced, and two behavioral invariants fossilized as assertions — the
  delivery-date rule (the book's Chapter 1 incident) and the instruction-hierarchy
  precedence statement.

The prompt content is the Northwind rewrite from the chapter's "The Rewrite Ships"
section: ~650 words, down from the 3,000-word policy dump it replaced.

## Prerequisites

- Python 3.10+
- No API key needed — the loader and tests run entirely offline.

## How to run

```bash
pip install -r requirements.txt
python prompt_loader.py   # print the assembled prompt and its word count
pytest                    # run the CI checks
```

## Versions

| Package | Version | Last verified |
|---|---|---|
| Python | 3.12 | 2026-07 |
| `pytest` | 8.2.2 | 2026-07 |

## Scope note

Per the book's repo conventions: this folder is the full runnable version of the
chapter's inline snippet. The printed code block in the book shows the same loader and
tests in compressed form; this folder adds the actual prompt section files and the
extra precedence-statement test.
