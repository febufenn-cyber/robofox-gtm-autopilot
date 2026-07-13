---
name: position-evaluator
description: Validate and freeze the latest Phase 1 commercial-position snapshot before strategic calculation. Do NOT use to invent missing evidence, silently resolve conflicts, update the ledger, or choose a strategic move.
---

# Position Evaluator

1. Run truth-ledger integrity verification when tampering is suspected.
2. Build or select exactly one Phase 1 snapshot.
3. Record its canonical hash, product, `as_of`, current constraint, unknown dimensions, blocking conflicts, and open assumptions.
4. Stop with `BLOCKED_CONFLICT` or `NEEDS_EVIDENCE` when the configured board gates require it.
5. Pass only the frozen file and hash to later roles.

Never replace an unknown with zero and never expose restricted records.
