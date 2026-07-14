from __future__ import annotations
import json,sqlite3
from pathlib import Path
from typing import Any
from .validation import *
def install_schema(c:sqlite3.Connection):c.executescript((Path(__file__).resolve().parent/'migrations/001_revenue_operations.sql').read_text());c.commit()
def _insert(c,table,r,cols,commit=True):
 vals=[r[x] for x in cols];sql=f"INSERT INTO {table}({','.join(cols)},record_json,record_hash) VALUES({','.join('?' for _ in cols)},?,?)"
 def op():c.execute(sql,(*vals,canonical_json(r),canonical_hash(r)))
 if commit:
  with c:op()
 else:op()
 return r['id']
def add_entity(c,r,commit=True):
 r=validate_entity(r)
 if r['account_id'] and not c.execute("SELECT 1 FROM commercial_entities WHERE id=? AND kind='ACCOUNT'",(r['account_id'],)).fetchone():raise RevenueError('account reference missing')
 return _insert(c,'commercial_entities',r,['id','kind','account_id','segment','region','created_at','source','external_key_hash','status'],commit)
def add_event(c,r,commit=True):
 r=validate_event(r)
 if not c.execute("SELECT 1 FROM commercial_entities WHERE id=? AND kind='OPPORTUNITY'",(r['opportunity_id'],)).fetchone():raise RevenueError('opportunity reference missing')
 if not c.execute("SELECT 1 FROM commercial_entities WHERE id=? AND kind='ACCOUNT'",(r['account_id'],)).fetchone():raise RevenueError('account reference missing')
 return _insert(c,'lifecycle_events',r,['id','opportunity_id','account_id','stage','occurred_at','source','experiment_id','channel','first_touch','self_reported_source','conversion_touch','consent_status'],commit)
def add_payment(c,r,commit=True):
 r=validate_payment(r)
 if not c.execute("SELECT 1 FROM commercial_entities WHERE id=? AND kind='OPPORTUNITY'",(r['opportunity_id'],)).fetchone():raise RevenueError('opportunity reference missing')
 return _insert(c,'revenue_records',r,['id','opportunity_id','amount','currency','kind','occurred_at','source_id'],commit)
def current_stage(c,opp):
 row=c.execute('SELECT stage FROM lifecycle_events WHERE opportunity_id=? ORDER BY occurred_at DESC,id DESC LIMIT 1',(opp,)).fetchone();return row[0] if row else None
def stage_exceptions(c,opp)->list[dict]:
 rows=list(c.execute('SELECT id,stage,occurred_at FROM lifecycle_events WHERE opportunity_id=? ORDER BY occurred_at,id',(opp,)));out=[]
 for a,b in zip(rows,rows[1:]):
  ai=STAGES.index(a[1]);bi=STAGES.index(b[1])
  if b[1] not in {'LOST','CHURNED'} and bi<ai:out.append({'code':'STAGE_REGRESSION','from':a[1],'to':b[1],'event_id':b[0]})
  if b[1] not in {'LOST','CHURNED'} and bi-ai>2:out.append({'code':'STAGE_SKIP','from':a[1],'to':b[1],'event_id':b[0]})
 return out
def attribution(c,opp)->dict[str,Any]:
 rows=list(c.execute('SELECT first_touch,self_reported_source,conversion_touch,record_json FROM lifecycle_events WHERE opportunity_id=? ORDER BY occurred_at,id',(opp,)))
 if not rows:return {'first_touch':None,'self_reported_source':None,'influencing_channels':[],'conversion_touch':None}
 influencing=[]
 for row in rows:influencing.extend(json.loads(row[3]).get('influencing_channels',[]))
 return {'first_touch':next((r[0] for r in rows if r[0]),None),'self_reported_source':next((r[1] for r in reversed(rows) if r[1]),None),'influencing_channels':sorted(set(influencing)),'conversion_touch':next((r[2] for r in reversed(rows) if r[2]),None)}
def reconcile(c,opp)->dict[str,Any]:
 stage=current_stage(c,opp);rows=list(c.execute('SELECT amount,currency,kind,id FROM revenue_records WHERE opportunity_id=?',(opp,)))
 currencies=sorted({r[1] for r in rows});received=sum(r[0] if r[2]=='RECEIVED' else -r[0] if r[2]=='REFUND' else 0 for r in rows);recognized=sum(r[0] if r[2]=='RECOGNIZED' else 0 for r in rows);exceptions=[]
 if len(currencies)>1:exceptions.append('CURRENCY_MISMATCH')
 if stage=='WON' and not rows:exceptions.append('WON_WITHOUT_REVENUE')
 if stage=='WON' and received<=0 and recognized<=0:exceptions.append('WON_WITHOUT_POSITIVE_VALUE')
 return {'opportunity_id':opp,'stage':stage,'currencies':currencies,'received':received,'recognized':recognized,'record_ids':[r[3] for r in rows],'exceptions':exceptions,'reconciled':not exceptions}
def integrity(c)->dict:
 issues=[]
 if [r[0] for r in c.execute('PRAGMA integrity_check')]!=['ok']:issues.append('sqlite integrity')
 if list(c.execute('PRAGMA foreign_key_check')):issues.append('foreign key')
 for table in ('commercial_entities','lifecycle_events','revenue_records','qualification_overrides'):
  for row in c.execute(f'SELECT id,record_json,record_hash FROM {table}'):
   if canonical_hash(json.loads(row[1]))!=row[2]:issues.append(f'hash mismatch {table}.{row[0]}')
 return {'ok':not issues,'issues':issues}
