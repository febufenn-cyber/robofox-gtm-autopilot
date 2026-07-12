# ADR-0003: Connectors are read-only during Phase 0

## Decision

HubSpot and Meta integrations are used for analysis only. Connector write capability, when technically present, is outside the permitted action set.

## Consequences

Analysis sessions use aggregate-first retrieval. A future mediation layer must enforce method allowlists before any write profile can be considered.
