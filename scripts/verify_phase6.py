#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from robofox_learning import *
REQ=['PHASE6.md','policies/learning-layer-policy.md','schemas/prediction-record.schema.json','schemas/belief-update.schema.json','schemas/portfolio-recommendation.schema.json','robofox_learning/core.py']
def verify():
 errors=[f'missing {x}' for x in REQ if not (ROOT/x).is_file()]
 b=belief_update(.5,'SUPPORT',1,['SRC-X'],['F1','F2','F3'])
 if not b['trigger_phase2']:errors.append('material update did not trigger Phase 2')
 a=allocate({'founder':.8,'referral':.6,'outbound':.2})
 if abs(sum(a.values())-100)>1e-5 or max(a.values())>50:errors.append('allocation smoke failed')
 return errors
if __name__=='__main__':
 errors=verify();print('PHASE6 VERIFY: '+('FAIL' if errors else 'PASS'));[print('- '+x) for x in errors];raise SystemExit(bool(errors))
