from __future__ import annotations
import json, sqlite3, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from robofox_decision import canonical_hash
from robofox_experiment import TruthStoreError, approved_apply, bind_definition, create_approval, detect_collisions, evaluate_criteria, experiment_status, finalize_experiment, install_schema, integrity_report, prepare_manifest, record_execution, record_observation, record_transition, register_experiment

NOW='2026-07-13T10:00:00+05:30'
def db():
    c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
    c.execute('CREATE TABLE sources(id TEXT PRIMARY KEY)')
    c.execute('CREATE TABLE approval_consumptions(approval_id TEXT PRIMARY KEY,action_id TEXT UNIQUE,action_type TEXT,manifest_hash TEXT,payload_hash TEXT,record_type TEXT,record_id TEXT,consumed_at TEXT)')
    install_schema(c); c.execute("INSERT INTO sources(id) VALUES('SRC-EXPERIMENT-01')"); return c
def definition(exp='EXP-VOICE-0001', audience='clinic-madurai-a', start='2026-07-13T10:00:00+05:30', end='2026-07-27T10:00:00+05:30', waiver=None):
    suffix=exp.rsplit('-',1)[-1]
    return {'version':1,'id':exp,'product':'voice-agents','decision_id':f'DEC-VOICE-{suffix}','decision_record_hash':'sha256:'+'1'*64,'candidate_id':f'MOV-VOICE-{suffix}','candidate_hash':'sha256:'+'2'*64,'snapshot_hash':'sha256:'+'3'*64,'decision_status':'CHOSEN','hypothesis':'Clinic owners will book a live demo when shown missed-call recovery.','target_segment':'Independent clinics in Madurai','audience_key':audience,'change_dimensions':['OFFER','MESSAGE'],'primary_metric':'qualified_owner_conversations','secondary_metrics':['demos_booked','complaint_rate'],'minimum_execution':{'unit':'owner_attempts','target':20},'maximum_exposure':{'cash_usd':50,'founder_hours':12,'days_to_signal':14},'planned_start':start,'planned_end':end,'success_criteria':[{'metric':'qualified_owner_conversations','operator':'GTE','threshold':5,'unit':'count','minimum_sample_size':20}],'kill_criteria':[{'metric':'complaint_rate','operator':'GT','threshold':0.001,'unit':'ratio','minimum_sample_size':1}],'hard_stop_conditions':['Any do-not-contact violation','Repeated misleading product claim'],'owner':'Febin','collision_waiver':waiver,'sensitivity':'INTERNAL','registered_at':NOW}
def transition(tid,exp,from_state,to_state,at,reason='Reviewed and approved by founder'):
    return {'version':1,'id':tid,'experiment_id':exp,'from_state':from_state,'to_state':to_state,'reason':reason,'actor':'Febin','occurred_at':at}
def execution(eid,exp,units=10,cash=10,hours=2,at='2026-07-14T10:00:00+05:30'):
    return {'version':1,'id':eid,'experiment_id':exp,'units':units,'cash_spent_usd':cash,'founder_hours':hours,'source_ids':['SRC-EXPERIMENT-01'],'notes':'Synthetic bounded execution','occurred_at':at}
def observation(oid,exp,metric,value,unit,sample,at='2026-07-14T11:00:00+05:30'):
    return {'version':1,'id':oid,'experiment_id':exp,'metric':metric,'value':value,'unit':unit,'sample_size':sample,'denominator':sample,'source_ids':['SRC-EXPERIMENT-01'],'observed_at':at}
def go_live(c,exp='EXP-VOICE-0001'):
    record_transition(c,transition('XTR-VOICE-0001',exp,'DRAFT','REVIEWED','2026-07-13T10:10:00+05:30'))
    record_transition(c,transition('XTR-VOICE-0002',exp,'REVIEWED','APPROVED','2026-07-13T10:20:00+05:30'))
    record_transition(c,transition('XTR-VOICE-0003',exp,'APPROVED','LIVE','2026-07-13T10:30:00+05:30'))
