"""Exact approvals for Phase 4 simulator execution and rollback."""
from __future__ import annotations
import re,secrets
from datetime import datetime,timedelta
from pathlib import Path
from typing import Any
from .validation import ExecutionError, canonical_hash, parse_time, validate_envelope, validate_rollback

ACTION_TYPES={"execute_simulated_action","rollback_simulated_action"}
ACTION_RE=re.compile(r'^ACT-[0-9]{4}-[0-9]{5,}$'); APPROVAL_RE=re.compile(r'^APR-[0-9]{4}-[0-9]{5,}$')
def _now(value:str)->datetime: return datetime.fromisoformat(parse_time(value,'time'))
def _id(prefix:str,now:datetime)->str: return f'{prefix}-{now.year}-{secrets.randbelow(10**10):010d}'
def workspace_id(workspace:Path)->str:
    import json
    data=json.loads((workspace/'workspace.json').read_text())
    if data.get('public_repo') is not False or not isinstance(data.get('workspace_id'),str): raise ExecutionError('private workspace identity is invalid')
    return data['workspace_id']
def prepare_manifest(workspace:Path,action_type:str,payload:dict[str,Any],*,requested_by:str,task_id:str,created_at:str)->dict[str,Any]:
    if action_type not in ACTION_TYPES: raise ExecutionError('unsupported execution approval action')
    if action_type=='execute_simulated_action': record=validate_envelope(payload); envelope_id=record['id']; max_records=record['batch_size']; adapter=record['adapter']; mode=record['mode']; spend=record['maximum_spend_usd']
    else: record=validate_rollback(payload); envelope_id=record['envelope_id']; max_records=1; adapter=None; mode='SIMULATOR'; spend=0
    now=_now(created_at)
    return {'action_id':_id('ACT',now),'action_type':action_type,'task_id':task_id,'workspace_id':workspace_id(workspace),'envelope_id':envelope_id,'adapter':adapter,'mode':mode,'payload_hash':canonical_hash(record),'maximum_records':max_records,'maximum_spend_usd':spend,'currency':'USD','requested_by':requested_by,'created_at':now.isoformat()}
def create_approval(manifest:dict[str,Any],*,approved_by:str,approved_at:str,expires_minutes:int=30)->dict[str,Any]:
    if not 1<=expires_minutes<=60: raise ExecutionError('execution approval expiry must be 1..60 minutes')
    now=_now(approved_at)
    return {'approval_id':_id('APR',now),'action_id':manifest['action_id'],'manifest_hash':canonical_hash(manifest),'approved_by':approved_by,'approved_at':now.isoformat(),'expires_at':(now+timedelta(minutes=expires_minutes)).isoformat(),'single_use':True,'consumed_at':None}
def validate_approval(workspace:Path,action_type:str,payload:dict[str,Any],manifest:dict[str,Any],approval:dict[str,Any],*,now:str)->None:
    if action_type not in ACTION_TYPES or manifest.get('action_type')!=action_type: raise ExecutionError('approval action mismatch')
    expected=prepare_manifest(workspace,action_type,payload,requested_by=manifest.get('requested_by',''),task_id=manifest.get('task_id',''),created_at=manifest.get('created_at',''))
    expected['action_id']=manifest.get('action_id')
    if expected!=manifest: raise ExecutionError('manifest does not bind exact execution payload and scope')
    if not ACTION_RE.fullmatch(str(manifest['action_id'])): raise ExecutionError('invalid action_id')
    if not APPROVAL_RE.fullmatch(str(approval.get('approval_id'))): raise ExecutionError('invalid approval_id')
    if approval.get('action_id')!=manifest['action_id'] or approval.get('manifest_hash')!=canonical_hash(manifest): raise ExecutionError('approval does not bind exact manifest')
    if approval.get('single_use') is not True or approval.get('consumed_at') is not None: raise ExecutionError('approval must be unused and single-use')
    approved=_now(approval['approved_at']); current=_now(now); expires=_now(approval['expires_at']); created=_now(manifest['created_at'])
    if approved<created or approved>current or current>=expires or expires-approved>timedelta(minutes=60): raise ExecutionError('approval time is invalid or expired')
def consume(connection,manifest:dict[str,Any],approval:dict[str,Any],payload:dict[str,Any],when:str)->None:
    connection.execute('INSERT INTO execution_approval_consumptions(approval_id,action_id,action_type,manifest_hash,payload_hash,envelope_id,consumed_at) VALUES(?,?,?,?,?,?,?)',(approval['approval_id'],manifest['action_id'],manifest['action_type'],approval['manifest_hash'],canonical_hash(payload),manifest['envelope_id'],when))
