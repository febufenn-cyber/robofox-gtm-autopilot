"""Integrity checks for Phase 4 append-only execution records."""
from __future__ import annotations
import json,sqlite3
from typing import Any
from .validation import canonical_hash
REQUIRED_TRIGGERS={f'{table}_{suffix}' for table in ('execution_envelopes','execution_attempts','execution_results','execution_rollbacks','execution_circuit_events') for suffix in ('no_update','no_delete')}|{'execution_approvals_no_update','execution_approvals_no_delete'}
def integrity_report(connection:sqlite3.Connection)->dict[str,Any]:
    issues=[]
    if [r[0] for r in connection.execute('PRAGMA integrity_check')]!=['ok']: issues.append('sqlite integrity check failed')
    if list(connection.execute('PRAGMA foreign_key_check')): issues.append('foreign-key violations')
    triggers={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    missing=sorted(REQUIRED_TRIGGERS-triggers)
    if missing: issues.append(f'missing triggers: {missing}')
    checked=0
    for table in ('execution_envelopes','execution_attempts','execution_results','execution_rollbacks','execution_circuit_events'):
        for row in connection.execute(f'SELECT id,record_json,record_hash FROM {table}'):
            checked+=1
            if canonical_hash(json.loads(row[1]))!=row[2]: issues.append(f'record hash mismatch: {table}.{row[0]}')
    counts={t:connection.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('execution_envelopes','execution_attempts','execution_results','execution_rollbacks','execution_circuit_events','execution_approval_consumptions')}
    return {'ok':not issues,'checked_record_hashes':checked,'counts':counts,'issues':issues}
