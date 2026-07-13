# ADR-0009: Freeze the position before calculation

## Decision

Every strategic decision binds to one canonical Phase 1 snapshot hash. The snapshot cannot refresh during candidate generation, critique, or arbitration.

## Consequences

Inputs are reproducible, candidates cannot cherry-pick a later board state, and changed evidence requires a new decision run.
