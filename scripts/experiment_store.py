#!/usr/bin/env python3
"""Approved write and read-only status CLI for the Phase 3 experiment OS."""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from phase0_policy import authorize
from robofox_experiment import TruthStoreError, approved_apply, evaluate_criteria, experiment_status, integrity_report
from robofox_truth import connect, resolve_workspace
from robofox_truth.approval import load_json_object
COMMAND_ACTIONS={'register':'register_experiment_definition','transition':'record_experiment_transition','execute':'record_experiment_execution','observe':'record_experiment_observation','finalize':'finalize_experiment'}
def add_write_args(p):
    p.add_argument('record'); p.add_argument('--manifest',required=True); p.add_argument('--approval',required=True); p.add_argument('--state',required=True)
def require_policy(workspace:Path,action_type:str,state_path:str)->None:
    path=Path(state_path).expanduser().resolve()
    try: path.relative_to(workspace.resolve())
    except ValueError as exc: raise TruthStoreError('system-state file must be inside private workspace') from exc
    state=load_json_object(path); ws=load_json_object(workspace/'workspace.json')
    if state.get('workspace_id')!=ws.get('workspace_id'): raise TruthStoreError('system-state workspace_id does not match workspace.json')
    decision=authorize(action_type,approval=True,state_path=path)
    if not decision.allowed: raise TruthStoreError(f'policy denied {action_type}: {decision.code}: {decision.reason}')
def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--workspace'); sub=p.add_subparsers(dest='command',required=True)
    for cmd in COMMAND_ACTIONS: add_write_args(sub.add_parser(cmd))
    q=sub.add_parser('status'); q.add_argument('experiment_id'); q.add_argument('--as-of')
    q=sub.add_parser('evaluate'); q.add_argument('experiment_id')
    sub.add_parser('integrity')
    a=p.parse_args(argv)
    try:
        workspace=resolve_workspace(a.workspace)
        with connect(workspace) as connection:
            if a.command=='status': output=experiment_status(connection,a.experiment_id,as_of=a.as_of)
            elif a.command=='evaluate': output=evaluate_criteria(connection,a.experiment_id)
            elif a.command=='integrity': output=integrity_report(connection)
            else:
                action=COMMAND_ACTIONS[a.command]; require_policy(workspace,action,a.state); payload=load_json_object(a.record); manifest=load_json_object(a.manifest); approval=load_json_object(a.approval)
                output={'inserted':approved_apply(connection,workspace,action,payload,manifest,approval),'approval_id':approval['approval_id']}
        print(json.dumps(output,indent=2,sort_keys=True)); return 0 if output.get('ok',True) else 1
    except (TruthStoreError,OSError,sqlite3.Error) as exc:
        print(f'EXPERIMENT STORE: FAIL\n- {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
