# Phase 4 Controlled Execution Policy

## Boundary

Phase 4 builds and tests a side-effect gateway, but the released implementation is simulator-only. It contains no network client, credential loader, live endpoint, or production adapter. `LIVE` execution is not a valid mode.

## Exact authority

Every simulator execution and rollback requires an exact, expiring, single-use approval bound to the workspace, envelope, adapter, mode, content hash, target count, maximum spend, currency, and payload hash. The agent may prepare a manifest but cannot approve it.

## Idempotency and ambiguity

Each envelope has one unique idempotency key. Replays fail closed. An ambiguous adapter response is never converted to success and contributes to the circuit breaker.

## Canary and blast radius

A multi-record batch requires a matching one-record successful canary from the same experiment, action, adapter, and content hash within 24 hours. Adapter batch and hourly rate limits are deterministic.

## Circuit breakers

Three consecutive `FAILURE` or `AMBIGUOUS` results open the adapter circuit. An open circuit blocks further execution until a separately reviewed future recovery mechanism exists.

## Rollback

Reversible adapters must pre-register a rollback strategy. Irreversible adapters may not claim rollback. Rollback creates a compensating immutable record; it never deletes the original result.

## Privacy

Execution targets are pseudonymous `TGT-*` keys. Direct names, email addresses, phone numbers, addresses, tokens, and secrets are prohibited from envelopes and public fixtures.

## Fail closed

Unknown adapters, live mode, spend above zero, mismatched approvals, expired approvals, stale canaries, duplicate idempotency keys, partial policy state, kill switch, external-execution enablement, rate overflow, and integrity failure all block the operation.
