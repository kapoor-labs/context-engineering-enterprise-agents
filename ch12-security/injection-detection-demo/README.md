# Injection Detection Demo

> Accompanies the book — Chapter 12, "Context and Memory Poisoning."

## DEFENSIVE ONLY

This folder contains **no working exploits, no novel attack construction, and no
step-by-step attack recipes** — only defender-side code. The single attack-shaped
string in it is the canonical "ignore previous instructions" example that appears
in essentially every prompt-injection paper, used purely as a **test fixture** for
the detector. Do not add real payloads here.

## What this demonstrates

Two layers of the chapter's defense-in-depth, made runnable:

1. **Spotlighting / untrusted-content marking** — `mark_untrusted()` wraps anything
   the agent ingests from the world (retrieved docs, tool results, extracted
   attachments) in an explicit boundary so the model can tell *data to reason
   about* from *instructions to obey*, reasserting Chapter 4's
   data-not-instructions line at the input layer. Forged close-markers inside the
   content are neutralized so content can't escape its own boundary.
2. **Injection-shaped detection + a memory-write validation gate** —
   `flag_injection_shaped()` is a partial first-sieve detector over
   publicly-documented pattern *classes* (it flags shapes; novel phrasings pass —
   that's the point of layering). `MemoryWriteGate` refuses to commit a memory
   write that lacks provenance, is injection-shaped, or (for a durable procedural
   rule) lacks human approval — the Chapter 6 review gate seen as a security
   control against a planted "correction."

Every layer here is deliberately **partial**. The demo and the code say so
repeatedly, because the chapter's honest conclusion is that depth lowers risk but
does not reach zero.

## Dependency-free by design

Stdlib-only; runs offline with no API key and no `pip install`.

## Prerequisites

- Python 3.11+ (developed and verified on 3.14).
- No third-party packages.

## How to run

```bash
python main.py                 # the three defensive layers, demonstrated
python -m unittest -v          # the defense tests (10 tests)
```

## Versions

| Component | Version | Last verified |
|---|---|---|
| Python (stdlib only) | 3.11+ (tested 3.14.0) | 2026-07 |

## Scope note

Detection and gating only. The governance machinery that makes memory writes
auditable and reversible (provenance stores, retrieval-time access control) is
motivated here and built in Chapter 13.
