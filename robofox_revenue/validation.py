from __future__ import annotations
import hashlib,json,re
from datetime import datetime
from math import isfinite
from typing import Any
class RevenueError(ValueError): pass
PATTERNS={'account':re.compile(r'^ACC-[A-Z0-9-]{6,80}$'),'contact':re.compile(r'^CNT-[A-Z0-9-]{6,80}$'),'opportunity':re.compile(r'^OPP-[A-Z0-9-]{6,80}$'),'event':re.compile(r'^REV-[A-Z0-9-]{6,80}$'),'payment':re.compile(r'^PAY-[A-Z0-9-]{6,80}$'),'override':re.compile(r'^QOV-[A-Z0-9-]{6,80}$'),'exception':re.compile(r'^REX-[A-Z0-9-]{6,80}$')}
STAGES=['LEAD','QUALIFIED','CONVERSATION','DEMO','PROPOSAL','WON','LOST','ONBOARDING','ACTIVE','RENEWAL','CHURNED']
PROHIBITED={'race','religion','caste','gender','health','disability','age','nationality','political_view'}
def canonical_json(v:Any)->str:
 try:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
 except (TypeError,ValueError) as e:raise RevenueError(f'not canonical JSON: {e}') from e
def canonical_hash(v:Any)->str:return 'sha256:'+hashlib.sha256(canonical_json(v).encode()).hexdigest()
def time(v:Any,f:str)->str:
 if not isinstance(v,str):raise RevenueError(f'{f} must be date-time')
 n=v[:-1]+'+00:00' if v.endswith('Z') else v
 try:d=datetime.fromisoformat(n)
 except ValueError as e:raise RevenueError(f'{f} invalid') from e
 if d.tzinfo is None:raise RevenueError(f'{f} must have timezone')
 return d.isoformat()
def ident(v:Any,k:str)->str:
 if not isinstance(v,str) or not PATTERNS[k].fullmatch(v):raise RevenueError(f'invalid {k} id')
 return v
def exact(r:dict,keys:set[str],req:set[str]|None=None):
 if not isinstance(r,dict):raise RevenueError('record must be object')
 m=(req or keys)-set(r);u=set(r)-keys
 if m or u:raise RevenueError(f'invalid fields missing={sorted(m)} unknown={sorted(u)}')
def num(v:Any,f:str,minv:float=0)->float:
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(float(v)) or float(v)<minv:raise RevenueError(f'{f} invalid')
 return float(v)
def no_direct_identity(r:dict):
 bad={k for k in r if k.lower() in {'name','email','phone','address','token','secret'}}
 if bad:raise RevenueError(f'direct identity fields prohibited: {sorted(bad)}')
def validate_entity(r:dict)->dict:
 keys={'id','kind','account_id','segment','region','created_at','source','external_key_hash','status','metadata'};exact(r,keys)
 kind=r['kind']
 if kind not in {'ACCOUNT','CONTACT','OPPORTUNITY'}:raise RevenueError('invalid entity kind')
 ident(r['id'],{'ACCOUNT':'account','CONTACT':'contact','OPPORTUNITY':'opportunity'}[kind])
 if kind!='ACCOUNT':ident(r['account_id'],'account')
 elif r['account_id'] is not None:raise RevenueError('account entity account_id must be null')
 if r['source'] not in {'HUBSPOT','META','MANUAL','SYNTHETIC'}:raise RevenueError('invalid source')
 if not isinstance(r['external_key_hash'],str) or not re.fullmatch(r'sha256:[a-f0-9]{64}',r['external_key_hash']):raise RevenueError('invalid external_key_hash')
 if not isinstance(r['metadata'],dict):raise RevenueError('metadata object required')
 no_direct_identity(r['metadata'])
 return {**r,'created_at':time(r['created_at'],'created_at')}
def validate_event(r:dict)->dict:
 keys={'id','opportunity_id','account_id','stage','occurred_at','source','experiment_id','channel','first_touch','self_reported_source','influencing_channels','conversion_touch','consent_status','metadata'};exact(r,keys)
 ident(r['id'],'event');ident(r['opportunity_id'],'opportunity');ident(r['account_id'],'account')
 if r['stage'] not in STAGES:raise RevenueError('invalid stage')
 if r['source'] not in {'HUBSPOT','META','MANUAL','SYNTHETIC'}:raise RevenueError('invalid source')
 if r['consent_status'] not in {'OPTED_IN','EXISTING_RELATIONSHIP','UNKNOWN','OPTED_OUT','DO_NOT_CONTACT'}:raise RevenueError('invalid consent')
 if not isinstance(r['influencing_channels'],list) or len(r['influencing_channels'])!=len(set(r['influencing_channels'])):raise RevenueError('influencing_channels must be unique list')
 if not isinstance(r['metadata'],dict):raise RevenueError('metadata object required')
 no_direct_identity(r['metadata'])
 return {**r,'occurred_at':time(r['occurred_at'],'occurred_at')}
def validate_payment(r:dict)->dict:
 keys={'id','opportunity_id','amount','currency','kind','occurred_at','source_id','metadata'};exact(r,keys)
 ident(r['id'],'payment');ident(r['opportunity_id'],'opportunity')
 if r['currency'] not in {'USD','INR'}:raise RevenueError('unsupported currency')
 if r['kind'] not in {'RECOGNIZED','RECEIVED','REFUND'}:raise RevenueError('invalid payment kind')
 if not isinstance(r['metadata'],dict):raise RevenueError('metadata object required')
 return {**r,'amount':num(r['amount'],'amount'),'occurred_at':time(r['occurred_at'],'occurred_at')}
def validate_qualification(features:dict)->dict:
 if not isinstance(features,dict):raise RevenueError('features must be object')
 bad=PROHIBITED&{k.lower() for k in features}
 if bad:raise RevenueError(f'prohibited qualification attributes: {sorted(bad)}')
 allowed={'segment_match','pain_signal','authority_signal','urgency_signal','budget_signal','consent_status'}
 if set(features)-allowed:raise RevenueError(f'unknown qualification features: {sorted(set(features)-allowed)}')
 for k in allowed-{'consent_status'}:
  if features.get(k) not in {True,False,None}:raise RevenueError(f'{k} must be boolean or null')
 if features.get('consent_status') not in {'OPTED_IN','EXISTING_RELATIONSHIP','UNKNOWN','OPTED_OUT','DO_NOT_CONTACT'}:raise RevenueError('invalid consent status')
 return dict(features)
