# ADR-0011: Deterministic bounded arbitration

## Decision

Eligibility, exposure gates, scoring, and tie-breaking are versioned deterministic code. Model prose cannot alter them.

## Consequences

Decisions are replayable and auditable. Ordinal scores guide comparison but are never represented as probabilities.
