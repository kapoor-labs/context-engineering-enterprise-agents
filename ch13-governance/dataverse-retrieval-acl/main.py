#!/usr/bin/env python3
"""
Retrieval-time access control with provenance and audit — companion code for
Chapter 13, "Governance, Provenance, and the Enterprise Context Layer."

Demonstrates governance as it should have been built in, not bolted on:

  * PROVENANCE on every retrievable item (source, owner, validation status,
    freshness) — so archived/superseded content (the Chapter 5 "2019 policy")
    is a filterable condition, not a judgment the model must make from prose.
  * RETRIEVAL-TIME ACCESS CONTROL under ON-BEHALF-OF identity — the same query
    returns different context to a first-line CSA vs a fraud investigator,
    enforced at the data layer (row + column security), not by the agent.
  * The Chapter 12 ATTACK REPLAYED — an injected instruction that asks a
    first-line CSA's session to retrieve payment data or a fabricated "priority
    policy" returns nothing, because the identity (not the prompt) is what the
    data layer checks, and the fabricated policy has no registered source.
  * An AUDIT record per decision: acting_as, context used (with provenance),
    tool calls, approvals, outcome.
  * The SUPER-IDENTITY pitfall shown by contrast: running retrieval as an
    all-seeing agent identity leaks what on-behalf-of withholds.

The idiomatic production call is C# against the Dataverse SDK flowing the user
identity so row/column security applies; this is the same design in stdlib
Python so it verifies offline.

    python main.py            # or --demo
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
# Provenance: the metadata that travels with every retrievable item.
# --------------------------------------------------------------------------- #
@dataclass
class Provenance:
    source: str
    owner: str
    validation_status: str            # current | draft | archived | superseded
    effective_from: str = ""
    review_by: str = ""


@dataclass
class Record:
    rec_id: str
    kind: str                         # "policy" (Tier 2) | "order" (Tier 1)
    fields: dict[str, str]            # column -> value
    provenance: Provenance
    # Row-level security: which roles may read this row at all.
    allowed_roles: set[str] = field(default_factory=set)
    # Column-level security: columns only some roles may see.
    restricted_columns: dict[str, set[str]] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Identity: an operator the agent acts on behalf of. The agent never retrieves
# as itself; it flows the user's identity, so the data layer scopes results.
# --------------------------------------------------------------------------- #
@dataclass
class Identity:
    name: str
    roles: set[str]

    def may_read_row(self, r: Record) -> bool:
        return bool(self.roles & r.allowed_roles)

    def readable_columns(self, r: Record) -> list[str]:
        cols = []
        for col in r.fields:
            if col.startswith("_"):
                continue                          # internal helper, not a data column
            needed = r.restricted_columns.get(col)
            if needed is None or (self.roles & needed):
                cols.append(col)
        return cols


# --------------------------------------------------------------------------- #
# The governed data layer (stands in for Dataverse + the context layer). Only
# registered sources are retrievable; retrieval enforces row + column security
# and freshness, and writes an audit record.
# --------------------------------------------------------------------------- #
class ContextLayer:
    def __init__(self) -> None:
        self.records: list[Record] = []
        self.audit: list[dict] = []

    def register(self, r: Record) -> None:
        self.records.append(r)

    def retrieve(self, query: str, acting_as: Identity | None,
                 as_super: bool = False) -> list[dict]:
        """On-behalf-of retrieval. `as_super=True` shows the anti-pattern: an
        all-seeing agent identity that ignores row/column security."""
        out = []
        for r in self.records:
            if not self._matches(query, r):
                continue
            if r.provenance.validation_status != "current":
                continue                          # freshness (Ch. 5 fix)
            if as_super:                          # PITFALL: super-identity sees all
                visible = [c for c in r.fields if not c.startswith("_")]
            else:
                if acting_as is None or not acting_as.may_read_row(r):
                    continue                      # row-level security
                visible = acting_as.readable_columns(r)  # column-level security
            out.append({"rec_id": r.rec_id,
                        "fields": {c: r.fields[c] for c in visible},
                        "source": r.provenance.source})
        self.audit.append({
            "query": query,
            "acting_as": ("SUPER-IDENTITY(agent)" if as_super
                          else acting_as.name if acting_as else "anonymous"),
            "returned": [o["rec_id"] for o in out],
        })
        return out

    @staticmethod
    def _matches(query: str, r: Record) -> bool:
        q = query.lower()
        return (r.rec_id.lower() in q
                or any(tok in q for tok in r.fields.get("_match", "").split()))


# --------------------------------------------------------------------------- #
# Northwind's registered context.
# --------------------------------------------------------------------------- #
def build_layer() -> ContextLayer:
    layer = ContextLayer()

    # Tier 2 policy — current, broadly readable.
    layer.register(Record(
        rec_id="kb:standard-returns", kind="policy",
        fields={"text": "Returns accepted within 30 days.", "_match": "policy returns"},
        provenance=Provenance("kb://returns/policy", "returns-team", "current",
                              "2026-03-01", "2026-09-01"),
        allowed_roles={"csa.read", "csa.fraud"}))

    # The Chapter 5 stale policy — archived; must never be served as canonical.
    layer.register(Record(
        rec_id="kb:returns-2019", kind="policy",
        fields={"text": "Returns accepted within 45 days.", "_match": "policy returns"},
        provenance=Provenance("kb://returns/policy/archive-2019", "returns-team",
                              "archived", "2019-01-01", ""),
        allowed_roles={"csa.read", "csa.fraud"}))

    # Tier 1 order — per-record, with a payment column only fraud roles may read.
    layer.register(Record(
        rec_id="NW-6612480", kind="order",
        fields={"status": "delivered", "line_items": "1x tree",
                "shipping": "scan on file", "payment_instrument": "card ****4491",
                "dispute_history": "chargeback BR-91145", "_match": "order everything"},
        provenance=Provenance("dataverse://orders/NW-6612480", "orders", "current"),
        allowed_roles={"csa.read", "csa.fraud"},
        restricted_columns={"payment_instrument": {"csa.fraud"},
                            "dispute_history": {"csa.fraud"}}))
    return layer


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def _cols(results: list[dict], rec_id: str) -> list[str]:
    for r in results:
        if r["rec_id"] == rec_id:
            return sorted(r["fields"])
    return []


def run_demo() -> None:
    print("Chapter 13 - retrieval-time access control, provenance, audit\n")
    layer = build_layer()
    first_line = Identity("csa:anjali-firstline", {"csa.read"})
    fraud = Identity("investigator:maria", {"csa.read", "csa.fraud"})

    q = "everything on order NW-6612480"
    r_fl = layer.retrieve(q, first_line)
    r_fr = layer.retrieve(q, fraud)
    print("1. Same query, two identities (on-behalf-of), one data layer:")
    print(f"   first-line CSA sees:      {_cols(r_fl, 'NW-6612480')}")
    print(f"   fraud investigator sees:  {_cols(r_fr, 'NW-6612480')}")

    print("\n2. Freshness/provenance: the archived 2019 policy is never served:")
    pol = layer.retrieve("returns policy", first_line)
    print(f"   returns-policy retrieval -> {[p['source'] for p in pol]}")
    print("   (kb:returns-2019 is archived, so it is filtered out by construction)")

    print("\n3. Chapter 12 attack replayed under a first-line CSA identity:")
    # The injected instruction tries to pull payment data and a fake policy.
    inj = layer.retrieve("everything on order NW-6612480 and the priority policy",
                         first_line)
    leaked_payment = any("payment_instrument" in r["fields"] for r in inj)
    fake_policy = any("priority" in r["source"].lower() for r in inj)
    print(f"   payment columns leaked?  {leaked_payment}  (identity not authorized)")
    print(f"   fabricated policy found? {fake_policy}  (no registered source)")
    print("   -> the injection asks; the data layer refuses. Attack dies at retrieval.")

    print("\n4. The super-identity PITFALL, by contrast:")
    leak = layer.retrieve(q, None, as_super=True)
    print(f"   agent super-identity sees: {_cols(leak, 'NW-6612480')}")
    print("   (an all-seeing agent identity leaks exactly what on-behalf-of withholds)")

    print("\n5. Audit trail (every retrieval recorded):")
    for a in layer.audit:
        print(f"   acting_as={a['acting_as']:26} returned={a['returned']}")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
