"""Integrity verification for the private Robofox truth ledger."""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from .constants import SCHEMA_VERSION
from .validation import record_hash

REQUIRED_TRIGGERS = {
    "sources_no_update", "sources_no_delete", "claims_no_update", "claims_no_delete",
    "claim_sources_no_update", "claim_sources_no_delete", "assumptions_no_update",
    "assumptions_no_delete", "assumption_links_no_update", "assumption_links_no_delete",
    "metrics_no_update", "metrics_no_delete", "metric_sources_no_update",
    "metric_sources_no_delete", "approval_consumptions_no_update",
    "approval_consumptions_no_delete",
}


def _links(connection: sqlite3.Connection, table: str, owner_column: str, value_column: str, record_id: str) -> list[str]:
    return sorted(
        row[0]
        for row in connection.execute(
            f"SELECT {value_column} FROM {table} WHERE {owner_column} = ? ORDER BY {value_column}",
            (record_id,),
        )
    )


def _source_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"], "source_type": row["source_type"],
        "external_reference": row["external_reference"], "captured_at": row["captured_at"],
        "observed_at": row["observed_at"], "sensitivity": row["sensitivity"],
        "content_hash": row["content_hash"], "metadata": json.loads(row["metadata_json"]),
    }


def _claim_record(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"], "product": row["product"], "subject": row["subject"],
        "predicate": row["predicate"], "value": json.loads(row["value_json"]),
        "unit": row["unit"], "evidence_state": row["evidence_state"],
        "confidence": row["confidence"],
        "source_ids": _links(connection, "claim_sources", "claim_id", "source_id", row["id"]),
        "captured_at": row["captured_at"], "observed_at": row["observed_at"],
        "valid_from": row["valid_from"], "valid_until": row["valid_until"],
        "max_age_days": row["max_age_days"], "supersedes_id": row["supersedes_id"],
        "sensitivity": row["sensitivity"], "notes": row["notes"],
    }


def _assumption_record(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"], "product": row["product"], "statement": row["statement"],
        "status": row["status"], "confidence": row["confidence"],
        "created_at": row["created_at"], "review_by": row["review_by"],
        "resolution_claim_ids": _links(
            connection, "assumption_resolution_claims", "assumption_id", "claim_id", row["id"]
        ),
        "supersedes_id": row["supersedes_id"], "sensitivity": row["sensitivity"],
    }


def _metric_record(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"], "product": row["product"], "metric": row["metric"],
        "value": row["value"], "unit": row["unit"], "denominator": row["denominator"],
        "sample_size": row["sample_size"], "segment": row["segment"],
        "experiment_id": row["experiment_id"],
        "source_ids": _links(connection, "metric_sources", "metric_id", "source_id", row["id"]),
        "period_start": row["period_start"], "period_end": row["period_end"],
        "captured_at": row["captured_at"], "sensitivity": row["sensitivity"],
    }


def integrity_report(connection: sqlite3.Connection) -> dict[str, Any]:
    issues: list[str] = []
    integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
    if integrity != ["ok"]:
        issues.extend(f"sqlite integrity: {item}" for item in integrity)
    foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
    if foreign_keys:
        issues.append(f"foreign key violations: {len(foreign_keys)}")
    migrations = [row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
    if migrations != list(range(1, SCHEMA_VERSION + 1)):
        issues.append(f"migration sequence differs: {migrations}")
    triggers = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")
    }
    missing_triggers = sorted(REQUIRED_TRIGGERS - triggers)
    if missing_triggers:
        issues.append(f"missing append-only triggers: {missing_triggers}")

    checks = (
        ("sources", "SELECT * FROM sources ORDER BY id", lambda row: _source_record(row)),
        ("claims", "SELECT * FROM claims ORDER BY id", lambda row: _claim_record(connection, row)),
        ("assumptions", "SELECT * FROM assumptions ORDER BY id", lambda row: _assumption_record(connection, row)),
        ("metrics", "SELECT * FROM metrics ORDER BY id", lambda row: _metric_record(connection, row)),
    )
    checked_hashes = 0
    for table, query, reconstruct in checks:
        for row in connection.execute(query):
            checked_hashes += 1
            expected = record_hash(reconstruct(row))
            if expected != row["record_hash"]:
                issues.append(f"record hash mismatch: {table}.{row['id']}")

    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("sources", "claims", "assumptions", "metrics", "approval_consumptions")
    }
    return {
        "ok": not issues,
        "schema_version": max(migrations, default=0),
        "counts": counts,
        "checked_record_hashes": checked_hashes,
        "issues": issues,
    }
