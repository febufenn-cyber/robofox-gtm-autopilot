# ADR-0012: No-move is a valid result

## Decision

The engine may return `NO_MOVE`, `NEEDS_EVIDENCE`, or `BLOCKED_CONFLICT` instead of selecting a candidate.

## Consequences

The system does not manufacture action when the position is unclear, exposure is excessive, or all moves fail hard gates.
