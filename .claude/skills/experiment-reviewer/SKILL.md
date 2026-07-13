---
name: experiment-reviewer
description: Deterministically evaluate a Phase 3 experiment and prepare an immutable outcome and learning record. Do NOT use to fabricate observations, change criteria, ignore minimum execution, suppress safety stops, approve the outcome, or execute the next action.
---

# Experiment Reviewer

1. Verify experiment integrity and current state.
2. Recompute every success and kill criterion from recorded observations.
3. Preserve `INSUFFICIENT_DATA` when minimum sample size is absent.
4. Apply minimum-execution and hard-stop rules exactly.
5. Prepare `SUCCESS`, `FAILED`, `SAFETY_STOP`, or `CANCELLED` with evidence IDs, learning, belief updates, and one next action.
6. Finalize only through exact approval; outcome and terminal transition must commit atomically.

The final learning feeds later evidence collection. It does not rewrite the truth ledger by itself.
