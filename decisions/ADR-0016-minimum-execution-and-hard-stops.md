# ADR-0016: Separate minimum execution from hard stops

## Decision

Ordinary failure requires minimum execution, while pre-registered kill criteria and safety hard stops may terminate earlier.

## Consequences

The system avoids killing good channels because of weak execution while still stopping trust, consent, or safety harm immediately.
