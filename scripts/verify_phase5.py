#!/usr/bin/env python3
from __future__ import annotations
import sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from robofox_revenue import *
REQUIRED=['PHASE5.md','policies/revenue-operations-policy.md','robofox_revenue/validation.py','robofox_revenue/store.py','robofox_revenue/qualification.py','robofox_revenue/ingest.py','schemas/commercial-entity.schema.json','schemas/lifecycle-event.schema.json','schemas/revenue-record.schema.json','schemas/qualification-decision.schema.json']
def entity(i,k,a=None):return {'id':i,'kind':k,'account_id':a,'segment':'clinic','region':'Madurai','created_at':'2026-07-14T10:00:00+05:30','source':'SYNTHETIC','external_key_hash':'sha256:'+'a'*64,'status':'ACTIVE','metadata':{}}
def verify():
 errors=[f'missing {x}' for x in REQUIRED if not (ROOT/x).is_file()]
 with tempfile.TemporaryDirectory() as d:
  c=sqlite3.connect(Path(d)/'x.db');c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');install_schema(c);add_entity(c,entity('ACC-SMOKE-0001','ACCOUNT'));add_entity(c,entity('OPP-SMOKE-0001','OPPORTUNITY','ACC-SMOKE-0001'));add_event(c,{'id':'REV-SMOKE-0001','opportunity_id':'OPP-SMOKE-0001','account_id':'ACC-SMOKE-0001','stage':'WON','occurred_at':'2026-07-14T11:00:00+05:30','source':'SYNTHETIC','experiment_id':None,'channel':'founder','first_touch':'referral','self_reported_source':'referral','influencing_channels':['whatsapp'],'conversion_touch':'demo','consent_status':'EXISTING_RELATIONSHIP','metadata':{}})
  if 'WON_WITHOUT_REVENUE' not in reconcile(c,'OPP-SMOKE-0001')['exceptions']:errors.append('reconciliation smoke failed')
  if not integrity(c)['ok']:errors.append('integrity smoke failed')
 return errors
if __name__=='__main__':
 errors=verify();print('PHASE5 VERIFY: '+('FAIL' if errors else 'PASS'));[print('- '+x) for x in errors];raise SystemExit(bool(errors))
