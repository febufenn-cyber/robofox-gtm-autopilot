#!/usr/bin/env python3
"""Prepare and interactively approve one exact Phase 3 experiment mutation."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robofox_experiment import TruthStoreError, create_approval, prepare_manifest
from robofox_truth import resolve_workspace
from robofox_truth.approval import canonical_hash, load_json_object, write_private_json
ACTIONS=('register_experiment_definition','record_experiment_transition','record_experiment_execution','record_experiment_observation','finalize_experiment')
def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--workspace')
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('prepare'); q.add_argument('action_type',choices=ACTIONS); q.add_argument('--record',required=True); q.add_argument('--requested-by',required=True); q.add_argument('--task-id',required=True)
    q=sub.add_parser('approve'); q.add_argument('manifest'); q.add_argument('--approved-by',required=True); q.add_argument('--expires-minutes',type=int,default=30)
    a=p.parse_args(argv)
    try:
        workspace=resolve_workspace(a.workspace)
        if a.command=='prepare':
            payload=load_json_object(a.record); manifest=prepare_manifest(workspace,a.action_type,payload,requested_by=a.requested_by,task_id=a.task_id)
            path=workspace/'approvals'/'pending'/f"{manifest['action_id']}.experiment-manifest.json"; write_private_json(path,manifest)
            print(json.dumps({'manifest':str(path),'manifest_hash':canonical_hash(manifest)},indent=2)); return 0
        manifest=load_json_object(a.manifest)
        if not sys.stdin.isatty(): raise TruthStoreError('approval requires an interactive founder-controlled terminal')
        phrase=f"APPROVE {manifest.get('action_id')} {manifest.get('payload_hash')}"
        print(json.dumps({'action_type':manifest.get('action_type'),'scope':manifest.get('scope'),'payload_hash':manifest.get('payload_hash'),'manifest_hash':canonical_hash(manifest),'expires_minutes':a.expires_minutes},indent=2))
        if input(f'Type exactly:\n{phrase}\n> ')!=phrase: raise TruthStoreError('approval phrase did not match exactly')
        approval=create_approval(manifest,approved_by=a.approved_by,expires_minutes=a.expires_minutes)
        path=workspace/'approvals'/'approved'/f"{approval['approval_id']}.experiment-approval.json"; write_private_json(path,approval)
        print(json.dumps({'approval':str(path),'expires_at':approval['expires_at']},indent=2)); return 0
    except (TruthStoreError,OSError) as exc:
        print(f'EXPERIMENT APPROVAL: FAIL\n- {exc}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