def outcome(exp,criteria,kind='SUCCESS',oid='OUT-VOICE-0001',tid='XTR-VOICE-0099',from_state='LIVE',hard=None):
    return {'version':1,'id':oid,'experiment_id':exp,'outcome':kind,'conclusion':'The bounded experiment produced a decision-grade result.','learning':'Founder-led demonstrations produced measurable commercial learning.','belief_updates':[{'belief':'Clinic owners respond to missed-call recovery proof','previous_state':'ASSUMED','new_state':'OBSERVED','confidence':'MEDIUM','evidence_ids':['OBS-VOICE-0001']}],'evidence_observation_ids':['OBS-VOICE-0001','OBS-VOICE-0002'],'criterion_results':criteria,'triggered_hard_stop':hard,'next_action':'Use this evidence in the next frozen position snapshot.','transition':transition(tid,exp,from_state,{'SUCCESS':'COMPLETED','FAILED':'KILLED','SAFETY_STOP':'KILLED','CANCELLED':'KILLED'}[kind],'2026-07-15T10:00:00+05:30','Finalize from deterministic experiment review')}

class ExperimentOSTests(unittest.TestCase):
    def setUp(self): self.c=db(); register_experiment(self.c,definition())
    def tearDown(self): self.c.close()
    def test_initial_state_is_derived_draft(self): self.assertEqual('DRAFT',experiment_status(self.c,'EXP-VOICE-0001',as_of=NOW)['state'])
    def test_lifecycle_to_live(self): go_live(self.c); self.assertEqual('LIVE',experiment_status(self.c,'EXP-VOICE-0001',as_of='2026-07-14T00:00:00+05:30')['state'])
    def test_illegal_state_jump_fails(self):
        with self.assertRaisesRegex(TruthStoreError,'not allowed'): record_transition(self.c,transition('XTR-BAD-0001','EXP-VOICE-0001','DRAFT','LIVE','2026-07-13T10:10:00+05:30'))
    def test_terminal_transition_requires_finalize(self):
        with self.assertRaisesRegex(TruthStoreError,'terminal states require'): record_transition(self.c,transition('XTR-BAD-0002','EXP-VOICE-0001','DRAFT','KILLED','2026-07-13T10:10:00+05:30'))
    def test_transition_from_state_must_match(self):
        with self.assertRaisesRegex(TruthStoreError,'does not match current state'): record_transition(self.c,transition('XTR-BAD-0003','EXP-VOICE-0001','LIVE','PAUSED','2026-07-13T10:10:00+05:30'))
    def test_execution_requires_live(self):
        with self.assertRaisesRegex(TruthStoreError,'only while experiment is LIVE'): record_execution(self.c,execution('EXE-BAD-0001','EXP-VOICE-0001'))
    def test_exposure_cap_is_enforced(self):
        go_live(self.c); record_execution(self.c,execution('EXE-VOICE-0001','EXP-VOICE-0001',units=10,cash=40,hours=10))
        with self.assertRaisesRegex(TruthStoreError,'cash exposure'): record_execution(self.c,execution('EXE-VOICE-0002','EXP-VOICE-0001',units=1,cash=11,hours=1,at='2026-07-14T12:00:00+05:30'))
    def test_time_to_signal_cap_is_enforced(self):
        go_live(self.c)
        with self.assertRaisesRegex(TruthStoreError,'maximum days to signal'): record_execution(self.c,execution('EXE-LATE-0001','EXP-VOICE-0001',at='2026-08-01T10:00:00+05:30'))
    def test_undeclared_metric_is_rejected(self):
        go_live(self.c)
        with self.assertRaisesRegex(TruthStoreError,'not pre-registered'): record_observation(self.c,observation('OBS-BAD-0001','EXP-VOICE-0001','vanity_impressions',100,'count',100))
    def test_criteria_use_latest_cumulative_observation(self):
        go_live(self.c); record_observation(self.c,observation('OBS-VOICE-0000','EXP-VOICE-0001','qualified_owner_conversations',2,'count',10)); record_observation(self.c,observation('OBS-VOICE-0001','EXP-VOICE-0001','qualified_owner_conversations',6,'count',20,at='2026-07-14T12:00:00+05:30')); record_observation(self.c,observation('OBS-VOICE-0002','EXP-VOICE-0001','complaint_rate',0,'ratio',20,at='2026-07-14T12:05:00+05:30'))
        r=evaluate_criteria(self.c,'EXP-VOICE-0001'); self.assertEqual('MET',r['success'][0]['status']); self.assertEqual('NOT_MET',r['kill'][0]['status'])
    def test_success_requires_minimum_execution(self):
        go_live(self.c); record_execution(self.c,execution('EXE-VOICE-0001','EXP-VOICE-0001',units=10)); record_observation(self.c,observation('OBS-VOICE-0001','EXP-VOICE-0001','qualified_owner_conversations',6,'count',20)); record_observation(self.c,observation('OBS-VOICE-0002','EXP-VOICE-0001','complaint_rate',0,'ratio',20))
        criteria=evaluate_criteria(self.c,'EXP-VOICE-0001')
        with self.assertRaisesRegex(TruthStoreError,'minimum execution'): finalize_experiment(self.c,outcome('EXP-VOICE-0001',criteria))
    def test_success_finalizes_atomically(self):
        go_live(self.c); record_execution(self.c,execution('EXE-VOICE-0001','EXP-VOICE-0001',units=20)); record_observation(self.c,observation('OBS-VOICE-0001','EXP-VOICE-0001','qualified_owner_conversations',6,'count',20)); record_observation(self.c,observation('OBS-VOICE-0002','EXP-VOICE-0001','complaint_rate',0,'ratio',20))
        finalize_experiment(self.c,outcome('EXP-VOICE-0001',evaluate_criteria(self.c,'EXP-VOICE-0001'))); self.assertEqual('COMPLETED',experiment_status(self.c,'EXP-VOICE-0001')['state']); self.assertEqual(1,self.c.execute('SELECT COUNT(*) FROM experiment_outcomes').fetchone()[0])
    def test_kill_criterion_can_stop_before_minimum(self):
        go_live(self.c); record_execution(self.c,execution('EXE-VOICE-0001','EXP-VOICE-0001',units=2)); record_observation(self.c,observation('OBS-VOICE-0001','EXP-VOICE-0001','qualified_owner_conversations',0,'count',2)); record_observation(self.c,observation('OBS-VOICE-0002','EXP-VOICE-0001','complaint_rate',0.5,'ratio',2))
        finalize_experiment(self.c,outcome('EXP-VOICE-0001',evaluate_criteria(self.c,'EXP-VOICE-0001'),kind='FAILED')); self.assertEqual('KILLED',experiment_status(self.c,'EXP-VOICE-0001')['state'])
    def test_safety_stop_requires_preregistered_condition(self):
        go_live(self.c); criteria=evaluate_criteria(self.c,'EXP-VOICE-0001'); raw=outcome('EXP-VOICE-0001',criteria,kind='SAFETY_STOP',hard='Invented stop')
        with self.assertRaisesRegex(TruthStoreError,'pre-registered hard stop'): finalize_experiment(self.c,raw)
    def test_outcome_results_cannot_be_fabricated(self):
        go_live(self.c); record_observation(self.c,observation('OBS-VOICE-0001','EXP-VOICE-0001','qualified_owner_conversations',1,'count',20)); record_observation(self.c,observation('OBS-VOICE-0002','EXP-VOICE-0001','complaint_rate',0,'ratio',20)); criteria=evaluate_criteria(self.c,'EXP-VOICE-0001'); criteria['success'][0]['status']='MET'
        with self.assertRaisesRegex(TruthStoreError,'deterministic evaluation'): finalize_experiment(self.c,outcome('EXP-VOICE-0001',criteria,kind='FAILED'))
    def test_collision_requires_exact_waiver(self):
        raw=definition('EXP-VOICE-0002')
        with self.assertRaisesRegex(TruthStoreError,'collides'): register_experiment(self.c,raw)
        raw['collision_waiver']={'conflicting_experiment_ids':['EXP-VOICE-0001'],'reason':'Same audience is required for a controlled paired test.','isolation_plan':'Use mutually exclusive clinic IDs assigned before launch.'}
        register_experiment(self.c,raw); self.assertEqual(['EXP-VOICE-0001'],detect_collisions(self.c,raw))
    def test_non_overlapping_dates_do_not_collide(self): register_experiment(self.c,definition('EXP-VOICE-0003',start='2026-08-01T10:00:00+05:30',end='2026-08-14T10:00:00+05:30')); self.assertEqual([],detect_collisions(self.c,definition('EXP-VOICE-0004',start='2026-09-01T10:00:00+05:30',end='2026-09-14T10:00:00+05:30')))
    def test_records_are_append_only(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError,'append-only'): self.c.execute("UPDATE experiments SET product='other' WHERE id='EXP-VOICE-0001'")
    def test_integrity_detects_tampering(self):
        self.assertTrue(integrity_report(self.c)['ok']); self.c.execute('DROP TRIGGER experiments_no_update'); self.c.execute("UPDATE experiments SET record_json='{}' WHERE id='EXP-VOICE-0001'"); report=integrity_report(self.c); self.assertFalse(report['ok']); self.assertTrue(any('record hash mismatch' in x for x in report['issues']))

