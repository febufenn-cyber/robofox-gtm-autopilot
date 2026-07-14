from __future__ import annotations
import json,sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from robofox_execution import ExecutionError, approved_execute, create_approval, execute_simulated, install_schema, integrity_report, prepare_manifest, rollback_simulated, validate_envelope

NOW='2026-07-14T10:00:00+05:30'
def env(identifier='EXR-TEST-0001',targets=None,**changes):
    targets=targets or ['TGT-TEST-0001']
    value={'id':identifier,'experiment_id':'EXP-TEST-0001','action_type':'PREPARE_CRM_TASK','adapter':'internal.crm_task','mode':'SIMULATOR','idempotency_key':'idem-'+identifier+'-000000','target_keys':targets,'content_hash':'sha256:'+'a'*64,'payload':{'simulate_outcome':'SUCCESS','task_kind':'follow_up'},'batch_size':len(targets),'canary_for_id':None,'maximum_spend_usd':0,'currency':'USD','rate_limit_per_hour':10,'rollback_plan':{'required':True,'strategy':'remove simulated task','timeout_seconds':60},'created_at':NOW,'sensitivity':'INTERNAL'}
    value.update(changes); return value
class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.workspace=Path(self.temp.name); (self.workspace/'truth').mkdir(); (self.workspace/'workspace.json').write_text(json.dumps({'workspace_id':'WS-PHASE4-TEST','public_repo':False})); self.state=self.workspace/'system-state.json'; self.state.write_text(json.dumps({'workspace_id':'WS-PHASE4-TEST','kill_switch':False,'simulation_enabled':True,'external_execution':False})); self.connection=sqlite3.connect(self.workspace/'truth/robofox_truth.sqlite3'); self.connection.row_factory=sqlite3.Row; self.connection.execute('PRAGMA foreign_keys=ON'); install_schema(self.connection)
    def tearDown(self): self.connection.close(); self.temp.cleanup()
    def approval(self,payload,action='execute_simulated_action'):
        m=prepare_manifest(self.workspace,action,payload,requested_by='tester',task_id='TASK-P4',created_at='2026-07-14T09:59:00+05:30'); a=create_approval(m,approved_by='founder',approved_at='2026-07-14T09:59:30+05:30',expires_minutes=10); return m,a
    def test_one_record_canary_succeeds(self):
        result=execute_simulated(self.connection,env()); self.assertEqual(('SUCCESS',1),(result['outcome'],result['affected_records']))
    def test_live_mode_rejected(self):
        with self.assertRaisesRegex(ExecutionError,'only SIMULATOR'): validate_envelope(env(mode='LIVE'))
    def test_direct_identifier_field_rejected(self):
        with self.assertRaisesRegex(ExecutionError,'direct identifier'): validate_envelope(env(payload={'email':'a@b.com'}))
    def test_non_pseudonymous_target_rejected(self):
        with self.assertRaisesRegex(ExecutionError,'pseudonymous'): validate_envelope(env(target_keys=['person@example.com']))
    def test_batch_requires_canary(self):
        with self.assertRaisesRegex(ExecutionError,'requires canary'): validate_envelope(env(targets=['TGT-TEST-0001','TGT-TEST-0002']))
    def test_successful_canary_unlocks_matching_batch(self):
        first=env(); execute_simulated(self.connection,first)
        batch=env('EXR-TEST-0002',['TGT-TEST-0002','TGT-TEST-0003'],canary_for_id=first['id'],created_at='2026-07-14T10:05:00+05:30')
        result=execute_simulated(self.connection,batch,completed_at='2026-07-14T10:05:00+05:30'); self.assertEqual(2,result['affected_records'])
    def test_mismatched_canary_rejected(self):
        first=env(); execute_simulated(self.connection,first)
        batch=env('EXR-TEST-0002',['TGT-TEST-0002','TGT-TEST-0003'],canary_for_id=first['id'],content_hash='sha256:'+'b'*64,created_at='2026-07-14T10:05:00+05:30')
        with self.assertRaisesRegex(ExecutionError,'content_hash'): execute_simulated(self.connection,batch)
    def test_duplicate_idempotency_rejected(self):
        first=env(); execute_simulated(self.connection,first)
        with self.assertRaisesRegex(ExecutionError,'idempotency'): execute_simulated(self.connection,env('EXR-TEST-0002',idempotency_key=first['idempotency_key']))
    def test_rate_limit_enforced(self):
        first=env(rate_limit_per_hour=1); execute_simulated(self.connection,first)
        with self.assertRaisesRegex(ExecutionError,'rate limit'): execute_simulated(self.connection,env('EXR-TEST-0002',rate_limit_per_hour=1,created_at='2026-07-14T10:10:00+05:30'))
    def test_three_failures_open_circuit(self):
        for index in range(3): execute_simulated(self.connection,env(f'EXR-FAIL-000{index}',payload={'simulate_outcome':'FAILURE'},created_at=f'2026-07-14T10:0{index}:00+05:30'))
        with self.assertRaisesRegex(ExecutionError,'circuit breaker'): execute_simulated(self.connection,env('EXR-TEST-9999',created_at='2026-07-14T10:10:00+05:30'))
    def test_irreversible_adapter_cannot_promise_rollback(self):
        bad=env(action_type='SEND_EMAIL',adapter='email',rollback_plan={'required':True,'strategy':'undo send','timeout_seconds':60})
        with self.assertRaisesRegex(ExecutionError,'cannot promise rollback'): validate_envelope(bad)
    def test_simulator_spend_must_be_zero(self):
        with self.assertRaisesRegex(ExecutionError,'cannot authorize spending'): validate_envelope(env(maximum_spend_usd=1))
    def test_exact_approval_atomic_consumption(self):
        payload=env(); manifest,approval=self.approval(payload); result=approved_execute(self.connection,self.workspace,self.state,payload,manifest,approval,now=NOW); self.assertEqual('SUCCESS',result['outcome']); self.assertEqual(1,self.connection.execute('SELECT COUNT(*) FROM execution_approval_consumptions').fetchone()[0])
    def test_payload_change_invalidates_approval(self):
        payload=env(); manifest,approval=self.approval(payload); changed={**payload,'content_hash':'sha256:'+'c'*64}
        with self.assertRaisesRegex(ExecutionError,'exact execution payload'): approved_execute(self.connection,self.workspace,self.state,changed,manifest,approval,now=NOW)
    def test_kill_switch_blocks(self):
        payload=env(); manifest,approval=self.approval(payload); self.state.write_text(json.dumps({'workspace_id':'WS-PHASE4-TEST','kill_switch':True,'simulation_enabled':True,'external_execution':False}))
        with self.assertRaisesRegex(ExecutionError,'kill switch'): approved_execute(self.connection,self.workspace,self.state,payload,manifest,approval,now=NOW)
    def test_external_execution_flag_blocks(self):
        payload=env(); manifest,approval=self.approval(payload); self.state.write_text(json.dumps({'workspace_id':'WS-PHASE4-TEST','kill_switch':False,'simulation_enabled':True,'external_execution':True}))
        with self.assertRaisesRegex(ExecutionError,'must remain false'): approved_execute(self.connection,self.workspace,self.state,payload,manifest,approval,now=NOW)
    def test_replay_approval_rejected_by_database(self):
        payload=env(); manifest,approval=self.approval(payload); approved_execute(self.connection,self.workspace,self.state,payload,manifest,approval,now=NOW)
        payload2=env('EXR-TEST-0002',idempotency_key='new-idempotency-key-0002'); manifest2,approval2=self.approval(payload2); approval2['approval_id']=approval['approval_id']
        with self.assertRaises(sqlite3.IntegrityError): approved_execute(self.connection,self.workspace,self.state,payload2,manifest2,approval2,now=NOW)
    def test_rollback_is_append_only(self):
        payload=env(); result=execute_simulated(self.connection,payload); rollback={'id':'XRB-TEST-0001','envelope_id':payload['id'],'result_id':result['id'],'outcome':'ROLLED_BACK','occurred_at':'2026-07-14T10:10:00+05:30','details':{}}
        stored=rollback_simulated(self.connection,rollback); self.assertEqual('ROLLED_BACK',stored['outcome'])
        with self.assertRaisesRegex(sqlite3.IntegrityError,'append-only'): self.connection.execute('DELETE FROM execution_rollbacks')
    def test_integrity_detects_tampering(self):
        execute_simulated(self.connection,env()); self.connection.execute('DROP TRIGGER execution_results_no_update'); self.connection.execute("UPDATE execution_results SET record_json='{}'")
        report=integrity_report(self.connection); self.assertFalse(report['ok']); self.assertTrue(any('record hash mismatch' in x for x in report['issues']))
if __name__=='__main__': unittest.main()
