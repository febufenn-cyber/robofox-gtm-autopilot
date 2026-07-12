# ADR-0001: Public engine and private workspace

## Decision

The public repository contains reusable code, schemas, policies, and synthetic examples. Real operating evidence belongs in a separate private workspace outside the engine directory.

## Consequences

The engine remains auditable and reusable. Customer and commercially sensitive information cannot be committed here. The workspace location is configured through `ROBOFOX_GTM_WORKSPACE`.
