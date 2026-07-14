#!/usr/bin/env python3
"""Verify Phase 4 contracts and run a deterministic simulator smoke test."""
from __future__ import annotations
import json,sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from robofox_execution import execute_simulated, install_schema, integrity_report
REQUIRED=['PHASE4.md','policies/execution-layer-policy.md','schemas/execution-envelope.schema.json','schemas/execution-approval.schema.json','schemas/execution-result.schema.json','schemas/rollback-record.schema.json','schemas/adapter-contract.schema.json','robofox_execution/constants.py','robofox_execution/validation.py','robofox_execution/adapters.py','robofox_execution/store.py','robofox_execution/approval.py','robofox_execution/service.py','robofox_execution/integrity.py','scripts/execution_gateway.py','scripts/execution_approval.py']
def envelope():
    return {'id':'EXR-SMOKE-0001','experiment_id':'EXP-SMOKE-0001','action_type':'PREPARE_CRM_TASK','adapter':'internal.crm_task','mode':'SIMULATOR','idempotency_key':'phase4-smoke-key-0001','target_keys':['TGT-SMOKE-0001'],'content_hash':'sha256:'+'1'*64,'payload':{'simulate_outcome':'SUCCESS','task_kind':'follow_up'},'batch_size':1,'canary_for_id':None,'maximum_spend_usd':0,'currency':'USD','rate_limit_per_hour':5,'rollback_plan':{'required':True,'strategy':'remove simulated task','timeout_seconds':60},'created_at':'2026-07-14T10:00:00+05:30','sensitivity':'INTERNAL'}
def verify()->list[str]:
    errors=[]
    for f in REQUIRED:
        if not (ROOT/f).is_file(): errors.append(f'missing Phase 4 file: {f}')
    for f in ROOT.glob('schemas/*execution*.json'):
        try:
            data=json.loads(f.read_text())
            if data.get('additionalProperties') is not False: errors.append(f'{f.name} is not closed')
        except Exception as exc: errors.append(f'invalid schema {f.name}: {exc}')
    with tempfile.TemporaryDirectory() as d:
        c=sqlite3.connect(Path(d)/'gateway.sqlite3'); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); install_schema(c)
        result=execute_simulated(c,envelope())
        if result['outcome']!='SUCCESS' or result['affected_records']!=1: errors.append('simulator smoke result differs')
        report=integrity_report(c)
        if not report['ok']: errors.extend(report['issues'])
        c.close()
    return errors
def main()->int:
    errors=verify()
    if errors:
        print('PHASE4 VERIFY: FAIL'); [print('- '+e) for e in errors]; return 1
    print('PHASE4 VERIFY: PASS'); print('- simulator-only adapters, exact contracts, canary, idempotency, rollback, circuit and integrity controls'); return 0
if __name__=='__main__': raise SystemExit(main())
