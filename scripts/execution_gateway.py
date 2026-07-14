#!/usr/bin/env python3
"""Operate the Phase 4 simulator gateway. No live adapter exists."""
from __future__ import annotations
import argparse,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from robofox_execution import ExecutionError, approved_execute, approved_rollback, execution_status, integrity_report, install_schema

def load(path:str)->dict:
    value=json.loads(Path(path).read_text())
    if not isinstance(value,dict): raise ExecutionError('JSON must be an object')
    return value
def connect(workspace:Path)->sqlite3.Connection:
    path=workspace/'truth/robofox_truth.sqlite3'; path.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(path); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def approval_args(p): p.add_argument('--manifest',required=True); p.add_argument('--approval',required=True); p.add_argument('--state',required=True); p.add_argument('--now',required=True)
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--workspace',required=True); s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('review'); q.add_argument('record')
    q=s.add_parser('execute'); q.add_argument('record'); approval_args(q)
    q=s.add_parser('rollback'); q.add_argument('record'); approval_args(q); q.add_argument('--simulate-failure',action='store_true')
    q=s.add_parser('status'); q.add_argument('envelope_id')
    s.add_parser('integrity')
    a=p.parse_args(); workspace=Path(a.workspace).expanduser().resolve()
    try:
        if a.cmd=='review':
            r=load(a.record); print(json.dumps({k:r.get(k) for k in ('id','experiment_id','action_type','adapter','mode','batch_size','canary_for_id','content_hash','maximum_spend_usd','rate_limit_per_hour','rollback_plan')},indent=2)); return 0
        c=connect(workspace); install_schema(c)
        try:
            if a.cmd=='execute': out=approved_execute(c,workspace,Path(a.state),load(a.record),load(a.manifest),load(a.approval),now=a.now)
            elif a.cmd=='rollback': out=approved_rollback(c,workspace,Path(a.state),load(a.record),load(a.manifest),load(a.approval),now=a.now,fail=a.simulate_failure)
            elif a.cmd=='status': out=execution_status(c,a.envelope_id)
            else: out=integrity_report(c)
        finally: c.close()
        print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out.get('ok',True) else 1
    except (ExecutionError,OSError,json.JSONDecodeError,sqlite3.IntegrityError) as exc:
        print(f'EXECUTION GATEWAY: FAIL\n- {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
