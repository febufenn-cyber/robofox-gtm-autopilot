# ADR-0006: Canonical observations are immutable

## Decision

Sources, claims, assumptions, and metrics are append-only. Corrections create a new record that references the record it supersedes.

## Reason

Overwriting evidence destroys the move history needed to understand why a decision looked correct at the time.

## Consequences

The ledger needs supersession links, active-record resolution, and audit-friendly timestamps. Storage grows slowly, but every position remains reconstructable.
