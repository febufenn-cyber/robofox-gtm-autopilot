# ADR-0017: Detect experiment collisions

## Decision

Block overlapping experiments on the same product and audience when they change a common dimension, unless an exact isolation waiver names every conflict.

## Consequences

Concurrent tests cannot quietly contaminate attribution. Necessary paired tests must document how audiences or treatments remain isolated.
