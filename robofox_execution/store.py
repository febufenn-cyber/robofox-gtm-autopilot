"""Append-only Phase 4 simulator gateway."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from .adapters import simulate, simulate_rollback
from .constants import ADAPTERS
from .validation import ExecutionError, canonical_hash, canonical_json, validate_envelope, validate_result, validate_rollback

def utc_now()->str: return datetime.now(timezone.utc).isoformat()
def install_schema(connection:sqlite3.Connection, migration_path:Path|None=None)->None:
    path=migration_path or Path(__file__).resolve().parent/'migrations/001_execution_gateway.sql'
    connection.executescript(path.read_text()); connection.commit()
def _row_json(connection:sqlite3.Connection,table:str,record_id:str)->dict[str,Any]:
    row=connection.execute(f'SELECT record_json FROM {table} WHERE id=?',(record_id,)).fetchone()
    if row is None: raise ExecutionError(f'{table} record not found: {record_id}')
    return json.loads(row[0])
def latest_circuit_state(connection:sqlite3.Connection,adapter:str)->str:
    row=connection.execute('SELECT state FROM execution_circuit_events WHERE adapter=? ORDER BY occurred_at DESC,id DESC LIMIT 1',(adapter,)).fetchone()
    return row[0] if row else 'CLOSED'
def _assert_canary(connection:sqlite3.Connection,envelope:dict[str,Any])->None:
    if envelope['batch_size']==1: return
    prior=_row_json(connection,'execution_envelopes',envelope['canary_for_id'])
    result_row=connection.execute('SELECT record_json FROM execution_results WHERE envelope_id=?',(envelope['canary_for_id'],)).fetchone()
    if result_row is None: raise ExecutionError('bounded batch requires completed canary')
    result=json.loads(result_row[0])
    if result['outcome']!='SUCCESS' or prior['batch_size']!=1: raise ExecutionError('canary must be one-record SUCCESS')
    for field in ('experiment_id','action_type','adapter','content_hash'):
        if prior[field]!=envelope[field]: raise ExecutionError(f'canary {field} does not match batch')
    if datetime.fromisoformat(envelope['created_at'])-datetime.fromisoformat(prior['created_at'])>timedelta(hours=24): raise ExecutionError('canary is older than 24 hours')
def _assert_rate(connection:sqlite3.Connection,envelope:dict[str,Any])->None:
    start=(datetime.fromisoformat(envelope['created_at'])-timedelta(hours=1)).isoformat()
    row=connection.execute('SELECT COALESCE(SUM(e.batch_size),0) FROM execution_envelopes e JOIN execution_results r ON r.envelope_id=e.id WHERE e.adapter=? AND r.completed_at>=?',(envelope['adapter'],start)).fetchone()
    used=int(row[0])
    limit=min(envelope['rate_limit_per_hour'],ADAPTERS[envelope['adapter']]['max_per_hour'])
    if used+envelope['batch_size']>limit: raise ExecutionError('adapter hourly rate limit would be exceeded')
def _record_circuit(connection:sqlite3.Connection,adapter:str,state:str,reason:str,occurred_at:str)->None:
    ident='XCB-'+canonical_hash([adapter,state,reason,occurred_at]).split(':')[1][:16].upper()
    record={'id':ident,'adapter':adapter,'state':state,'reason':reason,'occurred_at':occurred_at}
    connection.execute('INSERT OR IGNORE INTO execution_circuit_events(id,adapter,state,reason,occurred_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?)',(ident,adapter,state,reason,occurred_at,canonical_json(record),canonical_hash(record),utc_now()))
def execute_simulated(connection:sqlite3.Connection,raw:dict[str,Any], *, completed_at:str|None=None, commit:bool=True)->dict[str,Any]:
    envelope=validate_envelope(raw); install_schema(connection)
    if latest_circuit_state(connection,envelope['adapter'])=='OPEN': raise ExecutionError('adapter circuit breaker is OPEN')
    if connection.execute('SELECT 1 FROM execution_envelopes WHERE idempotency_key=?',(envelope['idempotency_key'],)).fetchone(): raise ExecutionError('idempotency key already consumed')
    _assert_canary(connection,envelope); _assert_rate(connection,envelope)
    when=completed_at or envelope['created_at']; response=simulate(envelope)
    result=validate_result({'id':'XRS-'+canonical_hash([envelope['id'],when]).split(':')[1][:16].upper(),'envelope_id':envelope['id'],'outcome':response['outcome'],'affected_records':response['affected_records'],'spend_usd':0,'external_reference':None,'reversible':ADAPTERS[envelope['adapter']]['reversible'],'completed_at':when,'details':response['details']})
    attempt={'id':'XAT-'+canonical_hash([envelope['id'],1]).split(':')[1][:16].upper(),'envelope_id':envelope['id'],'attempt_no':1,'started_at':envelope['created_at'],'finished_at':when,'status':result['outcome']}
    def op():
        connection.execute('INSERT INTO execution_envelopes(id,experiment_id,action_type,adapter,mode,idempotency_key,batch_size,canary_for_id,content_hash,created_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(envelope['id'],envelope['experiment_id'],envelope['action_type'],envelope['adapter'],envelope['mode'],envelope['idempotency_key'],envelope['batch_size'],envelope['canary_for_id'],envelope['content_hash'],envelope['created_at'],canonical_json(envelope),canonical_hash(envelope),utc_now()))
        connection.execute('INSERT INTO execution_attempts(id,envelope_id,attempt_no,started_at,finished_at,status,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?,?)',(attempt['id'],envelope['id'],1,attempt['started_at'],attempt['finished_at'],attempt['status'],canonical_json(attempt),canonical_hash(attempt),utc_now()))
        connection.execute('INSERT INTO execution_results(id,envelope_id,outcome,affected_records,spend_usd,reversible,completed_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(result['id'],envelope['id'],result['outcome'],result['affected_records'],0,int(result['reversible']),result['completed_at'],canonical_json(result),canonical_hash(result),utc_now()))
        recent=[r[0] for r in connection.execute("SELECT r.outcome FROM execution_results r JOIN execution_envelopes e ON e.id=r.envelope_id WHERE e.adapter=? ORDER BY r.completed_at DESC,r.id DESC LIMIT 3",(envelope['adapter'],))]
        if len(recent)==3 and all(x in {'FAILURE','AMBIGUOUS'} for x in recent): _record_circuit(connection,envelope['adapter'],'OPEN','three consecutive unsafe outcomes',when)
    if commit:
        with connection: op()
    else: op()
    return result
def rollback_simulated(connection:sqlite3.Connection,raw:dict[str,Any], *, fail:bool=False, commit:bool=True)->dict[str,Any]:
    record=validate_rollback(raw); envelope=_row_json(connection,'execution_envelopes',record['envelope_id']); result=_row_json(connection,'execution_results',record['result_id'])
    if result['envelope_id']!=envelope['id']: raise ExecutionError('rollback result does not belong to envelope')
    if connection.execute('SELECT 1 FROM execution_rollbacks WHERE envelope_id=?',(envelope['id'],)).fetchone(): raise ExecutionError('envelope already has rollback record')
    simulated=simulate_rollback(envelope,result,fail=fail)
    if record['outcome']!=simulated['outcome']: raise ExecutionError('rollback outcome does not match simulator')
    record={**record,'details':simulated['details']}
    def op(): connection.execute('INSERT INTO execution_rollbacks(id,envelope_id,result_id,outcome,occurred_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?)',(record['id'],record['envelope_id'],record['result_id'],record['outcome'],record['occurred_at'],canonical_json(record),canonical_hash(record),utc_now()))
    if commit:
        with connection: op()
    else: op()
    return record
def execution_status(connection:sqlite3.Connection,envelope_id:str)->dict[str,Any]:
    env=_row_json(connection,'execution_envelopes',envelope_id)
    row=connection.execute('SELECT record_json FROM execution_results WHERE envelope_id=?',(envelope_id,)).fetchone()
    rollback=connection.execute('SELECT record_json FROM execution_rollbacks WHERE envelope_id=?',(envelope_id,)).fetchone()
    return {'envelope':env,'result':json.loads(row[0]) if row else None,'rollback':json.loads(rollback[0]) if rollback else None,'circuit_state':latest_circuit_state(connection,env['adapter'])}
