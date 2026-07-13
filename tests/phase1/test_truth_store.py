from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from robofox_truth import (  # noqa: E402
    TruthStoreError,
    connect,
    initialize,
    insert_assumption,
    insert_claim,
    insert_metric,
    insert_source,
    resolve_workspace,
    status,
    validate_claim,
)


SOURCE = {
    "id": "SRC-TEST-0001",
    "source_type": "CALL_TEST",
    "captured_at": "2026-07-13T09:00:00+05:30",
    "observed_at": "2026-07-13T08:55:00+05:30",
    "sensitivity": "INTERNAL",
    "content_hash": "sha256:" + "a" * 64,
    "metadata": {"synthetic": True},
}


def claim(record_id: str = "CLM-TEST-0001", **overrides):
    value = {
        "id": record_id,
        "product": "voice-agents",
        "subject": "commercial-position",
        "predicate": "delivery_readiness",
        "value": "developing",
        "evidence_state": "OBSERVED",
        "confidence": "MEDIUM",
        "source_ids": [SOURCE["id"]],
        "captured_at": "2026-07-13T09:01:00+05:30",
        "max_age_days": 14,
        "sensitivity": "INTERNAL",
    }
    value.update(overrides)
    return value


class TruthStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="robofox-truth-test-")
        self.workspace = resolve_workspace(self.temp.name, create=True)
        initialize(self.workspace)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_init_and_status(self) -> None:
        with connect(self.workspace) as connection:
            self.assertEqual(
                {"schema_version": 2, "counts": {"sources": 0, "claims": 0, "assumptions": 0, "metrics": 0, "approval_consumptions": 0}, "append_only": True},
                status(connection),
            )

    def test_source_linked_claim_and_metric(self) -> None:
        metric = {
            "id": "MET-TEST-0001",
            "product": "voice-agents",
            "metric": "successful_call_rate",
            "value": 0.8,
            "unit": "ratio",
            "denominator": 10,
            "sample_size": 10,
            "source_ids": [SOURCE["id"]],
            "period_start": "2026-07-13T08:00:00+05:30",
            "period_end": "2026-07-13T09:00:00+05:30",
            "captured_at": "2026-07-13T09:02:00+05:30",
            "sensitivity": "INTERNAL",
        }
        with connect(self.workspace) as connection:
            insert_source(connection, SOURCE)
            insert_claim(connection, claim())
            insert_metric(connection, metric)
            self.assertEqual(1, status(connection)["counts"]["metrics"])

    def test_observed_claim_requires_source(self) -> None:
        with self.assertRaisesRegex(TruthStoreError, "require at least one source"):
            validate_claim(claim(source_ids=[]))

    def test_missing_source_reference_fails(self) -> None:
        with connect(self.workspace) as connection:
            with self.assertRaisesRegex(TruthStoreError, "missing sources references"):
                insert_claim(connection, claim())

    def test_timestamps_require_timezone(self) -> None:
        with self.assertRaisesRegex(TruthStoreError, "timezone"):
            validate_claim(claim(captured_at="2026-07-13T09:01:00"))

    def test_database_triggers_block_update_and_delete(self) -> None:
        with connect(self.workspace) as connection:
            insert_source(connection, SOURCE)
            insert_claim(connection, claim())
            for statement in (
                "UPDATE claims SET confidence = 'HIGH' WHERE id = 'CLM-TEST-0001'",
                "DELETE FROM claims WHERE id = 'CLM-TEST-0001'",
            ):
                with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
                    connection.execute(statement)

    def test_correction_uses_single_supersession_edge(self) -> None:
        with connect(self.workspace) as connection:
            insert_source(connection, SOURCE)
            insert_claim(connection, claim())
            insert_claim(connection, claim("CLM-TEST-0002", value="ready", supersedes_id="CLM-TEST-0001"))
            with self.assertRaisesRegex(TruthStoreError, "already superseded"):
                insert_claim(connection, claim("CLM-TEST-0003", value="not-ready", supersedes_id="CLM-TEST-0001"))

    def test_duplicate_id_is_rejected(self) -> None:
        with connect(self.workspace) as connection:
            insert_source(connection, SOURCE)
            with self.assertRaises(sqlite3.IntegrityError):
                insert_source(connection, SOURCE)

    def test_assumption_is_separate_from_claim(self) -> None:
        assumption = {
            "id": "ASM-TEST-0001",
            "product": "voice-agents",
            "statement": "Clinic owners will pay for missed-call recovery.",
            "status": "OPEN",
            "confidence": "LOW",
            "created_at": "2026-07-13T09:00:00+05:30",
            "sensitivity": "CONFIDENTIAL",
        }
        with connect(self.workspace) as connection:
            insert_assumption(connection, assumption)
            self.assertEqual(1, status(connection)["counts"]["assumptions"])
            self.assertEqual(0, status(connection)["counts"]["claims"])

    def test_restricted_records_are_allowed_only_in_private_store(self) -> None:
        restricted = dict(SOURCE)
        restricted["id"] = "SRC-TEST-0002"
        restricted["content_hash"] = "sha256:" + "b" * 64
        restricted["sensitivity"] = "RESTRICTED"
        with connect(self.workspace) as connection:
            insert_source(connection, restricted)
            row = connection.execute("SELECT sensitivity FROM sources WHERE id = ?", (restricted["id"],)).fetchone()
            self.assertEqual("RESTRICTED", row[0])

    def test_validity_window_cannot_run_backwards(self) -> None:
        with self.assertRaisesRegex(TruthStoreError, "valid_until cannot precede valid_from"):
            validate_claim(claim(
                valid_from="2026-07-14T09:00:00+05:30",
                valid_until="2026-07-13T09:00:00+05:30",
            ))

    def test_claim_cannot_supersede_different_predicate(self) -> None:
        with connect(self.workspace) as connection:
            insert_source(connection, SOURCE)
            insert_claim(connection, claim())
            with self.assertRaisesRegex(TruthStoreError, "same subject and predicate"):
                insert_claim(connection, claim(
                    "CLM-TEST-0002",
                    predicate="customer_trust",
                    supersedes_id="CLM-TEST-0001",
                ))



    def test_initialize_upgrades_version_one_database(self) -> None:
        import sqlite3
        from robofox_truth.constants import MIGRATIONS_ROOT
        from robofox_truth.store import database_path

        upgrade_root = Path(self.temp.name) / "upgrade-workspace"
        upgrade_root.mkdir()
        path = database_path(upgrade_root)
        path.parent.mkdir(parents=True)
        connection = sqlite3.connect(path)
        connection.executescript((MIGRATIONS_ROOT / "001_initial.sql").read_text())
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (1, ?)",
            ("2026-07-13T10:00:00+05:30",),
        )
        connection.commit()
        connection.close()
        initialize(upgrade_root)
        with connect(upgrade_root) as upgraded:
            versions = [row[0] for row in upgraded.execute("SELECT version FROM schema_migrations ORDER BY version")]
            self.assertEqual([1, 2], versions)
            table = upgraded.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='approval_consumptions'"
            ).fetchone()
            self.assertIsNotNone(table)

    def test_non_finite_numbers_are_rejected(self) -> None:
        metric = {
            "id": "MET-TEST-NAN01",
            "product": "voice-agents",
            "metric": "successful_call_rate",
            "value": float("nan"),
            "unit": "ratio",
            "source_ids": [SOURCE["id"]],
            "period_start": "2026-07-13T08:00:00+05:30",
            "period_end": "2026-07-13T09:00:00+05:30",
            "captured_at": "2026-07-13T09:02:00+05:30",
            "sensitivity": "INTERNAL",
        }
        with connect(self.workspace) as connection:
            insert_source(connection, SOURCE)
            with self.assertRaisesRegex(TruthStoreError, "canonical JSON"):
                insert_metric(connection, metric)

    def test_no_update_or_delete_cli_commands_exist(self) -> None:
        script = (ROOT / "scripts/truth_store.py").read_text()
        self.assertNotIn('add_parser("update', script)
        self.assertNotIn('add_parser("delete', script)
        self.assertNotIn("arbitrary SQL", script.lower().replace("does not expose ", ""))


if __name__ == "__main__":
    unittest.main()
