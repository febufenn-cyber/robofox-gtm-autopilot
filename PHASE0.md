# Phase 0 Implementation

Phase 0 is the constitutional and technical safety boundary for Robofox GTM Autopilot.

## Enforced defaults

- Public engine and private workspace separation
- L1 advisory autonomy
- Active kill switch
- Default-deny action registry
- External sends, calls, publishing, CRM writes, ad writes, spending, and contact export disabled
- Aggregate-first evidence access and most-restrictive consent resolution
- External content treated as untrusted data
- Exact action-bound approval schemas
- Closed JSON schemas for tasks, actions, approvals, evidence, and audit events
- Public-repository secret/PII/path scanner
- Pinned upstream source lock
- GitHub Actions and local policy tests

## Bootstrap the private workspace

```bash
python3 scripts/bootstrap_private_workspace.py ~/private/robofox-gtm-workspace
export ROBOFOX_GTM_WORKSPACE=~/private/robofox-gtm-workspace
```

The script refuses to place the private workspace inside this repository. Creating the remote private GitHub repository remains an explicit founder action because repository creation and access policy are outside this engine.

## Verify

```bash
python3 scripts/verify_repo.py
python3 scripts/verify_phase0.py
python3 -m unittest discover -s tests/phase0 -p 'test_*.py' -v
python3 scripts/scan_public_repo.py
```

## Test an action decision

The safe default has the kill switch active:

```bash
python3 scripts/phase0_policy.py authorize generate_channel_plan
```

A private workspace may deliberately lift only the kill switch while remaining at L1. External and financial actions remain disabled in the action registry.
