"""Foundry Agent Service memory — companion code for Chapter 6.

Maps the chapter's memory taxonomy (working / episodic / semantic / procedural)
onto Microsoft Foundry Agent Service's native memory scopes (session / user /
procedural), and emits an example agent-memory configuration you can adapt.

IMPORTANT — capability status: Foundry Agent Service agent memory was in
PUBLIC PREVIEW at the time of writing (Build 2026). Preview APIs change.
This script therefore does everything that is stable — the taxonomy mapping
and the configuration shape — locally and deterministically, and prints
pointers for the live part instead of hard-coding SDK calls that may be stale
by the time you run them. For the live walkthrough, follow the current
Microsoft Learn quickstart for agent memory with your own Foundry project
(see README), using the .env values in .env.example.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# --------------------------------------------------------------------------
# The mapping the chapter's Azure sidebar spells out. The "almost" column is
# the part teams skip: Foundry's session memory is working memory's durable
# shadow within a session — NOT a per-customer episodic history. If you need
# Chapter 6's episodic memory (contact histories across weeks), you build and
# govern that store yourself (see ../minimal-tiered-memory/ and Dataverse).
# --------------------------------------------------------------------------

TAXONOMY_MAPPING = [
    # (chapter term, Foundry scope, fit, caveat)
    ("working memory", "(the context window itself)", "exact",
     "free and volatile; not a Foundry memory scope"),
    ("episodic memory", "-- no direct scope --", "gap",
     "session memory persists salient state within a session, not a "
     "cross-session per-customer contact history; bring your own store"),
    ("semantic memory", "user memory", "close",
     "durable facts/preferences about a user, carried across sessions"),
    ("procedural memory", "procedural memory", "exact",
     "learned adjustments to agent behavior; gate adoption (see Ch. 6/12)"),
]

EXAMPLE_AGENT_MEMORY_CONFIG = {
    "note": ("Illustrative configuration shape for an agent with memory "
             "scopes enabled. Field names in preview APIs drift - treat the "
             "current Microsoft Learn reference as authoritative."),
    "agent": "northwind-agent-assist",
    "memory": {
        "user_memory": {
            "enabled": True,
            "purpose": "semantic: customer preferences and durable facts",
            "erasure": "must cascade with your GDPR process - see Ch. 6 hygiene",
        },
        "session_memory": {
            "enabled": True,
            "purpose": "working-memory shadow within a session",
        },
        "procedural_memory": {
            "enabled": False,
            "why_disabled": ("Northwind adopts learned rules through a human "
                             "review gate into the versioned prompt repo "
                             "(Ch. 4/6), not silent self-update"),
        },
    },
}


def main() -> None:
    print("Chapter 6 taxonomy -> Foundry Agent Service memory scopes\n")
    print(f"{'chapter term':<20} {'Foundry scope':<28} fit    caveat")
    print("-" * 100)
    for term, scope, fit, caveat in TAXONOMY_MAPPING:
        print(f"{term:<20} {scope:<28} {fit:<6} {caveat}")

    print("\nExample agent-memory configuration (illustrative shape):\n")
    print(json.dumps(EXAMPLE_AGENT_MEMORY_CONFIG, indent=2))

    endpoint = os.environ.get("PROJECT_ENDPOINT", "")
    env_file = Path(__file__).with_name(".env")
    print("\nLive walkthrough:")
    if endpoint:
        print(f"  PROJECT_ENDPOINT is set ({endpoint[:40]}...) - follow the "
              "current Microsoft Learn agent-memory quickstart with this project.")
    else:
        hint = "" if env_file.exists() else " (copy .env.example to .env first)"
        print("  No PROJECT_ENDPOINT configured" + hint + ".")
        print("  Agent memory was in PUBLIC PREVIEW at time of writing; this "
              "folder intentionally ships no preview SDK calls that would rot. "
              "See README for the current docs pointer.")


if __name__ == "__main__":
    main()
