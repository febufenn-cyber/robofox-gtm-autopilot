"""Exact, expiring, single-use approvals for Phase 3 experiment mutations."""
from __future__ import annotations
import re, secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from robofox_truth.approval import ApprovalDecision, canonical_hash, consume_approval, workspace_id
from robofox_truth.store import utc_now
from robofox_truth.validation import TruthStoreError, parse_datetime
from .constants import ACTION_MAX_RECORDS, ACTION_TO_KIND, HASH_RE
from .store import INSERT_FUNCTIONS, install_schema

ACTION_ID_RE=re.compile(r'^ACT-[0-9]{4}-[0-9]{5,}$')
APPROVAL_ID_RE=re.compile(r'^APR-[0-9]{4}-[0-9]{5,}$')
MANIFEST_KEYS={'action_id','action_type','task_id','experiment_id','scope','payload_hash','requested_by','created_at','maximum_records','maximum_spend','currency'}
APPROVAL_KEYS={'approval_id','action_id','manifest_hash','approved_by','approved_at','expires_at','single_use','consumed_at'}

def _now(value:str|None=None)->datetime:
    normalized=parse_datetime(value or utc_now(),'now'); assert normalized is not None; return datetime.fromisoformat(normalized)
def _identifier(prefix:str, now:datetime)->str: return f'{prefix}-{now.year}-{secrets.randbelow(10**10):010d}'
def expected_scope(workspace:Path, action_type:str, payload:dict[str,Any])->dict[str,Any]:
    if action_type not in ACTION_TO_KIND: raise TruthStoreError(f'unsupported experiment action: {action_type}')
    record_id=payload.get('id'); experiment_id=payload.get('experiment_id') or (record_id if action_type=='register_experiment_definition' else None)
    if not isinstance(record_id,str) or not isinstance(experiment_id,str): raise TruthStoreError('experiment action payload requires id and experiment binding')
    return {'workspace_id':workspace_id(workspace),'database':'truth/robofox_truth.sqlite3','record_id':record_id,'experiment_id':experiment_id}
def prepare_manifest(workspace:Path, action_type:str, payload:dict[str,Any], *, requested_by:str, task_id:str, created_at:str|None=None)->dict[str,Any]:
    if action_type not in ACTION_TO_KIND: raise TruthStoreError(f'unsupported experiment action: {action_type}')
    if not requested_by.strip() or not task_id.strip(): raise TruthStoreError('requested_by and task_id are required')
    now=_now(created_at); exp_id=payload.get('experiment_id') or payload.get('id')
    return {'action_id':_identifier('ACT',now),'action_type':action_type,'task_id':task_id,'experiment_id':exp_id,'scope':expected_scope(workspace,action_type,payload),'payload_hash':canonical_hash(payload),'requested_by':requested_by,'created_at':now.isoformat(),'maximum_records':ACTION_MAX_RECORDS[action_type],'maximum_spend':0,'currency':None}
def validate_manifest(manifest:dict[str,Any])->None:
    if not isinstance(manifest,dict): raise TruthStoreError('manifest must be an object')
    unknown=set(manifest)-MANIFEST_KEYS; missing={'action_id','action_type','task_id','experiment_id','scope','payload_hash','requested_by','created_at','maximum_records','maximum_spend','currency'}-set(manifest)
    if unknown or missing: raise TruthStoreError(f'invalid manifest fields; missing={sorted(missing)} unknown={sorted(unknown)}')
    if not ACTION_ID_RE.fullmatch(str(manifest['action_id'])): raise TruthStoreError('invalid action_id')
    if manifest['action_type'] not in ACTION_TO_KIND: raise TruthStoreError('unsupported experiment action_type')
    if not isinstance(manifest['payload_hash'],str) or not HASH_RE.fullmatch(manifest['payload_hash']): raise TruthStoreError('invalid payload_hash')
    parse_datetime(manifest['created_at'],'manifest.created_at')
    if manifest['maximum_records']!=ACTION_MAX_RECORDS[manifest['action_type']]: raise TruthStoreError('manifest maximum_records differs from action contract')
    if manifest['maximum_spend']!=0 or manifest['currency'] is not None: raise TruthStoreError('experiment mutations cannot authorize spending')
def create_approval(manifest:dict[str,Any], *, approved_by:str, approved_at:str|None=None, expires_minutes:int=30)->dict[str,Any]:
    validate_manifest(manifest)
    if not approved_by.strip(): raise TruthStoreError('approved_by is required')
    if not 1<=expires_minutes<=1440: raise TruthStoreError('approval expiry must be 1..1440 minutes')
    now=_now(approved_at)
    return {'approval_id':_identifier('APR',now),'action_id':manifest['action_id'],'manifest_hash':canonical_hash(manifest),'approved_by':approved_by,'approved_at':now.isoformat(),'expires_at':(now+timedelta(minutes=expires_minutes)).isoformat(),'single_use':True,'consumed_at':None}
def validate_approval(workspace:Path, action_type:str, payload:dict[str,Any], manifest:dict[str,Any], approval:dict[str,Any], *, now:str|None=None)->ApprovalDecision:
    validate_manifest(manifest)
    if not isinstance(approval,dict): raise TruthStoreError('approval must be an object')
    unknown=set(approval)-APPROVAL_KEYS; missing={'approval_id','action_id','manifest_hash','approved_by','approved_at','expires_at','single_use','consumed_at'}-set(approval)
    if unknown or missing: raise TruthStoreError(f'invalid approval fields; missing={sorted(missing)} unknown={sorted(unknown)}')
    if not APPROVAL_ID_RE.fullmatch(str(approval['approval_id'])): raise TruthStoreError('invalid approval_id')
    if approval['action_id']!=manifest['action_id'] or approval['manifest_hash']!=canonical_hash(manifest): raise TruthStoreError('approval does not bind to exact manifest')
    if manifest['action_type']!=action_type or manifest['payload_hash']!=canonical_hash(payload): raise TruthStoreError('manifest does not bind to exact action payload')
    if manifest['scope']!=expected_scope(workspace,action_type,payload): raise TruthStoreError('manifest scope does not match workspace or experiment')
    if approval['single_use'] is not True or approval['consumed_at'] is not None: raise TruthStoreError('approval must be unused and single-use')
    created=datetime.fromisoformat(parse_datetime(manifest['created_at'],'manifest.created_at') or '')
    approved=datetime.fromisoformat(parse_datetime(approval['approved_at'],'approval.approved_at') or '')
    expires=datetime.fromisoformat(parse_datetime(approval['expires_at'],'approval.expires_at') or '')
    current=_now(now)
    if approved<created or approved>current: raise TruthStoreError('approval time is invalid')
    if expires<=approved or current>=expires or expires-approved>timedelta(minutes=1440): raise TruthStoreError('approval has expired or exceeds maximum validity')
    return ApprovalDecision(approval['approval_id'],manifest['action_id'],action_type,approval['manifest_hash'],manifest['payload_hash'],ACTION_TO_KIND[action_type],str(payload['id']))
def approved_apply(connection, workspace:Path, action_type:str, payload:dict[str,Any], manifest:dict[str,Any], approval:dict[str,Any], *, now:str|None=None)->str:
    decision=validate_approval(workspace,action_type,payload,manifest,approval,now=now); insert=INSERT_FUNCTIONS[ACTION_TO_KIND[action_type]]
    if action_type=='register_experiment_definition': install_schema(connection)
    with connection:
        record_id=insert(connection,payload,commit=False); consume_approval(connection,decision)
    return record_id
