#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robofox_decision import DecisionError,verify_decision_record

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def main():
    p=argparse.ArgumentParser(description='Replay and verify one Phase 2 decision record')
    p.add_argument('--snapshot',required=True);p.add_argument('--request',required=True);p.add_argument('--candidates',nargs='+',required=True);p.add_argument('--reviews',nargs='+',required=True);p.add_argument('--assessments',nargs='+',required=True);p.add_argument('--record',required=True);p.add_argument('--weights');a=p.parse_args()
    try:
        verify_decision_record(load(a.snapshot),load(a.request),[load(x) for x in a.candidates],[load(x) for x in a.reviews],[load(x) for x in a.assessments],load(a.record),weights_path=Path(a.weights) if a.weights else None)
        print('DECISION RECORD: PASS'); return 0
    except (DecisionError,OSError,json.JSONDecodeError) as exc: print(f'DECISION RECORD: FAIL\n- {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
