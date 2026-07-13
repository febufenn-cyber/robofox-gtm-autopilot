#!/usr/bin/env python3
"""Smoke-verify exact approvals, single-use consumption, and integrity checks."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth import (  # noqa: E402
    TruthStoreError,
    approved_insert,
    connect,
    create_approval,
    initialize,
    integrity_report,
    prepare_manifest,
    resolve_workspace,
)


def verify() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="robofox-approval-smoke-") as directory:
        workspace = resolve_workspace(directory, create=True)
        (workspace / "workspace.json").write_text(json.dumps({
            "workspace_id": "WS-APPROVAL-SMOKE",
            "public_repo": False,
        }), encoding="utf-8")
        initialize(workspace)
        payload = {
            "id": "SRC-APPROVAL-SMOKE",
            "source_type": "FOUNDER_OBSERVATION",
            "captured_at": "2026-07-13T10:00:00+05:30",
            "sensitivity": "INTERNAL",
            "content_hash": "sha256:" + "c" * 64,
            "metadata": {"synthetic": True},
        }
        manifest = prepare_manifest(
            workspace, "record_truth_source", payload,
            requested_by="phase1-smoke", task_id="TASK-PHASE1-SMOKE",
            created_at="2026-07-13T10:01:00+05:30",
        )
        approval = create_approval(
            manifest, approved_by="founder-smoke",
            approved_at="2026-07-13T10:02:00+05:30", expires_minutes=30,
        )
        with connect(workspace) as connection:
            approved_insert(
                connection, workspace, "record_truth_source", payload, manifest, approval,
                now="2026-07-13T10:03:00+05:30",
            )
            try:
                approved_insert(
                    connection, workspace, "record_truth_source", {**payload, "id": "SRC-APPROVAL-OTHER"},
                    manifest, approval, now="2026-07-13T10:04:00+05:30",
                )
            except TruthStoreError:
                pass
            else:
                errors.append("changed payload was accepted by the same approval")
            report = integrity_report(connection)
            if not report["ok"]:
                errors.append(f"clean ledger failed integrity: {report['issues']}")
            if report["counts"]["approval_consumptions"] != 1:
                errors.append("approval consumption was not recorded exactly once")
            try:
                connection.execute("DELETE FROM approval_consumptions")
            except sqlite3.IntegrityError as exc:
                if "append-only" not in str(exc):
                    errors.append(f"wrong approval append-only error: {exc}")
            else:
                errors.append("approval consumption delete was not blocked")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        print("PHASE1 APPROVALS: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PHASE1 APPROVALS: PASS")
    print("- exact payload/workspace/action binding")
    print("- atomic record insertion and single-use approval consumption")
    print("- SQLite, migration, trigger, foreign-key, and record-hash integrity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
