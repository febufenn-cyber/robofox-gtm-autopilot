"""Integrity checks for Phase 3 experiment records."""
from __future__ import annotations
import json, sqlite3
from typing import Any
from robofox_truth.validation import record_hash

TABLES=("experiments","experiment_transitions","experiment_executions","experiment_observations","experiment_outcomes")
TRIGGERS={f'{name}_{action}' for name in TABLES for action in ('no_update','no_delete')}
def integrity_report(connection:sqlite3.Connection)->dict[str,Any]:
    issues=[]; triggers={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}; missing=sorted(TRIGGERS-triggers)
    if missing: issues.append(f'missing append-only experiment triggers: {missing}')
    counts={}; checked=0
    for table in TABLES:
        try: rows=list(connection.execute(f'SELECT id,record_json,record_hash FROM {table} ORDER BY id'))
        except sqlite3.OperationalError as exc:
            issues.append(f'missing experiment table {table}: {exc}'); continue
        counts[table]=len(rows)
        for row in rows:
            checked+=1
            try: payload=json.loads(row['record_json'])
            except Exception as exc: issues.append(f'invalid record_json: {table}.{row["id"]}: {exc}'); continue
            if record_hash(payload)!=row['record_hash']: issues.append(f'record hash mismatch: {table}.{row["id"]}')
    return {'ok':not issues,'counts':counts,'checked_record_hashes':checked,'issues':issues}
