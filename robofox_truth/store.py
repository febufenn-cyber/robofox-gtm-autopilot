"""SQLite storage implementation for the Robofox truth layer."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .constants import DB_RELATIVE_PATH, DEFAULT_WORKSPACE, ENGINE_ROOT, MIGRATIONS_ROOT, SCHEMA_VERSION
from .validation import (
    TruthStoreError,
    canonical_json,
    record_hash,
    validate_assumption,
    validate_claim,
    validate_metric,
    validate_source,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_workspace(path: str | Path | None = None, *, create: bool = False) -> Path:
    raw = path or os.getenv("ROBOFOX_GTM_WORKSPACE") or DEFAULT_WORKSPACE
    root = Path(raw).expanduser().resolve()
    try:
        root.relative_to(ENGINE_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise TruthStoreError("private workspace cannot be inside the public engine")
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if not root.exists() or not root.is_dir():
        raise TruthStoreError(f"workspace does not exist: {root}")
    return root


def database_path(workspace: Path) -> Path:
    return workspace / DB_RELATIVE_PATH


@contextmanager
def connect(workspace: Path, *, initialize: bool = False) -> Iterator[sqlite3.Connection]:
    path = database_path(workspace)
    if initialize:
        path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() and not initialize:
        raise TruthStoreError(f"truth ledger is not initialized: {path}")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    try:
        yield connection
    finally:
        connection.close()


def initialize(workspace: Path) -> Path:
    migration = MIGRATIONS_ROOT / "001_initial.sql"
    if not migration.is_file():
        raise TruthStoreError("missing migration 001_initial.sql")
    with connect(workspace, initialize=True) as connection:
        with connection:
            connection.executescript(migration.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, utc_now()),
            )
    return database_path(workspace)


def ensure_references(connection: sqlite3.Connection, table: str, ids: list[str]) -> None:
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    existing = {row[0] for row in connection.execute(f"SELECT id FROM {table} WHERE id IN ({placeholders})", ids)}
    missing = sorted(set(ids) - existing)
    if missing:
        raise TruthStoreError(f"missing {table} references: {missing}")


def ensure_supersedes(
    connection: sqlite3.Connection,
    table: str,
    record_id: str,
    supersedes_id: str | None,
    product: str,
    *,
    subject: str | None = None,
    predicate: str | None = None,
) -> None:
    if supersedes_id is None:
        return
    if supersedes_id == record_id:
        raise TruthStoreError("a record cannot supersede itself")
    columns = "product, subject, predicate" if table == "claims" else "product, NULL, NULL"
    row = connection.execute(f"SELECT {columns} FROM {table} WHERE id = ?", (supersedes_id,)).fetchone()
    if row is None:
        raise TruthStoreError(f"superseded record does not exist: {supersedes_id}")
    if row[0] != product:
        raise TruthStoreError("superseded record belongs to a different product")
    if table == "claims" and (row[1] != subject or row[2] != predicate):
        raise TruthStoreError("a claim may only supersede the same subject and predicate")
    already = connection.execute(f"SELECT id FROM {table} WHERE supersedes_id = ?", (supersedes_id,)).fetchone()
    if already is not None:
        raise TruthStoreError(f"record is already superseded by {already[0]}")


def insert_source(connection: sqlite3.Connection, raw: dict[str, Any]) -> str:
    record = validate_source(raw)
    digest = record_hash(record)
    with connection:
        connection.execute(
            """INSERT INTO sources(id, source_type, external_reference, captured_at, observed_at, sensitivity, content_hash, metadata_json, record_hash, inserted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["source_type"], record["external_reference"], record["captured_at"], record["observed_at"], record["sensitivity"], record["content_hash"], canonical_json(record["metadata"]), digest, utc_now()),
        )
    return str(record["id"])


def insert_claim(connection: sqlite3.Connection, raw: dict[str, Any]) -> str:
    record = validate_claim(raw)
    ensure_references(connection, "sources", record["source_ids"])
    ensure_supersedes(
        connection, "claims", str(record["id"]), record["supersedes_id"], str(record["product"]),
        subject=str(record["subject"]), predicate=str(record["predicate"]),
    )
    digest = record_hash(record)
    with connection:
        connection.execute(
            """INSERT INTO claims(id, product, subject, predicate, value_json, unit, evidence_state, confidence, captured_at, observed_at, valid_from, valid_until, max_age_days, supersedes_id, sensitivity, notes, record_hash, inserted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["product"], record["subject"], record["predicate"], canonical_json(record["value"]), record["unit"], record["evidence_state"], record["confidence"], record["captured_at"], record["observed_at"], record["valid_from"], record["valid_until"], record["max_age_days"], record["supersedes_id"], record["sensitivity"], record["notes"], digest, utc_now()),
        )
        connection.executemany(
            "INSERT INTO claim_sources(claim_id, source_id) VALUES (?, ?)",
            [(record["id"], source_id) for source_id in record["source_ids"]],
        )
    return str(record["id"])


def insert_assumption(connection: sqlite3.Connection, raw: dict[str, Any]) -> str:
    record = validate_assumption(raw)
    ensure_references(connection, "claims", record["resolution_claim_ids"])
    ensure_supersedes(connection, "assumptions", str(record["id"]), record["supersedes_id"], str(record["product"]))
    digest = record_hash(record)
    with connection:
        connection.execute(
            """INSERT INTO assumptions(id, product, statement, status, confidence, created_at, review_by, supersedes_id, sensitivity, record_hash, inserted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["product"], record["statement"], record["status"], record["confidence"], record["created_at"], record["review_by"], record["supersedes_id"], record["sensitivity"], digest, utc_now()),
        )
        connection.executemany(
            "INSERT INTO assumption_resolution_claims(assumption_id, claim_id) VALUES (?, ?)",
            [(record["id"], claim_id) for claim_id in record["resolution_claim_ids"]],
        )
    return str(record["id"])


def insert_metric(connection: sqlite3.Connection, raw: dict[str, Any]) -> str:
    record = validate_metric(raw)
    ensure_references(connection, "sources", record["source_ids"])
    digest = record_hash(record)
    with connection:
        connection.execute(
            """INSERT INTO metrics(id, product, metric, value, unit, denominator, sample_size, segment, experiment_id, period_start, period_end, captured_at, sensitivity, record_hash, inserted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["id"], record["product"], record["metric"], record["value"], record["unit"], record["denominator"], record["sample_size"], record["segment"], record["experiment_id"], record["period_start"], record["period_end"], record["captured_at"], record["sensitivity"], digest, utc_now()),
        )
        connection.executemany(
            "INSERT INTO metric_sources(metric_id, source_id) VALUES (?, ?)",
            [(record["id"], source_id) for source_id in record["source_ids"]],
        )
    return str(record["id"])


def status(connection: sqlite3.Connection) -> dict[str, Any]:
    tables = ("sources", "claims", "assumptions", "metrics")
    counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
    migrations = [row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
    return {"schema_version": max(migrations, default=0), "counts": counts, "append_only": True}
