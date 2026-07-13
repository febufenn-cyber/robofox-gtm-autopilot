# ADR-0015: Derive experiment state from events

## Decision

Store immutable transition events and derive current state instead of updating a mutable status column.

## Consequences

The complete lifecycle is reconstructable at any time, and no silent status rewrite can erase how the experiment reached its outcome.
