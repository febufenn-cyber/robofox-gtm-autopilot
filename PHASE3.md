# Phase 3 — Experiment Operating System

Phase 3 converts one `CHOSEN` Phase 2 move into a bounded, pre-registered experiment. It controls experiment records only; it does not send outreach, modify CRM, change ads, publish content, spend money, or perform the selected move.

## Core guarantees

- The experiment is hash-bound to the chosen Phase 2 decision and candidate.
- Hypothesis, audience, changed dimensions, metrics, minimum execution, success criteria, kill criteria, hard stops, dates, and maximum exposure are fixed before launch.
- State is derived from append-only transitions: `DRAFT → REVIEWED → APPROVED → LIVE ↔ PAUSED → COMPLETED/KILLED`.
- Cash, founder-hour, and signal-time caps are enforced before each execution record.
- A channel is not declared failed before minimum execution unless a pre-registered kill criterion or hard safety stop fires.
- Concurrent experiments changing overlapping dimensions for the same audience and date range are blocked unless an exact isolation waiver names every collision.
- Outcome criteria are recomputed from recorded observations; supplied results cannot override deterministic evaluation.
- Finalization writes the outcome and terminal transition atomically.
- All mutations require exact, expiring, single-use approval in the private workspace.

## Prepare an experiment

Start from the final Phase 2 decision record, its chosen candidate, and a private specification:

```bash
python3 scripts/prepare_experiment_definition.py \
  --decision-record "$ROBOFOX_GTM_WORKSPACE/decisions/<decision>.json" \
  --candidate "$ROBOFOX_GTM_WORKSPACE/decisions/work/<decision>/candidates/<candidate>.json" \
  --spec experiment-spec.json \
  --output "$ROBOFOX_GTM_WORKSPACE/experiments/EXP-VOICE-0001.definition.json"
```

The specification may narrow exposure but cannot exceed the chosen move.

## Approve and register

```bash
python3 scripts/experiment_approval.py --workspace "$ROBOFOX_GTM_WORKSPACE" \
  prepare register_experiment_definition \
  --record "$ROBOFOX_GTM_WORKSPACE/experiments/EXP-VOICE-0001.definition.json" \
  --requested-by Febin --task-id TASK-EXP-VOICE-0001

python3 scripts/experiment_approval.py --workspace "$ROBOFOX_GTM_WORKSPACE" \
  approve "$ROBOFOX_GTM_WORKSPACE/approvals/pending/<ACT>.experiment-manifest.json" \
  --approved-by Febin

python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" register \
  "$ROBOFOX_GTM_WORKSPACE/experiments/EXP-VOICE-0001.definition.json" \
  --manifest "$ROBOFOX_GTM_WORKSPACE/approvals/pending/<ACT>.experiment-manifest.json" \
  --approval "$ROBOFOX_GTM_WORKSPACE/approvals/approved/<APR>.experiment-approval.json" \
  --state "$ROBOFOX_GTM_WORKSPACE/system-state.json"
```

Registration installs the Phase 3 tables in the existing private truth database after the exact approval has validated.

## Operate the lifecycle

Use a new exact approval for every transition, execution event, observation, and final outcome:

```bash
python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" transition transition.json ...
python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" execute execution.json ...
python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" observe observation.json ...
python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" finalize outcome.json ...
```

Read-only commands need no approval:

```bash
python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" status EXP-VOICE-0001
python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" evaluate EXP-VOICE-0001
python3 scripts/experiment_store.py --workspace "$ROBOFOX_GTM_WORKSPACE" integrity
```

## Outcome rules

- `SUCCESS`: minimum execution reached and every success criterion is `MET`.
- `FAILED`: a kill criterion is met, or minimum execution is complete and success criteria remain unmet.
- `SAFETY_STOP`: a named pre-registered hard stop fired.
- `CANCELLED`: founder terminates a non-terminal experiment without claiming a commercial result.

Every final record contains learning, belief updates, evidence observation IDs, deterministic criterion results, and one next action. The learning feeds a later Phase 1 snapshot; it does not silently rewrite evidence.

## Verify

```bash
python3 scripts/verify_phase3.py
python3 -m unittest discover -s tests/phase3 -p 'test_*.py' -v
```
