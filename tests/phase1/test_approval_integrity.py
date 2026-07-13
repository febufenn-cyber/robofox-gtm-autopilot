from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth import (  # noqa: E402
    TruthStoreError,
    approved_insert,
    canonical_hash,
    connect,
    create_approval,
    initialize,
    integrity_report,
    prepare_manifest,
    resolve_workspace,
    validate_approval,
)
from robofox_truth.constants import SCHEMA_VERSION  # noqa: E402


class ApprovalIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="robofox-approval-test-")
        self.workspace = resolve_workspace(self.temp.name, create=True)
        (self.workspace / "workspace.json").write_text(json.dumps({
            "workspace_id": "WS-APPROVAL-TEST",
            "public_repo": False,
        }), encoding="utf-8")
        initialize(self.workspace)
        self.connection_context = connect(self.workspace)
        self.connection = self.connection_context.__enter__()
        self.payload = {
            "id": "SRC-APPROVAL-0001",
            "source_type": "FOUNDER_OBSERVATION",
            "captured_at": "2026-07-13T10:00:00+05:30",
            "sensitivity": "INTERNAL",
            "content_hash": "sha256:" + "d" * 64,
            "metadata": {"synthetic": True},
        }
        self.manifest = prepare_manifest(
            self.workspace,
            "record_truth_source",
            self.payload,
            requested_by="test-requester",
            task_id="TASK-APPROVAL-TEST",
            created_at="2026-07-13T10:01:00+05:30",
        )
        self.approval = create_approval(
            self.manifest,
            approved_by="test-founder",
            approved_at="2026-07-13T10:02:00+05:30",
            expires_minutes=30,
        )

    def tearDown(self) -> None:
        self.connection_context.__exit__(None, None, None)
        self.temp.cleanup()

    def insert(self) -> str:
        return approved_insert(
            self.connection,
            self.workspace,
            "record_truth_source",
            self.payload,
            self.manifest,
            self.approval,
            now="2026-07-13T10:03:00+05:30",
        )

    def test_exact_approval_inserts_and_consumes_atomically(self) -> None:
        self.assertEqual(self.payload["id"], self.insert())
        source_count = self.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        approval_count = self.connection.execute("SELECT COUNT(*) FROM approval_consumptions").fetchone()[0]
        self.assertEqual((1, 1), (source_count, approval_count))

    def test_payload_change_invalidates_approval(self) -> None:
        changed = {**self.payload, "metadata": {"synthetic": False}}
        with self.assertRaisesRegex(TruthStoreError, "payload_hash"):
            approved_insert(
                self.connection, self.workspace, "record_truth_source", changed,
                self.manifest, self.approval, now="2026-07-13T10:03:00+05:30",
            )
        self.assertEqual(0, self.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0])
        self.assertEqual(0, self.connection.execute("SELECT COUNT(*) FROM approval_consumptions").fetchone()[0])

    def test_workspace_scope_change_invalidates_approval(self) -> None:
        (self.workspace / "workspace.json").write_text(json.dumps({
            "workspace_id": "WS-DIFFERENT-TEST",
            "public_repo": False,
        }), encoding="utf-8")
        with self.assertRaisesRegex(TruthStoreError, "scope"):
            validate_approval(
                self.workspace, "record_truth_source", self.payload,
                self.manifest, self.approval, now="2026-07-13T10:03:00+05:30",
            )

    def test_manifest_edit_invalidates_approval(self) -> None:
        changed = dict(self.manifest)
        changed["task_id"] = "TASK-CHANGED"
        with self.assertRaisesRegex(TruthStoreError, "manifest_hash"):
            validate_approval(
                self.workspace, "record_truth_source", self.payload,
                changed, self.approval, now="2026-07-13T10:03:00+05:30",
            )

    def test_expired_approval_is_rejected(self) -> None:
        with self.assertRaisesRegex(TruthStoreError, "expired"):
            validate_approval(
                self.workspace, "record_truth_source", self.payload,
                self.manifest, self.approval, now="2026-07-13T11:00:00+05:30",
            )


    def test_overlong_manual_approval_is_rejected(self) -> None:
        changed = dict(self.approval)
        changed["expires_at"] = "2026-07-15T10:02:00+05:30"
        with self.assertRaisesRegex(TruthStoreError, "validity exceeds"):
            validate_approval(
                self.workspace, "record_truth_source", self.payload,
                self.manifest, changed, now="2026-07-13T10:03:00+05:30",
            )

    def test_consumed_approval_cannot_be_replayed(self) -> None:
        self.insert()
        changed_id = {**self.payload, "id": "SRC-APPROVAL-0002"}
        manifest = prepare_manifest(
            self.workspace, "record_truth_source", changed_id,
            requested_by="test-requester", task_id="TASK-REPLAY",
            created_at="2026-07-13T10:04:00+05:30",
        )
        replay = create_approval(
            manifest, approved_by="test-founder",
            approved_at="2026-07-13T10:05:00+05:30", expires_minutes=30,
        )
        replay["approval_id"] = self.approval["approval_id"]
        with self.assertRaises(sqlite3.IntegrityError):
            approved_insert(
                self.connection, self.workspace, "record_truth_source", changed_id,
                manifest, replay, now="2026-07-13T10:05:00+05:30",
            )
        self.assertEqual(1, self.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0])

    def test_failed_record_insert_does_not_consume_approval(self) -> None:
        self.insert()
        second_manifest = prepare_manifest(
            self.workspace, "record_truth_source", self.payload,
            requested_by="test-requester", task_id="TASK-DUPLICATE",
            created_at="2026-07-13T10:04:00+05:30",
        )
        second_approval = create_approval(
            second_manifest, approved_by="test-founder",
            approved_at="2026-07-13T10:05:00+05:30", expires_minutes=30,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            approved_insert(
                self.connection, self.workspace, "record_truth_source", self.payload,
                second_manifest, second_approval, now="2026-07-13T10:06:00+05:30",
            )
        self.assertEqual(1, self.connection.execute("SELECT COUNT(*) FROM approval_consumptions").fetchone()[0])

    def test_integrity_report_passes_clean_ledger(self) -> None:
        self.insert()
        report = integrity_report(self.connection)
        self.assertTrue(report["ok"], report["issues"])
        self.assertEqual(SCHEMA_VERSION, report["schema_version"])
        self.assertEqual(1, report["checked_record_hashes"])

    def test_integrity_report_detects_out_of_band_record_tampering(self) -> None:
        self.insert()
        self.connection.execute("DROP TRIGGER sources_no_update")
        self.connection.execute(
            "UPDATE sources SET metadata_json = ? WHERE id = ?",
            ('{"tampered":true}', self.payload["id"]),
        )
        report = integrity_report(self.connection)
        self.assertFalse(report["ok"])
        self.assertTrue(any("record hash mismatch" in issue for issue in report["issues"]))
        self.assertTrue(any("missing append-only triggers" in issue for issue in report["issues"]))

    def test_initialization_payload_is_schema_bound(self) -> None:
        payload = {"schema_version": SCHEMA_VERSION}
        manifest = prepare_manifest(
            self.workspace, "initialize_truth_ledger", payload,
            requested_by="test-requester", task_id="TASK-INIT",
            created_at="2026-07-13T10:01:00+05:30",
        )
        self.assertEqual(SCHEMA_VERSION, manifest["scope"]["schema_version"])
        self.assertEqual(0, manifest["maximum_records"])

    def test_approval_consumption_is_append_only(self) -> None:
        self.insert()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
            self.connection.execute("DELETE FROM approval_consumptions")


if __name__ == "__main__":
    unittest.main()