class BindingAndApprovalTests(unittest.TestCase):
    def test_phase2_binding_rejects_unchosen_candidate(self):
        candidate={'candidate_id':'MOV-VOICE-0001','product':'voice-agents','snapshot_hash':'sha256:'+'3'*64,'exposure':{'cash_usd':50,'founder_hours':12,'days_to_signal':14}}
        decision={'decision_id':'DEC-VOICE-0001','product':'voice-agents','snapshot_hash':candidate['snapshot_hash'],'status':'NO_MOVE','chosen_candidate_id':None,'maximum_exposure':candidate['exposure'],'input_hashes':{'candidates':{candidate['candidate_id']:canonical_hash(candidate)}}}
        spec=definition(); [spec.pop(k) for k in ('version','decision_id','decision_record_hash','candidate_id','candidate_hash','snapshot_hash','decision_status')]
        with self.assertRaisesRegex(TruthStoreError,'candidate chosen'): bind_definition(decision,candidate,spec)
    def test_phase2_binding_rejects_exposure_increase(self):
        candidate={'candidate_id':'MOV-VOICE-0001','product':'voice-agents','snapshot_hash':'sha256:'+'3'*64,'exposure':{'cash_usd':50,'founder_hours':12,'days_to_signal':14}}
        decision={'decision_id':'DEC-VOICE-0001','product':'voice-agents','snapshot_hash':candidate['snapshot_hash'],'status':'CHOSEN','chosen_candidate_id':candidate['candidate_id'],'maximum_exposure':candidate['exposure'],'input_hashes':{'candidates':{candidate['candidate_id']:canonical_hash(candidate)}}}
        spec=definition(); [spec.pop(k) for k in ('version','decision_id','decision_record_hash','candidate_id','candidate_hash','snapshot_hash','decision_status')]; spec['maximum_exposure']['cash_usd']=51
        with self.assertRaisesRegex(TruthStoreError,'cash_usd exceeds'): bind_definition(decision,candidate,spec)
    def test_approved_registration_installs_schema_in_existing_truth_database(self):
        c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
        c.execute('CREATE TABLE sources(id TEXT PRIMARY KEY)'); c.execute('CREATE TABLE approval_consumptions(approval_id TEXT PRIMARY KEY,action_id TEXT UNIQUE,action_type TEXT,manifest_hash TEXT,payload_hash TEXT,record_type TEXT,record_id TEXT,consumed_at TEXT)')
        workspace=Path(tempfile.mkdtemp()); (workspace/'workspace.json').write_text(json.dumps({'workspace_id':'WS-EXPERIMENT-INSTALL','public_repo':False}))
        payload=definition(); manifest=prepare_manifest(workspace,'register_experiment_definition',payload,requested_by='tester',task_id='TASK-EXP-INSTALL',created_at='2026-07-13T09:00:00+05:30'); approval=create_approval(manifest,approved_by='founder',approved_at='2026-07-13T09:01:00+05:30',expires_minutes=120)
        approved_apply(c,workspace,'register_experiment_definition',payload,manifest,approval,now='2026-07-13T09:02:00+05:30')
        self.assertEqual(1,c.execute('SELECT COUNT(*) FROM experiments').fetchone()[0]); c.close()
    def test_exact_approval_is_single_use(self):
        c=db(); workspace=Path(tempfile.mkdtemp()); (workspace/'workspace.json').write_text(json.dumps({'workspace_id':'WS-EXPERIMENT-TEST','public_repo':False}))
        payload=definition(); manifest=prepare_manifest(workspace,'register_experiment_definition',payload,requested_by='tester',task_id='TASK-EXP-01',created_at='2026-07-13T09:00:00+05:30'); approval=create_approval(manifest,approved_by='founder',approved_at='2026-07-13T09:01:00+05:30',expires_minutes=120)
        approved_apply(c,workspace,'register_experiment_definition',payload,manifest,approval,now='2026-07-13T09:02:00+05:30')
        self.assertEqual(1,c.execute('SELECT COUNT(*) FROM approval_consumptions').fetchone()[0])
        with self.assertRaises(sqlite3.IntegrityError): approved_apply(c,workspace,'register_experiment_definition',payload,manifest,approval,now='2026-07-13T09:03:00+05:30')
        c.close()
if __name__=='__main__': unittest.main()
