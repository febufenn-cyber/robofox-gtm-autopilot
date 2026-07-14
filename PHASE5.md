# Phase 5 — Revenue Operations Loop

Phase 5 normalizes read-only commercial snapshots into pseudonymous, immutable entities, lifecycle events, attribution fields, qualification decisions, revenue records, and explicit exception reports.

It performs no CRM writes and sends no follow-up. Any proposed task must later pass through the Phase 4 simulator or a separately approved future gateway.

## Guarantees

- read-only snapshot mode and cursor replay protection
- pseudonymous account/contact/opportunity identifiers
- first-touch, self-reported, influencing, and conversion attribution remain separate
- explainable deterministic qualification using only allowed commercial signals
- prohibited personal attributes are rejected
- consent restrictions override qualification
- pipeline state derives from append-only events
- regressions and skips become explicit exceptions
- won deals require reconciled revenue evidence
- currency conflicts and missing payments remain visible

## Verify

```bash
python3 scripts/verify_phase5.py
python3 -m unittest discover -s tests/phase5 -p 'test_*.py' -v
```
