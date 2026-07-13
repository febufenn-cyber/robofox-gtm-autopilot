# Phase 1 — Truth Layer

Phase 1 gives Robofox GTM Autopilot a canonical, private, reconstructable view of the commercial position. It does not automate outreach, CRM writes, ad changes, publishing, or spending.

## Design goals

- Preserve source provenance and observation time.
- Separate observations, inferences, and assumptions.
- Never overwrite history; corrections supersede earlier records.
- Distinguish missing data from a measured zero.
- Detect contradictory active claims.
- Mark stale evidence using explicit validity or age rules.
- Keep restricted data in the private workspace and out of generated summaries.
- Generate position snapshots as derived artifacts, never as the source of truth.

## Increment plan

1. **Contracts:** policies, schemas, dimensions, and validation.
2. **Ledger:** zero-dependency SQLite store in the private workspace.
3. **Position engine:** staleness, contradiction, and snapshot generation.
4. **End-to-end gate:** bootstrap integration, adversarial tests, and CI.

## Canonical evidence states

`VERIFIED`, `OBSERVED`, `INFERRED`, `ASSUMED`, `STALE`, `CONFLICTED`, `UNKNOWN`, and `PROHIBITED`.

`STALE` and `CONFLICTED` may be derived at read time. Raw records retain the state assigned when captured.

## Truth hierarchy

1. Current first-party measured outcomes
2. Current direct customer observations
3. Current internal operational observations
4. Local or segment-specific external evidence
5. General benchmarks
6. Explicit assumptions

Higher-ranked evidence does not silently delete lower-ranked evidence. It changes which claim is preferred in a derived position snapshot.

## Private workspace

The future ledger lives below `ROBOFOX_GTM_WORKSPACE`, outside this public engine. Public files contain only contracts, code, and synthetic tests.
