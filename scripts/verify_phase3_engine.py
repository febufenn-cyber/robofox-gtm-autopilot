#!/usr/bin/env python3
"""Smoke-verify the Phase 3 state machine and immutable experiment ledger."""
from __future__ import annotations
import sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from robofox_experiment import evaluate_criteria, experiment_status, finalize_experiment, install_schema, integrity_report, record_execution, record_observation, record_transition, register_experiment

def verify()->list[str]:
    errors=[]; c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
    c.execute('CREATE TABLE sources(id TEXT PRIMARY KEY)'); c.execute("INSERT INTO sources VALUES('SRC-PHASE3-SMOKE')"); install_schema(c)
    definition={'version':1,'id':'EXP-PHASE3-SMOKE','product':'voice-agents','decision_id':'DEC-PHASE3-SMOKE','decision_record_hash':'sha256:'+'1'*64,'candidate_id':'MOV-PHASE3-SMOKE','candidate_hash':'sha256:'+'2'*64,'snapshot_hash':'sha256:'+'3'*64,'decision_status':'CHOSEN','hypothesis':'A bounded demonstration produces qualified conversations.','target_segment':'Synthetic clinics','audience_key':'synthetic-audience','change_dimensions':['OFFER'],'primary_metric':'qualified_conversations','secondary_metrics':['complaint_rate'],'minimum_execution':{'unit':'attempts','target':2},'maximum_exposure':{'cash_usd':10,'founder_hours':2,'days_to_signal':7},'planned_start':'2026-07-13T10:00:00+05:30','planned_end':'2026-07-20T10:00:00+05:30','success_criteria':[{'metric':'qualified_conversations','operator':'GTE','threshold':1,'unit':'count','minimum_sample_size':2}],'kill_criteria':[{'metric':'complaint_rate','operator':'GT','threshold':0.1,'unit':'ratio','minimum_sample_size':1}],'hard_stop_conditions':['Any consent violation'],'owner':'synthetic','collision_waiver':None,'sensitivity':'INTERNAL','registered_at':'2026-07-13T10:00:00+05:30'}
    register_experiment(c,definition)
    for item in ({'version':1,'id':'XTR-PHASE3-0001','experiment_id':definition['id'],'from_state':'DRAFT','to_state':'REVIEWED','reason':'Synthetic review','actor':'tester','occurred_at':'2026-07-13T10:01:00+05:30'},{'version':1,'id':'XTR-PHASE3-0002','experiment_id':definition['id'],'from_state':'REVIEWED','to_state':'APPROVED','reason':'Synthetic approval','actor':'tester','occurred_at':'2026-07-13T10:02:00+05:30'},{'version':1,'id':'XTR-PHASE3-0003','experiment_id':definition['id'],'from_state':'APPROVED','to_state':'LIVE','reason':'Synthetic launch record only','actor':'tester','occurred_at':'2026-07-13T10:03:00+05:30'}): record_transition(c,item)
    record_execution(c,{'version':1,'id':'EXE-PHASE3-0001','experiment_id':definition['id'],'units':2,'cash_spent_usd':1,'founder_hours':1,'source_ids':['SRC-PHASE3-SMOKE'],'notes':'Synthetic execution','occurred_at':'2026-07-14T10:00:00+05:30'})
    record_observation(c,{'version':1,'id':'OBS-PHASE3-0001','experiment_id':definition['id'],'metric':'qualified_conversations','value':1,'unit':'count','sample_size':2,'denominator':2,'source_ids':['SRC-PHASE3-SMOKE'],'observed_at':'2026-07-14T11:00:00+05:30'})
    record_observation(c,{'version':1,'id':'OBS-PHASE3-0002','experiment_id':definition['id'],'metric':'complaint_rate','value':0,'unit':'ratio','sample_size':2,'denominator':2,'source_ids':['SRC-PHASE3-SMOKE'],'observed_at':'2026-07-14T11:01:00+05:30'})
    criteria=evaluate_criteria(c,definition['id'])
    final={'version':1,'id':'OUT-PHASE3-SMOKE','experiment_id':definition['id'],'outcome':'SUCCESS','conclusion':'Synthetic smoke result.','learning':'The deterministic experiment path completed.','belief_updates':[{'belief':'Bounded experiment flow works','previous_state':'ASSUMED','new_state':'VERIFIED','confidence':'HIGH','evidence_ids':['OBS-PHASE3-0001']}],'evidence_observation_ids':['OBS-PHASE3-0001','OBS-PHASE3-0002'],'criterion_results':criteria,'triggered_hard_stop':None,'next_action':'Use the verified Phase 3 engine.','transition':{'version':1,'id':'XTR-PHASE3-0099','experiment_id':definition['id'],'from_state':'LIVE','to_state':'COMPLETED','reason':'Deterministic synthetic finalization','actor':'tester','occurred_at':'2026-07-15T10:00:00+05:30'}}
    finalize_experiment(c,final)
    if experiment_status(c,definition['id'])['state']!='COMPLETED': errors.append('smoke experiment did not reach COMPLETED')
    report=integrity_report(c)
    if not report['ok']: errors.extend(report['issues'])
    c.close(); return errors

def main()->int:
    errors=verify()
    if errors:
        print('PHASE3 ENGINE: FAIL'); [print(f'- {x}') for x in errors]; return 1
    print('PHASE3 ENGINE: PASS')
    print('- registration, state machine, exposure, observations, criteria, finalization, integrity')
    return 0
if __name__=='__main__': raise SystemExit(main())
