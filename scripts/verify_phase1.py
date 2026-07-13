#!/usr/bin/env python3
"""Run all zero-dependency Phase 1 truth-layer verification."""
from __future__ import annotations

from verify_phase1_approvals import verify as verify_approvals
from verify_phase1_contracts import verify as verify_contracts
from verify_phase1_ledger import verify as verify_ledger
from verify_phase1_position import verify as verify_position


def verify() -> list[str]:
    errors: list[str] = []
    errors.extend(f"contracts: {item}" for item in verify_contracts())
    errors.extend(f"ledger: {item}" for item in verify_ledger())
    errors.extend(f"position: {item}" for item in verify_position())
    errors.extend(f"approvals: {item}" for item in verify_approvals())
    return errors


def main() -> int:
    errors = verify()
    if errors:
        print("PHASE1 VERIFY: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PHASE1 VERIFY: PASS")
    print("- contracts, private ledger, position engine, exact approvals, and integrity checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
