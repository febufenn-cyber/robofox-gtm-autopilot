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

The ledger lives below `ROBOFOX_GTM_WORKSPACE`, outside this public engine. Public files contain only contracts, code, and synthetic tests.

## Ledger commands

Initialize the ledger in the private workspace:

```bash
python3 scripts/truth_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" init
```

Insert a validated JSON record:

```bash
python3 scripts/truth_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" add-source source.json
python3 scripts/truth_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" add-claim claim.json
python3 scripts/truth_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" add-assumption assumption.json
python3 scripts/truth_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" add-metric metric.json
```

Every write requires an exact approved internal action. The CLI has no update, delete, or arbitrary SQL command.

## Position snapshots

Generate a historical or current board-state evaluation from the private ledger:

```bash
python3 scripts/build_position_snapshot.py voice-agents \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  --as-of "2026-07-13T12:00:00+05:30" \
  --stdout
```

The engine:

- resolves only records that existed at the requested `as_of` time
- follows supersession without rewriting history
- distinguishes unknown, stale, conflicted, and supported dimensions
- blocks a value only when multiple current claims disagree
- surfaces stale disagreement without allowing obsolete evidence to paralyse the current position
- excludes `RESTRICTED` and `PROHIBITED` values from generated output
- writes uniquely named, atomic JSON and Markdown artifacts under the private workspace `snapshots/` directory
- records claim, source, and open-assumption IDs for traceability

Position snapshots are derived artifacts. Correct the ledger with a superseding record, then regenerate the snapshot; do not edit the snapshot as evidence.
