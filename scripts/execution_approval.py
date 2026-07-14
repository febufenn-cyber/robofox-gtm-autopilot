#!/usr/bin/env python3
"""Prepare and founder-approve exact Phase 4 simulator actions."""
from __future__ import annotations
import argparse,json,os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from robofox_execution import ExecutionError, canonical_hash, create_approval, prepare_manifest

def load(path:str)->dict:
    value=json.loads(Path(path).read_text())
    if not isinstance(value,dict): raise ExecutionError('record must be an object')
    return value
def write(path:Path,value:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True); fd,name=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name+'.')
    try:
        with os.fdopen(fd,'w') as h: json.dump(value,h,indent=2); h.write('\n'); h.flush(); os.fsync(h.fileno())
        Path(name).chmod(0o600); os.replace(name,path)
    finally:
        if Path(name).exists(): Path(name).unlink()
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--workspace',required=True); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('prepare'); q.add_argument('action_type',choices=['execute_simulated_action','rollback_simulated_action']); q.add_argument('--record',required=True); q.add_argument('--requested-by',required=True); q.add_argument('--task-id',required=True); q.add_argument('--created-at',required=True)
    q=sub.add_parser('approve'); q.add_argument('manifest'); q.add_argument('--approved-by',required=True); q.add_argument('--approved-at',required=True); q.add_argument('--expires-minutes',type=int,default=15)
    a=p.parse_args(); workspace=Path(a.workspace).expanduser().resolve()
    try:
        if a.cmd=='prepare':
            record=load(a.record); m=prepare_manifest(workspace,a.action_type,record,requested_by=a.requested_by,task_id=a.task_id,created_at=a.created_at); out=workspace/'approvals/pending'/f"{m['action_id']}.execution-manifest.json"; write(out,m); print(json.dumps({'manifest':str(out),'manifest_hash':canonical_hash(m)},indent=2)); return 0
        m=load(a.manifest)
        if not sys.stdin.isatty(): raise ExecutionError('approval requires an interactive founder-controlled terminal')
        phrase=f"APPROVE {m['action_id']} {m['payload_hash']}"
        print(json.dumps({'action_type':m['action_type'],'envelope_id':m['envelope_id'],'adapter':m['adapter'],'mode':m['mode'],'maximum_records':m['maximum_records'],'maximum_spend_usd':m['maximum_spend_usd']},indent=2))
        if input(f'Type exactly:\n{phrase}\n> ')!=phrase: raise ExecutionError('approval phrase mismatch')
        approval=create_approval(m,approved_by=a.approved_by,approved_at=a.approved_at,expires_minutes=a.expires_minutes); out=workspace/'approvals/approved'/f"{approval['approval_id']}.execution-approval.json"; write(out,approval); print(json.dumps({'approval':str(out),'expires_at':approval['expires_at']},indent=2)); return 0
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        print(f'EXECUTION APPROVAL: FAIL\n- {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
