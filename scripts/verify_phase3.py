#!/usr/bin/env python3
"""Run all Phase 3 experiment operating-system verification."""
from verify_phase3_contracts import verify as verify_contracts
from verify_phase3_engine import verify as verify_engine
from verify_phase3_skills import verify as verify_skills
def verify()->list[str]:
    errors=[]
    errors.extend(f'contracts: {x}' for x in verify_contracts())
    errors.extend(f'engine: {x}' for x in verify_engine())
    errors.extend(f'skills: {x}' for x in verify_skills())
    return errors
def main()->int:
    errors=verify()
    if errors:
        print('PHASE3 VERIFY: FAIL'); [print(f'- {x}') for x in errors]; return 1
    print('PHASE3 VERIFY: PASS')
    print('- pre-registration, lifecycle, collision, exposure, criteria, learning, approvals, integrity')
    return 0
if __name__=='__main__': raise SystemExit(main())
