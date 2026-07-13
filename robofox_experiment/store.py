"""Append-only experiment state machine stored in the private truth ledger."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from robofox_truth.store import utc_now
from robofox_truth.validation import TruthStoreError, canonical_json, record_hash
from .constants import ACTIVE_STATES, GENERIC_TRANSITIONS, OUTCOME_TO_STATE, TERMINAL_STATES
from .validation import validate_definition, validate_execution, validate_observation, validate_outcome, validate_transition


def install_schema(connection: sqlite3.Connection, migration_path: Path | None=None) -> None:
    path=migration_path or Path(__file__).resolve().parent/'migrations/001_experiment_operating_system.sql'
    connection.executescript(path.read_text(encoding='utf-8'))
    connection.commit()

def _write(connection:sqlite3.Connection, op:Callable[[],None], *, commit:bool)->None:
    if commit:
        with connection: op()
    else: op()
def _definition(connection:sqlite3.Connection, experiment_id:str)->dict[str,Any]:
    row=connection.execute('SELECT record_json FROM experiments WHERE id=?',(experiment_id,)).fetchone()
    if row is None: raise TruthStoreError(f'experiment does not exist: {experiment_id}')
    return json.loads(row[0])
def _current_state(connection:sqlite3.Connection, experiment_id:str)->str:
    _definition(connection,experiment_id)
    row=connection.execute('SELECT to_state FROM experiment_transitions WHERE experiment_id=? ORDER BY occurred_at DESC,id DESC LIMIT 1',(experiment_id,)).fetchone()
    return row[0] if row else 'DRAFT'
def _latest_transition_time(connection:sqlite3.Connection, experiment_id:str)->datetime|None:
    row=connection.execute('SELECT occurred_at FROM experiment_transitions WHERE experiment_id=? ORDER BY occurred_at DESC,id DESC LIMIT 1',(experiment_id,)).fetchone()
    return datetime.fromisoformat(row[0]) if row else None
def _live_started_at(connection:sqlite3.Connection, experiment_id:str)->datetime|None:
    row=connection.execute("SELECT occurred_at FROM experiment_transitions WHERE experiment_id=? AND to_state='LIVE' ORDER BY occurred_at,id LIMIT 1",(experiment_id,)).fetchone()
    return datetime.fromisoformat(row[0]) if row else None
def _source_ids_exist(connection:sqlite3.Connection, ids:list[str])->None:
    if not ids: return
    try:
        marks=','.join('?' for _ in ids); found={x[0] for x in connection.execute(f'SELECT id FROM sources WHERE id IN ({marks})',ids)}
    except sqlite3.OperationalError as exc: raise TruthStoreError('truth sources table is unavailable') from exc
    missing=sorted(set(ids)-found)
    if missing: raise TruthStoreError(f'missing sources references: {missing}')
def _intervals_overlap(a_start:str,a_end:str,b_start:str,b_end:str)->bool:
    return datetime.fromisoformat(a_start)<=datetime.fromisoformat(b_end) and datetime.fromisoformat(b_start)<=datetime.fromisoformat(a_end)
def detect_collisions(connection:sqlite3.Connection, definition:dict[str,Any])->list[str]:
    conflicts=[]
    for row in connection.execute('SELECT id,record_json FROM experiments WHERE product=? AND audience_key=?',(definition['product'],definition['audience_key'])):
        other=json.loads(row['record_json'] if isinstance(row,sqlite3.Row) else row[1])
        if other['id']==definition['id']: continue
        if _current_state(connection,other['id']) in TERMINAL_STATES: continue
        if not _intervals_overlap(definition['planned_start'],definition['planned_end'],other['planned_start'],other['planned_end']): continue
        if set(definition['change_dimensions']) & set(other['change_dimensions']): conflicts.append(other['id'])
    return sorted(conflicts)
def register_experiment(connection:sqlite3.Connection, raw:dict[str,Any], *, commit:bool=True)->str:
    record=validate_definition(raw); conflicts=detect_collisions(connection,record); waiver=record['collision_waiver']
    if conflicts:
        if waiver is None: raise TruthStoreError(f'experiment collides with active experiments: {conflicts}')
        if waiver['conflicting_experiment_ids']!=conflicts: raise TruthStoreError('collision waiver must name exactly the detected experiments')
    elif waiver is not None: raise TruthStoreError('collision waiver supplied but no collision exists')
    digest=record_hash(record)
    def op(): connection.execute('INSERT INTO experiments(id,product,decision_id,candidate_id,audience_key,planned_start,planned_end,change_dimensions_json,primary_metric,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(record['id'],record['product'],record['decision_id'],record['candidate_id'],record['audience_key'],record['planned_start'],record['planned_end'],canonical_json(record['change_dimensions']),record['primary_metric'],canonical_json(record),digest,utc_now()))
    _write(connection,op,commit=commit); return record['id']
def record_transition(connection:sqlite3.Connection, raw:dict[str,Any], *, commit:bool=True)->str:
    record=validate_transition(raw); current=_current_state(connection,record['experiment_id'])
    if record['from_state']!=current: raise TruthStoreError(f'transition from_state {record["from_state"]} does not match current state {current}')
    if (record['from_state'],record['to_state']) not in GENERIC_TRANSITIONS: raise TruthStoreError('transition is not allowed; terminal states require finalize_experiment')
    occurred=datetime.fromisoformat(record['occurred_at']); latest=_latest_transition_time(connection,record['experiment_id']); definition=_definition(connection,record['experiment_id'])
    if occurred<datetime.fromisoformat(definition['registered_at']): raise TruthStoreError('transition predates experiment registration')
    if latest is not None and occurred<=latest: raise TruthStoreError('transition timestamps must be strictly increasing')
    digest=record_hash(record)
    def op(): connection.execute('INSERT INTO experiment_transitions(id,experiment_id,from_state,to_state,occurred_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?)',(record['id'],record['experiment_id'],record['from_state'],record['to_state'],record['occurred_at'],canonical_json(record),digest,utc_now()))
    _write(connection,op,commit=commit); return record['id']
def _totals(connection:sqlite3.Connection, experiment_id:str)->dict[str,float|int]:
    row=connection.execute('SELECT COALESCE(SUM(units),0),COALESCE(SUM(cash_spent_usd),0),COALESCE(SUM(founder_hours),0) FROM experiment_executions WHERE experiment_id=?',(experiment_id,)).fetchone()
    return {'units':int(row[0]),'cash_spent_usd':float(row[1]),'founder_hours':float(row[2])}
def record_execution(connection:sqlite3.Connection, raw:dict[str,Any], *, commit:bool=True)->str:
    record=validate_execution(raw); definition=_definition(connection,record['experiment_id']); state=_current_state(connection,record['experiment_id'])
    if state!='LIVE': raise TruthStoreError('execution may be recorded only while experiment is LIVE')
    _source_ids_exist(connection,record['source_ids']); totals=_totals(connection,record['experiment_id']); limit=definition['maximum_exposure']
    if totals['cash_spent_usd']+record['cash_spent_usd']>limit['cash_usd']+1e-9: raise TruthStoreError('cash exposure would exceed experiment maximum')
    if totals['founder_hours']+record['founder_hours']>limit['founder_hours']+1e-9: raise TruthStoreError('founder-hour exposure would exceed experiment maximum')
    live=_live_started_at(connection,record['experiment_id']); occurred=datetime.fromisoformat(record['occurred_at'])
    if live is None or occurred<live: raise TruthStoreError('execution event predates LIVE state')
    if occurred>live+timedelta(days=limit['days_to_signal']): raise TruthStoreError('execution event exceeds maximum days to signal')
    digest=record_hash(record)
    def op(): connection.execute('INSERT INTO experiment_executions(id,experiment_id,units,cash_spent_usd,founder_hours,occurred_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?,?)',(record['id'],record['experiment_id'],record['units'],record['cash_spent_usd'],record['founder_hours'],record['occurred_at'],canonical_json(record),digest,utc_now()))
    _write(connection,op,commit=commit); return record['id']
def _declared_metrics(definition:dict[str,Any])->set[str]: return {definition['primary_metric'],*definition['secondary_metrics']}
def record_observation(connection:sqlite3.Connection, raw:dict[str,Any], *, commit:bool=True)->str:
    record=validate_observation(raw); definition=_definition(connection,record['experiment_id']); state=_current_state(connection,record['experiment_id'])
    if state not in {'LIVE','PAUSED'}: raise TruthStoreError('observations require a LIVE or PAUSED experiment')
    if record['metric'] not in _declared_metrics(definition): raise TruthStoreError('observation metric was not pre-registered')
    expected_units={c['unit'] for c in definition['success_criteria']+definition['kill_criteria'] if c['metric']==record['metric']}
    if expected_units and record['unit'] not in expected_units: raise TruthStoreError('observation unit does not match pre-registered criteria')
    _source_ids_exist(connection,record['source_ids']); live=_live_started_at(connection,record['experiment_id']); observed=datetime.fromisoformat(record['observed_at'])
    if live is None or observed<live: raise TruthStoreError('observation predates LIVE state')
    digest=record_hash(record)
    def op(): connection.execute('INSERT INTO experiment_observations(id,experiment_id,metric,value,unit,sample_size,observed_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(record['id'],record['experiment_id'],record['metric'],record['value'],record['unit'],record['sample_size'],record['observed_at'],canonical_json(record),digest,utc_now()))
    _write(connection,op,commit=commit); return record['id']
def _criterion_met(value:float,operator:str,threshold:float)->bool:
    return {'GTE':value>=threshold,'LTE':value<=threshold,'GT':value>threshold,'LT':value<threshold,'EQ':value==threshold}[operator]
def evaluate_criteria(connection:sqlite3.Connection, experiment_id:str)->dict[str,list[dict[str,Any]]]:
    definition=_definition(connection,experiment_id); result={'success':[],'kill':[]}
    for group,key in ((definition['success_criteria'],'success'),(definition['kill_criteria'],'kill')):
        for criterion in group:
            row=connection.execute('SELECT id,value,unit,sample_size FROM experiment_observations WHERE experiment_id=? AND metric=? ORDER BY observed_at DESC,id DESC LIMIT 1',(experiment_id,criterion['metric'])).fetchone()
            if row is None or row['sample_size']<criterion['minimum_sample_size']:
                status='INSUFFICIENT_DATA'; obs_id=row['id'] if row else None; value=row['value'] if row else None; sample=row['sample_size'] if row else 0
            else:
                if row['unit']!=criterion['unit']: raise TruthStoreError('latest observation unit differs from criterion unit')
                status='MET' if _criterion_met(float(row['value']),criterion['operator'],float(criterion['threshold'])) else 'NOT_MET'; obs_id=row['id']; value=float(row['value']); sample=int(row['sample_size'])
            result[key].append({**criterion,'observation_id':obs_id,'observed_value':value,'sample_size':sample,'status':status})
    return result
def finalize_experiment(connection:sqlite3.Connection, raw:dict[str,Any], *, commit:bool=True)->str:
    record=validate_outcome(raw); definition=_definition(connection,record['experiment_id']); current=_current_state(connection,record['experiment_id']); transition=record['transition']
    if transition['experiment_id']!=record['experiment_id'] or transition['from_state']!=current: raise TruthStoreError('outcome transition does not match current experiment state')
    if transition['to_state']!=OUTCOME_TO_STATE[record['outcome']]: raise TruthStoreError('outcome transition terminal state is invalid')
    if record['outcome'] in {'SUCCESS','FAILED','SAFETY_STOP'} and current not in {'LIVE','PAUSED'}: raise TruthStoreError('active experiment state is required for this outcome')
    if record['outcome']=='CANCELLED' and current not in {'DRAFT','REVIEWED','APPROVED','LIVE','PAUSED'}: raise TruthStoreError('experiment cannot be cancelled from its current state')
    latest=_latest_transition_time(connection,record['experiment_id']); occurred=datetime.fromisoformat(transition['occurred_at'])
    if latest is not None and occurred<=latest: raise TruthStoreError('terminal transition timestamp must follow prior transitions')
    computed=evaluate_criteria(connection,record['experiment_id'])
    if canonical_json(computed)!=canonical_json(record['criterion_results']): raise TruthStoreError('criterion_results do not match deterministic evaluation')
    totals=_totals(connection,record['experiment_id']); minimum_reached=totals['units']>=definition['minimum_execution']['target']; success_all=all(x['status']=='MET' for x in computed['success']); kill_any=any(x['status']=='MET' for x in computed['kill'])
    if record['outcome']=='SUCCESS' and (not minimum_reached or not success_all): raise TruthStoreError('SUCCESS requires minimum execution and every success criterion MET')
    if record['outcome']=='FAILED' and not (kill_any or (minimum_reached and not success_all)): raise TruthStoreError('FAILED requires a met kill criterion or completed minimum execution without success')
    if record['outcome']=='SAFETY_STOP':
        if record['triggered_hard_stop'] not in definition['hard_stop_conditions']: raise TruthStoreError('SAFETY_STOP must name a pre-registered hard stop condition')
    elif record['triggered_hard_stop'] is not None: raise TruthStoreError('triggered_hard_stop is only valid for SAFETY_STOP')
    known={row[0] for row in connection.execute('SELECT id FROM experiment_observations WHERE experiment_id=?',(record['experiment_id'],))}
    if not set(record['evidence_observation_ids'])<=known: raise TruthStoreError('outcome references unknown experiment observations')
    required_obs={x['observation_id'] for group in computed.values() for x in group if x['observation_id'] is not None}
    if record['outcome'] in {'SUCCESS','FAILED'} and not required_obs<=set(record['evidence_observation_ids']): raise TruthStoreError('outcome evidence must include observations used by criteria')
    outcome_hash=record_hash(record); transition_hash=record_hash(transition)
    def op():
        connection.execute('INSERT INTO experiment_outcomes(id,experiment_id,outcome,occurred_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?)',(record['id'],record['experiment_id'],record['outcome'],transition['occurred_at'],canonical_json(record),outcome_hash,utc_now()))
        connection.execute('INSERT INTO experiment_transitions(id,experiment_id,from_state,to_state,occurred_at,record_json,record_hash,inserted_at) VALUES(?,?,?,?,?,?,?,?)',(transition['id'],transition['experiment_id'],transition['from_state'],transition['to_state'],transition['occurred_at'],canonical_json(transition),transition_hash,utc_now()))
    _write(connection,op,commit=commit); return record['id']
def experiment_status(connection:sqlite3.Connection, experiment_id:str, *, as_of:str|None=None)->dict[str,Any]:
    definition=_definition(connection,experiment_id); state=_current_state(connection,experiment_id); totals=_totals(connection,experiment_id); criteria=evaluate_criteria(connection,experiment_id); live=_live_started_at(connection,experiment_id)
    now=datetime.fromisoformat(as_of) if as_of else datetime.fromisoformat(utc_now().replace('Z','+00:00'))
    deadline=live+timedelta(days=definition['maximum_exposure']['days_to_signal']) if live else None
    return {'experiment_id':experiment_id,'product':definition['product'],'state':state,'minimum_execution':definition['minimum_execution'],'execution_totals':totals,'minimum_execution_reached':totals['units']>=definition['minimum_execution']['target'],'maximum_exposure':definition['maximum_exposure'],'remaining_exposure':{'cash_usd':max(0,definition['maximum_exposure']['cash_usd']-totals['cash_spent_usd']),'founder_hours':max(0,definition['maximum_exposure']['founder_hours']-totals['founder_hours'])},'signal_deadline':deadline.isoformat() if deadline else None,'time_limit_reached':bool(deadline and now>deadline),'criteria':criteria,'collision_waiver':definition['collision_waiver']}

INSERT_FUNCTIONS={'experiment':register_experiment,'transition':record_transition,'execution':record_execution,'observation':record_observation,'outcome':finalize_experiment}
