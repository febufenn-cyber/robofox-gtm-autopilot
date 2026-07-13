# Phase 1 — Truth Layer

Phase 1 gives Robofox GTM Autopilot a canonical, private, reconstructable view of the commercial position. It does not automate outreach, CRM writes, ad changes, publishing, or spending.

## What Phase 1 establishes

- immutable sources, claims, assumptions, and metrics
- source provenance and timezone-aware observation time
- strict separation between facts, inferences, assumptions, unknowns, stale evidence, conflicts, and prohibited evidence
- a private SQLite ledger with foreign keys, WAL, ordered migrations, and database-level append-only triggers
- historical `as_of` position snapshots that can be rebuilt from canonical records
- conflict and stale-disagreement detection without averaging contradictory evidence away
- automatic exclusion of `RESTRICTED` and `PROHIBITED` values from generated snapshots
- hash-bound, workspace-scoped, expiring, single-use approvals for every ledger mutation
- append-only approval consumption and integrity verification of every canonical record hash

## Evidence states

Raw records use `VERIFIED`, `OBSERVED`, `INFERRED`, `ASSUMED`, `UNKNOWN`, or `PROHIBITED`.

`STALE` and `CONFLICTED` are derived at read time. They never overwrite the state originally captured.

## Truth hierarchy

1. Current first-party measured outcomes
2. Current direct customer observations
3. Current internal operational observations
4. Local or segment-specific external evidence
5. General benchmarks
6. Explicit assumptions

Higher-ranked evidence does not silently delete lower-ranked evidence. It changes which same-value claim is preferred. Multiple different current values remain an unresolved conflict. A stale disagreement is shown without allowing obsolete evidence to block a fresh current value.

## 1. Bootstrap the private workspace

Run this outside the public engine:

```bash
python3 scripts/bootstrap_private_workspace.py ~/private/robofox-gtm-workspace
export ROBOFOX_GTM_WORKSPACE=~/private/robofox-gtm-workspace
```

Bootstrap creates a unique workspace identity and a private `system-state.json` with the kill switch still active. It deliberately does **not** initialize the truth database.

Review the generated files. When you deliberately intend to perform an approved internal truth write, change only the private workspace state from:

```json
"kill_switch": true
```

to:

```json
"kill_switch": false
```

External execution remains disabled.

## 2. Initialize the ledger with exact approval

Prepare the exact initialization action:

```bash
python3 scripts/truth_approval.py \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  prepare initialize_truth_ledger \
  --requested-by Febin \
  --task-id TASK-TRUTH-INIT
```

In a founder-controlled interactive terminal, approve the generated manifest:

```bash
python3 scripts/truth_approval.py \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  approve "$ROBOFOX_GTM_WORKSPACE/approvals/pending/<ACT-ID>.manifest.json" \
  --approved-by Febin
```

Consume that approval exactly once:

```bash
python3 scripts/truth_store.py \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  init \
  --manifest "$ROBOFOX_GTM_WORKSPACE/approvals/pending/<ACT-ID>.manifest.json" \
  --approval "$ROBOFOX_GTM_WORKSPACE/approvals/approved/<APR-ID>.approval.json" \
  --state "$ROBOFOX_GTM_WORKSPACE/system-state.json"
```

## 3. Record one source, claim, assumption, or metric

Prepare one record JSON file that follows the applicable schema. Then create and approve an action bound to that exact file.

Example for a source:

```bash
python3 scripts/truth_approval.py \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  prepare record_truth_source \
  --record source.json \
  --requested-by Febin \
  --task-id TASK-SOURCE-001

python3 scripts/truth_approval.py \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  approve "$ROBOFOX_GTM_WORKSPACE/approvals/pending/<ACT-ID>.manifest.json" \
  --approved-by Febin

python3 scripts/truth_store.py \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  add-source source.json \
  --manifest "$ROBOFOX_GTM_WORKSPACE/approvals/pending/<ACT-ID>.manifest.json" \
  --approval "$ROBOFOX_GTM_WORKSPACE/approvals/approved/<APR-ID>.approval.json" \
  --state "$ROBOFOX_GTM_WORKSPACE/system-state.json"
```

Equivalent commands are `add-claim`, `add-assumption`, and `add-metric`, with action types `record_truth_claim`, `record_truth_assumption`, and `record_truth_metric`.

Any payload, manifest, action, workspace, state, expiry, or identifier change invalidates the approval. The record and approval consumption commit in one transaction. The CLI provides no update, delete, arbitrary SQL, or approval-bypass command.

## 4. Evaluate the board position

Generate a historical or current snapshot:

```bash
python3 scripts/build_position_snapshot.py voice-agents \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  --as-of "2026-07-13T12:00:00+05:30" \
  --stdout
```

The position engine evaluates ten dimensions:

- ICP clarity
- problem urgency
- proof strength
- customer access
- delivery readiness
- unit economics
- founder capacity
- customer trust
- data quality
- current constraint

It resolves only records that existed at `as_of`, follows supersession without rewriting history, preserves an observed zero, rejects future positions, exposes open and overdue assumptions, and writes uniquely named atomic JSON and Markdown files under the private `snapshots/` directory.

Snapshots are derived artifacts. Correct the ledger through a new superseding record and regenerate; never edit a snapshot as evidence.

## 5. Verify integrity

Run the read-only integrity command:

```bash
python3 scripts/truth_store.py \
  --workspace "$ROBOFOX_GTM_WORKSPACE" \
  integrity
```

It checks:

- SQLite structural integrity
- foreign-key consistency
- the complete migration sequence
- required append-only triggers
- canonical hashes for every source, claim, assumption, and metric
- approval-consumption counts

## 6. Verify the public engine

```bash
python3 scripts/verify_phase1.py
python3 -m unittest discover -s tests/phase1 -p 'test_*.py' -v
```

The public repository contains only contracts, code, and synthetic tests. Real customer, contact, pipeline, pricing-negotiation, transcript, experiment, approval, snapshot, and database files remain in the private workspace.

## Approval limitation

The approval is cryptographically hash-bound to exact content, scope, workspace, and expiry. The `approved_by` label is not a cryptographic proof of human identity. Human control depends on the private workspace permissions and the interactive approval terminal. The agent-facing action registry therefore disables and forbids `approve_truth_action`.
