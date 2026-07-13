# ADR-0007: Use SQLite for the private truth ledger

## Decision

Phase 1 uses a zero-dependency SQLite database located under the private workspace.

## Reason

A solo-founder system needs transactions, constraints, portability, backups, and simple local inspection more than distributed infrastructure.

## Consequences

The engine ships migrations and CLI tooling but no database file. WAL mode, foreign keys, schema versioning, and parameterized queries are mandatory.
