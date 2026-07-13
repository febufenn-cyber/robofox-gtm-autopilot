# ADR-0008: Position snapshots are derived artifacts

## Decision

A position snapshot is generated from canonical ledger records for a named product and `as_of` time. It is never edited as the source of truth.

## Reason

A snapshot is an evaluation of the board, not the board itself. Treating it as canonical would hide changed evidence, staleness, and contradictions.

## Consequences

Snapshots include their input record identifiers, generation time, unresolved conflicts, stale records, assumptions, and unknown dimensions.
