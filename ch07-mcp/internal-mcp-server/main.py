#!/usr/bin/env python3
"""
Internal MCP server for OrderCore — companion code for Chapter 7,
"Tools, Function-Calling, and MCP."

This wraps Northwind's fictional legacy order-management system, OrderCore,
behind a small Model Context Protocol (MCP) server. It demonstrates the four
design decisions the chapter argues for:

  1. Expose the FEWEST operations that do the job — five tools, not OrderCore's
     forty. Everything not exposed cannot be misused, cannot consume the context
     budget, and cannot be selected in error.
  2. Scope access by ROLE — seniority tiers (first-line / senior / lead) survive
     the move to tools; the agent inherits the operator's permissions, not the
     union of everyone's.
  3. Separate READ from WRITE — read tools are free to retry; write tools change
     the world. The distinction is visible in names, enforced in permissions,
     and stated in each tool's description.
  4. Gate consequential writes behind HUMAN CONFIRMATION — `issue_refund` only
     proposes; a human confirms before money moves. (Canon for Ch. 10 and 13.)

It is deliberately DEPENDENCY-FREE: it speaks MCP's JSON-RPC 2.0 wire protocol
over stdio using only the Python standard library, so it runs offline with no
`pip install`. A production server would use the official `mcp` Python SDK (or
the C#/TypeScript SDKs) rather than hand-rolling the transport; the tool
*designs* below are what carry over, not this transport code.

Run the guided demonstration (no MCP client needed):

    python main.py --demo

Run as a real MCP stdio server (connect an MCP client to it):

    ORDERCORE_CSA_ROLE=csa.write python main.py --serve
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


# --------------------------------------------------------------------------- #
# Role model: seniority tiers. A caller holds one role; higher tiers inherit
# the permissions of lower ones. The gateway (not the tool arguments) supplies
# the caller's identity — here modelled by the ORDERCORE_CSA_ROLE env var for
# the --serve path, and passed explicitly in --demo.
# --------------------------------------------------------------------------- #
ROLE_RANK = {
    "csa.read": 1,    # first-line CSA: look up orders, check status, add notes
    "csa.write": 2,   # senior CSA (e.g. Anjali): also issue replacements
    "csa.refund": 3,  # lead: also propose refunds (which then require a human yes)
}


def caller_may(caller_role: str, required_role: str) -> bool:
    return ROLE_RANK.get(caller_role, 0) >= ROLE_RANK[required_role]


class PermissionError_(Exception):
    """Raised when a caller's role is below a tool's required role."""


class ConfirmationRequired(Exception):
    """Not an error: signals that a write is pending human confirmation."""

    def __init__(self, proposal: dict[str, Any]):
        super().__init__("human confirmation required")
        self.proposal = proposal


# --------------------------------------------------------------------------- #
# Mock OrderCore backend. In reality this is the ugly adapter over OrderCore's
# database (reads) and scriptable batch interface (writes) — quarantined here
# behind clean methods so the MCP tools never see the legacy mess.
# --------------------------------------------------------------------------- #
class OrderCore:
    def __init__(self) -> None:
        self._orders: dict[str, dict[str, Any]] = {
            "NW-4820193": {
                "status": "delivered",
                "region": "UK",
                "fulfilment": "delivered 2026-07-14",
                "items": [{"sku": "BLND-9", "name": "Countertop blender", "qty": 1}],
                "value": 89.00,
                "notes": [],
            },
            "NW-5591027": {
                "status": "in_transit",
                "region": "NA",
                "fulfilment": "out for delivery",
                "items": [{"sku": "HDPH-2", "name": "Wireless headphones", "qty": 1}],
                "value": 149.00,
                "notes": [],
            },
        }
        self.audit: list[dict[str, Any]] = []

    # -- reads ------------------------------------------------------------- #
    def get_order(self, order_id: str) -> dict[str, Any]:
        order = self._orders.get(order_id)
        if order is None:
            raise KeyError(f"unknown order id: {order_id}")
        return {"order_id": order_id, "status": order["status"],
                "region": order["region"], "items": order["items"],
                "value": order["value"]}

    def get_fulfilment(self, order_id: str) -> dict[str, Any]:
        order = self._orders.get(order_id)
        if order is None:
            raise KeyError(f"unknown order id: {order_id}")
        return {"order_id": order_id, "fulfilment": order["fulfilment"]}

    # -- writes ------------------------------------------------------------ #
    def add_note(self, order_id: str, note: str) -> dict[str, Any]:
        self._orders[order_id]["notes"].append(note)
        return {"order_id": order_id, "note_count": len(self._orders[order_id]["notes"])}

    def issue_replacement(self, order_id: str, reason: str) -> dict[str, Any]:
        rep_id = "NW-" + uuid.uuid4().hex[:7].upper()
        return {"replacement_order_id": rep_id, "for_order": order_id, "reason": reason}

    def commit_refund(self, order_id: str, amount: float, reason: str) -> dict[str, Any]:
        ref_id = "RF-" + uuid.uuid4().hex[:7].upper()
        return {"refund_id": ref_id, "order_id": order_id, "amount": amount,
                "reason": reason, "committed": True}

    def order_value(self, order_id: str) -> float:
        return float(self._orders[order_id]["value"])


# --------------------------------------------------------------------------- #
# Tool registry. Each tool is written the way Chapter 7 argues for: the
# description is CONTEXT the model reads (it says what the tool returns, when to
# reach for it, and — crucially — what it will NOT do), and the role scope is a
# first-class property, not an afterthought.
# --------------------------------------------------------------------------- #
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    required_role: str
    is_write: bool
    handler: Callable[..., dict[str, Any]]


class OrderCoreServer:
    def __init__(self, backend: OrderCore) -> None:
        self.backend = backend
        # Pending refund proposals, keyed by a confirmation token. A refund
        # never moves money on the model's say-so: issue_refund parks a proposal
        # here and returns pending; a human commits it via confirm_refund.
        self._pending_refunds: dict[str, dict[str, Any]] = {}
        self.tools: dict[str, Tool] = {}
        self._register_tools()

    # -- registration ------------------------------------------------------ #
    def _register_tools(self) -> None:
        order_id_prop = {
            "order_id": {"type": "string",
                         "description": "The Northwind order ID, e.g. 'NW-4820193'."}
        }

        self._add(Tool(
            name="lookup_order",
            description=(
                "Look up a Northwind order by its order ID and return status, "
                "line items, ship-to region, and order value. Use this when a "
                "customer asks about the status or contents of a specific existing "
                "order. Read-only: this tool never modifies an order. It cannot "
                "issue refunds, cancel shipments, or change addresses — those are "
                "separate, permissioned tools."),
            input_schema={"type": "object", "properties": dict(order_id_prop),
                          "required": ["order_id"]},
            required_role="csa.read", is_write=False,
            handler=lambda a: self.backend.get_order(a["order_id"]),
        ))

        self._add(Tool(
            name="check_fulfilment",
            description=(
                "Return the current fulfilment/delivery state of a specific order "
                "(e.g. 'out for delivery', 'delivered 2026-07-14'). Use this when a "
                "customer asks *where* their order is. Read-only: does not modify "
                "anything."),
            input_schema={"type": "object", "properties": dict(order_id_prop),
                          "required": ["order_id"]},
            required_role="csa.read", is_write=False,
            handler=lambda a: self.backend.get_fulfilment(a["order_id"]),
        ))

        self._add(Tool(
            name="add_order_note",
            description=(
                "Append a free-text note to an order's history for the record. Use "
                "this to document what was discussed or promised. Low-risk write: "
                "it annotates but does not change order state, fulfilment, or money."),
            input_schema={"type": "object",
                          "properties": {**order_id_prop,
                                         "note": {"type": "string",
                                                  "description": "The note text to append."}},
                          "required": ["order_id", "note"]},
            required_role="csa.read", is_write=True,
            handler=lambda a: self.backend.add_note(a["order_id"], a["note"]),
        ))

        self._add(Tool(
            name="issue_replacement",
            description=(
                "Create a replacement order for an existing order, e.g. for a "
                "defective item under warranty. Use this only after confirming the "
                "order and the reason. Write: this creates a new order. Requires "
                "senior-CSA permission."),
            input_schema={"type": "object",
                          "properties": {**order_id_prop,
                                         "reason": {"type": "string",
                                                    "description": "Why a replacement is warranted."}},
                          "required": ["order_id", "reason"]},
            required_role="csa.write", is_write=True,
            handler=lambda a: self.backend.issue_replacement(a["order_id"], a["reason"]),
        ))

        self._add(Tool(
            name="issue_refund",
            description=(
                "PROPOSE a refund against an order. This tool does NOT move money "
                "on its own: it returns a pending proposal that a human must confirm "
                "with confirm_refund before it commits. Use this when a refund is "
                "warranted; expect a human approval step. Requires lead permission."),
            input_schema={"type": "object",
                          "properties": {**order_id_prop,
                                         "amount": {"type": "number",
                                                    "description": "Refund amount in the order's currency."},
                                         "reason": {"type": "string",
                                                    "description": "Why a refund is warranted."}},
                          "required": ["order_id", "amount", "reason"]},
            required_role="csa.refund", is_write=True,
            handler=self._propose_refund,
        ))

        self._add(Tool(
            name="confirm_refund",
            description=(
                "Commit a refund that issue_refund proposed, identified by its "
                "confirmation token. This is the HUMAN approval step — it should be "
                "invoked by a person's explicit yes, not autonomously by the model. "
                "Commits the refund and writes the audit record."),
            input_schema={"type": "object",
                          "properties": {"confirmation_token": {"type": "string",
                                         "description": "Token from the issue_refund proposal."},
                                         "approver": {"type": "string",
                                         "description": "Identity of the human approving."}},
                          "required": ["confirmation_token", "approver"]},
            required_role="csa.refund", is_write=True,
            handler=self._commit_refund,
        ))

    def _add(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    # -- the refund confirmation gate -------------------------------------- #
    def _propose_refund(self, args: dict[str, Any]) -> dict[str, Any]:
        token = uuid.uuid4().hex
        proposal = {"confirmation_token": token, "order_id": args["order_id"],
                    "amount": float(args["amount"]), "reason": args["reason"]}
        self._pending_refunds[token] = proposal
        # Signal to the caller that money has NOT moved — a human must confirm.
        raise ConfirmationRequired(proposal)

    def _commit_refund(self, args: dict[str, Any]) -> dict[str, Any]:
        token = args["confirmation_token"]
        proposal = self._pending_refunds.pop(token, None)
        if proposal is None:
            raise KeyError("unknown or already-used confirmation token")
        result = self.backend.commit_refund(
            proposal["order_id"], proposal["amount"], proposal["reason"])
        result["approved_by"] = args["approver"]
        return result

    # -- dispatch ---------------------------------------------------------- #
    def call_tool(self, name: str, args: dict[str, Any], caller_role: str) -> dict[str, Any]:
        tool = self.tools.get(name)
        if tool is None:
            raise KeyError(f"unknown tool: {name}")
        if not caller_may(caller_role, tool.required_role):
            raise PermissionError_(
                f"caller role '{caller_role}' may not call '{name}' "
                f"(requires '{tool.required_role}')")
        self.backend.audit.append({
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "caller_role": caller_role, "tool": name,
            "write": tool.is_write, "args": args})
        return tool.handler(args)

    def list_tools(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description,
                 "inputSchema": t.input_schema} for t in self.tools.values()]


# --------------------------------------------------------------------------- #
# MCP transport: newline-delimited JSON-RPC 2.0 over stdio. Implements just
# enough of the protocol to be a real MCP server: initialize, tools/list,
# tools/call. The caller's role for a --serve session comes from the gateway;
# here we read it from ORDERCORE_CSA_ROLE.
# --------------------------------------------------------------------------- #
PROTOCOL_VERSION = "2025-06-18"


def _result(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def serve_stdio(server: OrderCoreServer, caller_role: str) -> None:
    out = sys.stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            out.write(json.dumps(_error(None, -32700, "parse error")) + "\n")
            out.flush()
            continue

        method = msg.get("method")
        req_id = msg.get("id")

        # Notifications (no id) get no response.
        if method == "notifications/initialized":
            continue

        if method == "initialize":
            resp = _result(req_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ordercore-internal", "version": "0.1.0"}})
        elif method == "tools/list":
            resp = _result(req_id, {"tools": server.list_tools()})
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name", "")
            args = params.get("arguments", {}) or {}
            try:
                data = server.call_tool(name, args, caller_role)
                content = [{"type": "text", "text": json.dumps(data)}]
                resp = _result(req_id, {"content": content, "isError": False})
            except ConfirmationRequired as c:
                content = [{"type": "text",
                            "text": "PENDING HUMAN CONFIRMATION: " + json.dumps(c.proposal)}]
                resp = _result(req_id, {"content": content, "isError": False})
            except (PermissionError_, KeyError) as e:
                content = [{"type": "text", "text": f"error: {e}"}]
                resp = _result(req_id, {"content": content, "isError": True})
        else:
            resp = _error(req_id, -32601, f"method not found: {method}")

        out.write(json.dumps(resp) + "\n")
        out.flush()


# --------------------------------------------------------------------------- #
# --demo: an in-process narrative that exercises every design decision so you
# can see role scoping, read/write separation, and the refund gate work without
# wiring up an MCP client. This is what `python main.py` (or `--demo`) runs.
# --------------------------------------------------------------------------- #
def run_demo() -> None:
    backend = OrderCore()
    server = OrderCoreServer(backend)

    def attempt(role: str, tool: str, **args: Any) -> None:
        try:
            result = server.call_tool(tool, args, role)
            print(f"  [{role:10}] {tool:18} -> {json.dumps(result)}")
        except ConfirmationRequired as c:
            print(f"  [{role:10}] {tool:18} -> PENDING human confirmation: "
                  f"{json.dumps(c.proposal)}")
        except PermissionError_ as e:
            print(f"  [{role:10}] {tool:18} -> DENIED: {e}")
        except KeyError as e:
            print(f"  [{role:10}] {tool:18} -> error: {e}")

    print("Northwind OrderCore MCP server - Chapter 7 demonstration\n")

    print("1. Reads are open to any authenticated CSA (first-line and up):")
    attempt("csa.read", "lookup_order", order_id="NW-4820193")
    attempt("csa.read", "check_fulfilment", order_id="NW-5591027")
    attempt("csa.read", "add_order_note", order_id="NW-4820193",
            note="Customer reports blender fault; warranty applies.")

    print("\n2. Role scope: a first-line CSA CANNOT issue a replacement...")
    attempt("csa.read", "issue_replacement", order_id="NW-4820193",
            reason="Defective under warranty")
    print("   ...but a senior CSA (Anjali's tier) can:")
    attempt("csa.write", "issue_replacement", order_id="NW-4820193",
            reason="Defective under warranty")

    print("\n3. issue_refund never moves money on the model's say-so.")
    print("   Even a lead only gets a PENDING proposal from the tool call:")
    proposal = None
    try:
        server.call_tool("issue_refund",
                         {"order_id": "NW-5591027", "amount": 149.00,
                          "reason": "Item never delivered"}, "csa.refund")
    except ConfirmationRequired as c:
        proposal = c.proposal
        print(f"  [csa.refund ] issue_refund       -> PENDING: {json.dumps(proposal)}")

    print("\n   A human then confirms with the token - money moves only now:")
    assert proposal is not None
    attempt("csa.refund", "confirm_refund",
            confirmation_token=proposal["confirmation_token"], approver="lead:ravi")

    print("\n   And a senior CSA still cannot reach the refund path at all:")
    attempt("csa.write", "issue_refund", order_id="NW-5591027",
            amount=149.00, reason="Item never delivered")

    print("\n4. Every call - allowed or denied - is audited at the gateway:")
    for entry in backend.audit:
        kind = "WRITE" if entry["write"] else "read "
        print(f"  {entry['at']}  {entry['caller_role']:10}  {kind}  {entry['tool']}")

    print(f"\nExposed {len(server.tools)} tools (OrderCore has ~40 operations); "
          "the rest are deliberately not reachable.")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode == "--serve":
        role = os.environ.get("ORDERCORE_CSA_ROLE", "csa.read")
        serve_stdio(OrderCoreServer(OrderCore()), role)
    elif mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo | --serve]",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
