# Phase 6 — Learning and Portfolio Optimizer

Phase 6 turns immutable predictions, experiment outcomes, and reconciled revenue into calibrated beliefs and explainable portfolio recommendations. Outputs are advice only and never change real budgets or execution.

## Guarantees

- prediction/outcome calibration with Brier score and overconfidence
- belief updates trace to source and independent experiment families
- first-party benchmark overrides require sample ≥30, relevance ≥0.7, and exact context match
- scorecards include revenue, margin, retention, attribution, learning, conversion, founder time, cash, and trust
- allocations are concentration-limited
- sensitivity analysis exposes rank instability
- material belief changes trigger a new Phase 2 decision request

## Verify

```bash
python3 scripts/verify_phase6.py
python3 -m unittest discover -s tests/phase6 -p 'test_*.py' -v
```
