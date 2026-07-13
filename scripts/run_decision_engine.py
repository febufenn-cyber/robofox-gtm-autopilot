#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robofox_decision import DecisionError,arbitrate,write_decision

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def main():
    p=argparse.ArgumentParser(description='Run deterministic Robofox Phase 2 arbitration')
    p.add_argument('--snapshot',required=True); p.add_argument('--request',required=True); p.add_argument('--candidates',nargs='+',required=True); p.add_argument('--reviews',nargs='+',required=True); p.add_argument('--assessments',nargs='+',required=True); p.add_argument('--weights'); p.add_argument('--workspace'); p.add_argument('--stdout',action='store_true'); a=p.parse_args()
    try:
        record=arbitrate(load(a.snapshot),load(a.request),[load(x) for x in a.candidates],[load(x) for x in a.reviews],[load(x) for x in a.assessments],weights_path=Path(a.weights) if a.weights else None)
        if a.workspace:
            paths=write_decision(record,Path(a.workspace).expanduser()); print(json.dumps({'json':str(paths[0]),'markdown':str(paths[1]),'status':record['status']},indent=2))
        if a.stdout or not a.workspace: print(json.dumps(record,indent=2,ensure_ascii=False))
        return 0
    except (DecisionError,OSError,json.JSONDecodeError) as exc: print(f'DECISION ENGINE: FAIL\n- {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
