#!/usr/bin/env python3
from verify_phase2_contracts import verify as contracts
from verify_phase2_engine import verify as engine
from verify_phase2_skills import verify as skills

def verify(): return [f'contracts: {x}' for x in contracts()]+[f'engine: {x}' for x in engine()]+[f'skills: {x}' for x in skills()]
if __name__=='__main__':
    errors=verify()
    if errors:
        print('PHASE2 VERIFY: FAIL'); [print(f'- {x}') for x in errors]; raise SystemExit(1)
    print('PHASE2 VERIFY: PASS')
    print('- contracts, deterministic arbiter, role separation, private work pack, replay verification')
