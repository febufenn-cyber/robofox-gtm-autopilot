#!/usr/bin/env python3
"""Verify Phase 7 production-hardening contracts and staging readiness."""
from __future__ import annotations
import json, sqlite3, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from robofox_ops import authorize, issue_session, install, readiness_report, redact, validate_environment, verify_session

REQUIRED=[
 'PHASE7.md','policies/operations-policy.md','.claude/skills/operator-console/SKILL.md',
 'robofox_ops/security.py','robofox_ops/queue.py','robofox_ops/backup.py','robofox_ops/console.py','robofox_ops/readiness.py',
 'deploy/staging-compose.yml','runbooks/incident-response.md','runbooks/backup-restore.md',
 'reports/operational-readiness.json','reports/evaluation-readiness.json'
]

def verify()->list[str]:
 errors=[f'missing Phase 7 file: {x}' for x in REQUIRED if not (ROOT/x).is_file()]
 try:
  operational=json.loads((ROOT/'reports/operational-readiness.json').read_text())
  evaluation=json.loads((ROOT/'reports/evaluation-readiness.json').read_text())
  if operational.get('v1_ready') is not True:errors.append('v1 operational readiness must pass')
  if operational.get('production_deployed') is not False:errors.append('production must remain undeployed')
  if operational.get('phase8_ready') is not False:errors.append('Phase 8 must remain readiness-gated')
  if evaluation.get('phase9_ready') is not False:errors.append('Phase 9 must remain readiness-gated')
  if evaluation.get('production_self_modification') is not False:errors.append('production self-modification must remain disabled')
 except Exception as exc:errors.append(f'invalid readiness report: {exc}')
 token=issue_session('smoke','read_only',b'x'*32,1000)
 try:
  session=verify_session(token,b'x'*32,1001);authorize(session,'view')
 except Exception as exc:errors.append(f'RBAC smoke failed: {exc}')
 if redact({'token':'x','nested':{'email':'y'}})!={'token':'[REDACTED]','nested':{'email':'[REDACTED]'}}:errors.append('redaction smoke failed')
 if validate_environment({'environment':'staging','workspace':'/private/staging','autonomous_deploy':False}):errors.append('staging environment rejected')
 report=readiness_report({'rbac':True,'secret_redaction':True,'queue_deduplication':True,'backup_restore':True,'staging_rollback':True,'incident_runbooks':True,'phase0_7_gate':True})
 if report.get('v1_ready') is not True or report.get('phase8_ready') is not False:errors.append('readiness calculation differs')
 with tempfile.TemporaryDirectory() as directory:
  connection=sqlite3.connect(Path(directory)/'queue.sqlite3');install(connection)
  tables={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  if 'jobs' not in tables:errors.append('job queue schema missing')
  connection.close()
 compose=(ROOT/'deploy/staging-compose.yml').read_text() if (ROOT/'deploy/staging-compose.yml').is_file() else ''
 for marker in ('network_mode: none','read_only: true','ROBOFOX_EXTERNAL_EXECUTION: "false"'):
  if marker not in compose:errors.append(f'staging manifest missing: {marker}')
 return errors

def main()->int:
 errors=verify()
 if errors:
  print('PHASE7 VERIFY: FAIL');[print('- '+x) for x in errors];return 1
 print('PHASE7 VERIFY: PASS')
 print('- private RBAC console, redaction, lease queue, authenticated backups, staging isolation, runbooks, and readiness reports')
 return 0
if __name__=='__main__':raise SystemExit(main())
