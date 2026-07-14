# Phase 4 — Controlled Execution Gateway

Phase 4 adds a deterministic boundary between approved intent and a side-effect adapter. The current release is intentionally **simulator-only**: no live credentials, endpoints, sends, calls, CRM writes, publishing, advertising changes, or spending are implemented.

## Guarantees

- exact payload- and scope-bound approvals
- private-workspace state checks
- unique idempotency keys and replay rejection
- one-record canary before bounded batches
- adapter-specific batch and hourly limits
- deterministic `SUCCESS`, `PARTIAL`, `FAILURE`, and `AMBIGUOUS` results
- circuit breaker after three consecutive unsafe outcomes
- immutable attempts, results, rollback, circuit, and approval-consumption records
- rollback only for adapters declared reversible
- zero network calls and zero spend in every adapter

## Private state

A simulator operation requires a private `system-state.json` containing:

```json
{
  "workspace_id": "WS-...",
  "kill_switch": false,
  "simulation_enabled": true,
  "external_execution": false
}
```

`external_execution` must remain false.

## Review, approve, execute

```bash
python3 scripts/execution_gateway.py --workspace "$ROBOFOX_GTM_WORKSPACE" review envelope.json
python3 scripts/execution_approval.py --workspace "$ROBOFOX_GTM_WORKSPACE" prepare execute_simulated_action --record envelope.json --requested-by Febin --task-id TASK-X --created-at "2026-07-14T10:00:00+05:30"
python3 scripts/execution_approval.py --workspace "$ROBOFOX_GTM_WORKSPACE" approve <manifest> --approved-by Febin --approved-at "2026-07-14T10:01:00+05:30"
python3 scripts/execution_gateway.py --workspace "$ROBOFOX_GTM_WORKSPACE" execute envelope.json --manifest <manifest> --approval <approval> --state "$ROBOFOX_GTM_WORKSPACE/system-state.json" --now "2026-07-14T10:02:00+05:30"
```

## Verify

```bash
python3 scripts/verify_phase4.py
python3 -m unittest discover -s tests/phase4 -p 'test_*.py' -v
```
