#!/usr/bin/env python3
"""
The assembled reference architecture — companion code for Chapter 15,
"Reference Architectures on Azure and Power Platform."

This is the book's promise kept, in code: it does NOT re-implement anything. It
COMPOSES the prior chapters' runnable modules into one governed contact flow, and
it prints the three architectures as component -> chapter maps (the chapter's
signature device). Every component traces to the chapter that taught it; if a
component can't, it doesn't belong.

The end-to-end run wires together three prior chapters' real code:
  * Ch. 14 (ch14-evaluation)            -> the eval gate that must pass to deploy
  * Ch. 13 (dataverse-retrieval-acl)    -> governed, on-behalf-of retrieval
  * Ch. 10 (minimal-orchestrator)       -> the triage->resolution->approval->QA flow

Everything is deterministic and stdlib-only, so the assembly verifies offline.

    python main.py            # or --demo
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys


# --------------------------------------------------------------------------- #
# Compose prior chapters' modules by loading them from their folders. We do NOT
# duplicate their code — we import and run it, which is the whole point of an
# assembly. Distinct module names avoid the shared `main` collision.
# --------------------------------------------------------------------------- #
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(mod_name: str, rel_path: str):
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {rel_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod          # required so @dataclass can resolve types
    spec.loader.exec_module(mod)
    return mod


def load_components():
    return {
        "ch10": _load("ch10_orchestrator",
                      "ch10-orchestration/minimal-orchestrator/main.py"),
        "ch13": _load("ch13_governed_retrieval",
                      "ch13-governance/dataverse-retrieval-acl/main.py"),
        "ch14": _load("ch14_evaluation", "ch14-evaluation/main.py"),
    }


# --------------------------------------------------------------------------- #
# The three architectures as component -> (operation, chapter) maps. This is the
# signature device: a build audit where every box names its operation and origin.
# --------------------------------------------------------------------------- #
ARCHITECTURES = {
    "1. Single-agent grounded copilot": [
        ("Altitude-calibrated system prompt", "authored context", "Ch. 4"),
        ("Dataverse grounding (Tier 1)", "select", "Ch. 5"),
        ("SharePoint grounding (Tier 2)", "select", "Ch. 5"),
        ("Topics (deterministic promises)", "-", "Ch. 10"),
        ("Generative answers (long tail)", "-", "Ch. 10"),
        ("Human-confirmed writeback", "-", "Ch. 7"),
    ],
    "2. Multi-agent operations system": [
        ("Triage / resolution / QA isolation", "isolate", "Ch. 9"),
        ("Agent Framework orchestration", "-", "Ch. 10"),
        ("Foundry Agent Service runtime", "-", "Ch. 10"),
        ("Structured handoffs", "isolate", "Ch. 9"),
        ("Foundry IQ shared retrieval", "select", "Ch. 5"),
        ("Toolboxes shared tool registry", "-", "Ch. 7"),
        ("Agent memory", "write", "Ch. 6"),
        ("Compaction / tool-result clearing", "compress", "Ch. 8"),
        ("Long-horizon continuity stack", "write+compress", "Ch. 11"),
    ],
    "3. Governed enterprise platform": [
        ("Everything in Architecture 2", "all four", "Ch. 4-11"),
        ("Retrieval-time access control", "select (governed)", "Ch. 13"),
        ("Provenance-carrying knowledge", "select+write", "Ch. 13"),
        ("Entra ID / on-behalf-of identity", "-", "Ch. 13"),
        ("Purview audit + DLP + isolation", "-", "Ch. 13"),
        ("Tenant-wide agent inventory", "-", "Ch. 13"),
        ("Per-subsystem golden-set evals", "-", "Ch. 14"),
        ("Full-flow tracing + improvement loop", "-", "Ch. 14"),
    ],
}


def print_architectures() -> None:
    for name, components in ARCHITECTURES.items():
        print(f"\n{name}")
        for comp, op, ch in components:
            print(f"   {comp:38} {op:18} {ch}")


# --------------------------------------------------------------------------- #
# The assembled governed contact: one request through Architecture 3, composed
# from the three prior chapters' real modules, annotated by source chapter.
# --------------------------------------------------------------------------- #
def run_assembled_contact(mods) -> dict:
    ch10, ch13, ch14 = mods["ch10"], mods["ch13"], mods["ch14"]
    trace: list[str] = []

    # 1. Eval gate (Ch. 14): golden-set retrieval eval must pass to deploy.
    score, _ = ch14.retrieval_eval(ch14.GOLDEN_SET, ch14.build_corpus())
    trace.append(f"[eval gate    | Ch.14] golden-set retrieval eval: {score:.0%} "
                 f"-> {'deploy allowed' if score == 1.0 else 'BLOCKED'}")

    # 2. Governed retrieval (Ch. 13): on-behalf-of the operator, row/col-scoped.
    layer = ch13.build_layer()
    operator = ch13.Identity("csa:first-line", {"csa.read"})
    hits = layer.retrieve("everything on order NW-6612480", operator)
    cols = sorted(hits[0]["fields"]) if hits else []
    trace.append(f"[retrieval    | Ch.13] on-behalf-of {operator.name}: "
                 f"columns={cols}")

    # 3. Orchestration (Ch. 10): triage -> resolution -> approval -> QA.
    wf = ch10.build_workflow()
    state = {"disclosure_given": True, "approved": True, "approver": "lead:ravi"}
    wf.run(state)
    trace.append(f"[orchestration| Ch.10] flow complete; refund issued "
                 f"{state['refund_issued_count']}x; qa={state['qa_verdict']}")

    # 4. Diagnosis (Ch. 14): a sampled failure classified by the rubric.
    sig = ch14.FailureSignals(False, False, False, False)  # right context absent
    trace.append(f"[diagnosis    | Ch.14] sampled failure classified: "
                 f"{ch14.classify_failure(sig)}")

    return {"score": score, "columns": cols,
            "refund_count": state["refund_issued_count"], "trace": trace}


def run_demo() -> None:
    print("Chapter 15 - the assembled reference architecture")
    print("\nThree architectures, every component traced to its chapter:")
    print_architectures()

    print("\n" + "=" * 68)
    print("Architecture 3, assembled from prior chapters' REAL modules:\n")
    result = run_assembled_contact(load_components())
    for line in result["trace"]:
        print("   " + line)
    print("\n   Nothing here is re-implemented: the eval, the governed retrieval,")
    print("   and the orchestration are the Ch. 14 / Ch. 13 / Ch. 10 modules,")
    print("   composed. That composition IS the reference architecture.")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--demo"
    if mode in ("--demo", ""):
        run_demo()
    else:
        print(f"unknown mode: {mode}\nusage: python main.py [--demo]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
