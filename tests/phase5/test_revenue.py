from __future__ import annotations
import sqlite3,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from robofox_revenue import *
def ent(i,k,a=None):return {'id':i,'kind':k,'account_id':a,'segment':'clinic','region':'Madurai','created_at':'2026-07-14T10:00:00+05:30','source':'SYNTHETIC','external_key_hash':'sha256:'+'a'*64,'status':'ACTIVE','metadata':{}}
def ev(i,stage,at='2026-07-14T11:00:00+05:30',**kw):
 r={'id':i,'opportunity_id':'OPP-TEST-0001','account_id':'ACC-TEST-0001','stage':stage,'occurred_at':at,'source':'SYNTHETIC','experiment_id':None,'channel':'founder','first_touch':'referral','self_reported_source':'owner','influencing_channels':['whatsapp'],'conversion_touch':'demo','consent_status':'EXISTING_RELATIONSHIP','metadata':{}};r.update(kw);return r
class T(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.c=sqlite3.connect(Path(self.t.name)/'x');self.c.row_factory=sqlite3.Row;self.c.execute('PRAGMA foreign_keys=ON');install_schema(self.c);add_entity(self.c,ent('ACC-TEST-0001','ACCOUNT'));add_entity(self.c,ent('OPP-TEST-0001','OPPORTUNITY','ACC-TEST-0001'))
 def tearDown(self):self.c.close();self.t.cleanup()
 def test_direct_identity_rejected(self):
  with self.assertRaisesRegex(RevenueError,'direct identity'):validate_entity({**ent('CNT-TEST-0001','CONTACT','ACC-TEST-0001'),'metadata':{'email':'x'}})
 def test_duplicate_entity_rejected(self):
  with self.assertRaises(sqlite3.IntegrityError):add_entity(self.c,ent('ACC-TEST-0001','ACCOUNT'))
 def test_multitouch_separate(self):
  add_event(self.c,ev('REV-TEST-0001','LEAD'));a=attribution(self.c,'OPP-TEST-0001');self.assertEqual(('referral','owner',['whatsapp'],'demo'),(a['first_touch'],a['self_reported_source'],a['influencing_channels'],a['conversion_touch']))
 def test_stage_regression_exception(self):
  add_event(self.c,ev('REV-TEST-0001','DEMO'));add_event(self.c,ev('REV-TEST-0002','QUALIFIED','2026-07-14T12:00:00+05:30'));self.assertEqual('STAGE_REGRESSION',stage_exceptions(self.c,'OPP-TEST-0001')[0]['code'])
 def test_won_without_revenue(self):
  add_event(self.c,ev('REV-TEST-0001','WON'));self.assertIn('WON_WITHOUT_REVENUE',reconcile(self.c,'OPP-TEST-0001')['exceptions'])
 def test_currency_mismatch(self):
  add_payment(self.c,{'id':'PAY-TEST-0001','opportunity_id':'OPP-TEST-0001','amount':100,'currency':'USD','kind':'RECEIVED','occurred_at':'2026-07-14T12:00:00+05:30','source_id':'x','metadata':{}});add_payment(self.c,{'id':'PAY-TEST-0002','opportunity_id':'OPP-TEST-0001','amount':100,'currency':'INR','kind':'RECEIVED','occurred_at':'2026-07-14T12:01:00+05:30','source_id':'y','metadata':{}});self.assertIn('CURRENCY_MISMATCH',reconcile(self.c,'OPP-TEST-0001')['exceptions'])
 def test_prohibited_attribute(self):
  with self.assertRaisesRegex(RevenueError,'prohibited'):qualify({'segment_match':True,'pain_signal':True,'authority_signal':True,'urgency_signal':True,'budget_signal':True,'consent_status':'OPTED_IN','caste':'x'})
 def test_contact_restriction(self):self.assertEqual('DISQUALIFIED',qualify({'segment_match':True,'pain_signal':True,'authority_signal':True,'urgency_signal':True,'budget_signal':True,'consent_status':'DO_NOT_CONTACT'})['status'])
 def test_qualification_explainable(self):
  q=qualify({'segment_match':True,'pain_signal':True,'authority_signal':True,'urgency_signal':False,'budget_signal':False,'consent_status':'OPTED_IN'});self.assertEqual('QUALIFIED',q['status']);self.assertIn('pain_signal',q['reasons'])
 def test_read_only_required(self):
  with self.assertRaisesRegex(RevenueError,'READ_ONLY'):ingest_snapshot(self.c,{'mode':'WRITE','source':'HUBSPOT','cursor':'1','records':[]})
 def test_cursor_dedupe(self):
  snap={'mode':'READ_ONLY','source':'HUBSPOT','cursor':'c1','records':[]};ingest_snapshot(self.c,snap)
  with self.assertRaises(sqlite3.IntegrityError):ingest_snapshot(self.c,snap)
 def test_append_only(self):
  with self.assertRaisesRegex(sqlite3.IntegrityError,'append-only'):self.c.execute("UPDATE commercial_entities SET status='X'")
 def test_integrity_tamper(self):
  self.c.execute('DROP TRIGGER entities_no_update');self.c.execute("UPDATE commercial_entities SET record_json='{}' WHERE id='ACC-TEST-0001'");self.assertFalse(integrity(self.c)['ok'])
if __name__=='__main__':unittest.main()
