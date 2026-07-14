---
name: execution-gateway
description: Prepare and inspect exact Phase 4 simulator execution envelopes with canary, idempotency, rate, rollback, and circuit controls. Do NOT use live credentials, contact anyone, mutate live systems, spend money, approve actions, or bypass the kill switch.
---

# Execution Gateway

1. Bind the envelope to one Phase 3 experiment.
2. Use pseudonymous target keys only.
3. Require one target for a canary; require a successful matching canary for a batch.
4. Keep mode `SIMULATOR`, spend zero, and `external_execution` false.
5. Generate an exact approval manifest for founder review.
6. Record immutable result and approval consumption atomically.
7. Stop on ambiguity, replay, rate overflow, circuit open, or state mismatch.
