---
name: decision-arbiter
description: Independently assess frozen candidates after blind critiques, run deterministic arbitration, and replay-verify the final decision record. Do NOT use to alter candidates or reviews, change weights, self-approve execution, suppress a no-move result, or perform the chosen action.
---

# Decision Arbiter

1. Confirm all candidates and critiques are frozen and hash-bound.
2. Read all candidates and critiques only after the blind-review stage is complete.
3. Produce exactly one `score-assessment.schema.json` record per candidate.
4. Justify every ordinal score using the frozen board and critique.
5. Use `assessor_role: ARBITER`, `saw_all_candidates: true`, and `saw_critiques: true`.
6. Run `scripts/run_decision_engine.py`.
7. Run `scripts/verify_decision_record.py` on the output.
8. Preserve `NO_MOVE`, `NEEDS_EVIDENCE`, or `BLOCKED_CONFLICT` when returned.

The deterministic engine owns gates, weights, penalties, ranking, and tie-breaking.
