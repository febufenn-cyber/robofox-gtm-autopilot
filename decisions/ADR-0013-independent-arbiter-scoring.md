# ADR-0013: Independent arbiter scores candidates

## Decision

Planner-authored candidate records contain no ranking scores. After blind critiques are complete, an independent `ARBITER` assessment supplies the ordinal score and justification for each candidate.

## Consequences

A proposal cannot grade itself. The deterministic engine still applies hard gates, weights, penalties, and tie-breaking; the assessor provides bounded judgment but cannot override policy.
