"""Minimal tiered memory — companion code for Chapter 6, "Memory Architectures".

The "build it yourself first" example: an OS-style tiered memory — a small,
budgeted, always-in-context CORE tier; a searchable RECALL tier; a durable
ARCHIVAL tier — run against the blender customer's four contacts so you can
watch entries demote out of core and return via recall.

The chapter's teaching claim, made runnable: a memory system is exactly three
policies — a write policy (what persists, in what form), an eviction policy
(what leaves the expensive tier, in what order), and a retrieval policy (what
comes back into context, on what signal). Every memory framework is a bundle
of opinions about those three things.

Self-contained: standard library only. Recall search is bag-of-words cosine
standing in for an embedding index; in production the extraction step (what
deserves to become an entry) is usually a model call — here the demo writes
hand-authored entries so the tier mechanics stay fully visible.
"""

from __future__ import annotations

import math
import re
from collections import Counter

# --------------------------------------------------------------------------
# Recall tier: searchable store (bag-of-words cosine stands in for embeddings).
# --------------------------------------------------------------------------

def _embed(text: str) -> Counter:
    return Counter(re.findall(r"[a-z0-9']+", text.lower()))


def _cosine(a: Counter, b: Counter) -> float:
    dot = sum(a[t] * b[t] for t in a)
    norm = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return dot / norm if norm else 0.0


class RecallStore:
    def __init__(self) -> None:
        self._entries: list[dict] = []

    def index(self, entry: dict) -> None:
        self._entries.append(entry)

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = _embed(query)
        ranked = sorted(self._entries, key=lambda e: _cosine(q, _embed(e["text"])), reverse=True)
        return ranked[:k]


# --------------------------------------------------------------------------
# The tiered memory. The write/evict path here is the manuscript's inline
# snippet, fleshed out; the policies are deliberately explicit and overridable.
# --------------------------------------------------------------------------

CORE_BUDGET = 350  # words of core block carried into every future context


def core_size(core: list[dict]) -> int:
    return sum(len(e["text"].split()) for e in core)


class TieredMemory:
    def __init__(self, core_budget: int = CORE_BUDGET) -> None:
        self.core: list[dict] = []       # always in context, budgeted
        self.recall = RecallStore()      # searchable on demand
        self.archival: list[dict] = []   # durable store of record
        self.core_budget = core_budget

    # -- write policy: everything lands in core first; provenance is required.
    def write(self, entry: dict) -> None:
        """entry: dict with text, kind (episodic|semantic|procedural),
        ts (timestamp), source (who/what produced it), customer_id."""
        missing = {"text", "kind", "ts", "source", "customer_id"} - entry.keys()
        if missing:
            raise ValueError(f"entry missing required fields: {missing}")
        self.core.append(entry)
        self._evict()

    # -- eviction policy: oldest non-procedural entries demote first.
    #    Demotion, never deletion: evicted entries stay searchable in recall
    #    and durable in archival. Procedural rules never silently leave core —
    #    a standing rule falling out of context is Ch. 4's rule 47 again.
    def _evict(self) -> None:
        while core_size(self.core) > self.core_budget:
            candidates = sorted(
                (e for e in self.core if e["kind"] != "procedural"),
                key=lambda e: e["ts"],
            )
            if not candidates:
                raise RuntimeError("core over budget but only procedural entries remain: "
                                   "raise the budget or retire a rule deliberately")
            victim = candidates[0]
            self.core.remove(victim)
            self.recall.index(victim)
            self.archival.append(victim)
            print(f"    [evict] demoted to recall: ({victim['kind']}) {victim['text'][:60]}...")

    # -- retrieval policy: core always rides along; recall is selected per
    #    turn — memory's read side is Chapter 5's select operation.
    def assemble_context(self, query: str, k: int = 3) -> str:
        lines = ["== CORE (always present) =="]
        lines += [f"  ({e['kind']}, {e['ts']}) {e['text']}" for e in self.core]
        lines.append(f"== RECALL (selected for: {query!r}) ==")
        lines += [f"  ({e['kind']}, {e['ts']}) {e['text']}" for e in self.recall.search(query, k)]
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Demo: the blender customer's four contacts. A small core budget is used so
# eviction is visible within four contacts; the mechanics don't change with
# scale, only the timescale does.
# --------------------------------------------------------------------------

def main() -> None:
    memory = TieredMemory(core_budget=60)
    cust = "C-877"

    def w(ts: str, kind: str, text: str, source: str = "wrapup-extractor") -> None:
        print(f"  write ({kind}): {text}")
        memory.write({"text": text, "kind": kind, "ts": ts,
                      "source": source, "customer_id": cust})

    print("--- contact 1 (June 30): intermittent power failure ---")
    w("2026-06-30", "episodic", "Contact 1: blender BL-300 intermittent power "
      "failure; walked through factory reset; customer will retest.")

    print("\n--- contact 2 (July 6): fault persists ---")
    w("2026-07-06", "episodic", "Contact 2: fault persists after reset; second "
      "reset performed on the call; customer asked about replacement.")
    w("2026-07-06", "semantic", "Prefers email follow-up.", source="customer-stated")

    print("\n--- contact 3 (July 12): third contact, same fault ---")
    w("2026-07-12", "episodic", "Contact 3: same fault; customer declined further "
      "troubleshooting; wants replacement, not repair.")
    w("2026-07-12", "semantic", "Factory reset already performed twice; do not "
      "propose the troubleshooting script again.", source="customer-stated")
    w("2026-07-12", "procedural", "Rule (adopted after CSA review): on a third "
      "contact for the same fault, lead with resolution options, not diagnostics.",
      source="csa-correction-review")

    print("\n--- contact 4 (July 19): what the copilot sees before hello ---\n")
    print(memory.assemble_context("blender replacement request"))

    print(f"\ncore: {core_size(memory.core)} words within budget {memory.core_budget}; "
          f"recall holds {len(memory.recall._entries)}; archival holds {len(memory.archival)}.")
    print("Note what eviction did: demoted, indexed, archived - never deleted.")


if __name__ == "__main__":
    main()
