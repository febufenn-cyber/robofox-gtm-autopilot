# ADR-0004: Unknown actions are denied

## Decision

Only actions registered in `policies/action-registry.yaml` can be evaluated. Unknown or ambiguous actions are denied.

## Consequences

New capabilities require an explicit policy change and tests rather than being inferred from tool availability.
