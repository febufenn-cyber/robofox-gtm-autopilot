from __future__ import annotations
import sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from robofox_ops import OpsError,authorize,claim,complete,create_backup,enqueue,fail,heartbeat,install,issue_session,readiness_report,redact,restore_backup,status,validate_environment,verify_session

class OpsTests(unittest.TestCase):
 def test_session_and_rbac(self):
  token=issue_session('u','reviewer',b's'*32,1000);session=verify_session(token,b's'*32,1001);authorize(session,'review')
  with self.assertRaisesRegex(OpsError,'permission denied'):authorize(session,'admin')
 def test_tampered_session_rejected(self):
  token=issue_session('u','read_only',b's'*32,1000);token=token[:-1]+('A' if token[-1]!='A' else 'B')
  with self.assertRaisesRegex(OpsError,'signature'):verify_session(token,b's'*32,1001)
 def test_expired_session_rejected(self):
  token=issue_session('u','read_only',b's'*32,1000,60)
  with self.assertRaisesRegex(OpsError,'expired'):verify_session(token,b's'*32,1060)
 def test_recursive_redaction(self):
  self.assertEqual({'token':'[REDACTED]','items':[{'phone':'[REDACTED]'}]},redact({'token':'x','items':[{'phone':'y'}]}))
 def queue(self):
  temporary=tempfile.TemporaryDirectory();connection=sqlite3.connect(Path(temporary.name)/'q.sqlite');install(connection);return temporary,connection
 def test_queue_duplicate_idempotency(self):
  t,c=self.queue();enqueue(c,'same-key','job',{},1)
  with self.assertRaises(sqlite3.IntegrityError):enqueue(c,'same-key','job',{},2)
  c.close();t.cleanup()
 def test_single_worker_lease(self):
  t,c=self.queue();job=enqueue(c,'key-1','job',{},1);self.assertEqual(job,claim(c,'worker-a',2));self.assertIsNone(claim(c,'worker-b',2));complete(c,job,'worker-a',3);self.assertEqual('DONE',status(c,job)['status']);c.close();t.cleanup()
 def test_irreversible_job_dead_letters(self):
  t,c=self.queue();job=enqueue(c,'key-2','external',{},1,irreversible=True);claim(c,'worker',2);fail(c,job,'worker',3,'ambiguous');self.assertEqual('DEAD',status(c,job)['status']);self.assertEqual(1,status(c,job)['max_attempts']);c.close();t.cleanup()
 def test_heartbeat_wrong_owner(self):
  t,c=self.queue();job=enqueue(c,'key-3','job',{},1);claim(c,'owner',2)
  with self.assertRaisesRegex(OpsError,'lease lost'):heartbeat(c,job,'other',3)
  c.close();t.cleanup()
 def test_backup_restore(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);db=root/'source.sqlite';c=sqlite3.connect(db);c.execute('CREATE TABLE x(v TEXT)');c.execute("INSERT INTO x VALUES('ok')");c.commit();c.close();backup=root/'backup.rfx';restored=root/'restored.sqlite';create_backup(db,backup,'correct horse battery staple','schema-7');restore_backup(backup,restored,'correct horse battery staple','schema-7');c=sqlite3.connect(restored);self.assertEqual('ok',c.execute('SELECT v FROM x').fetchone()[0]);c.close()
 def test_wrong_backup_key_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);db=root/'source.sqlite';c=sqlite3.connect(db);c.execute('CREATE TABLE x(v TEXT)');c.commit();c.close();backup=root/'backup.rfx';create_backup(db,backup,'correct horse battery staple','schema-7')
   with self.assertRaisesRegex(OpsError,'authentication failed'):restore_backup(backup,root/'out.sqlite','wrong password value','schema-7')
 def test_environment_mixing_rejected(self):
  self.assertTrue(validate_environment({'environment':'production','workspace':'/tmp/test-workspace','autonomous_deploy':False}))
  self.assertTrue(validate_environment({'environment':'staging','workspace':'/private/prod-workspace','autonomous_deploy':False}))
 def test_production_autonomous_deploy_rejected(self):
  self.assertIn('production deployment cannot be autonomous',validate_environment({'environment':'production','workspace':'/private/live','autonomous_deploy':True}))
 def test_v1_ready_but_phase8_deferred(self):
  report=readiness_report({'rbac':True,'secret_redaction':True,'queue_deduplication':True,'backup_restore':True,'staging_rollback':True,'incident_runbooks':True,'phase0_7_gate':True});self.assertTrue(report['v1_ready']);self.assertFalse(report['phase8_ready'])

if __name__=='__main__':unittest.main()
