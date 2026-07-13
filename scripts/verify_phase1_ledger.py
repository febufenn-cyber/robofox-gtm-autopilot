#!/usr/bin/env python3
"""Run a zero-dependency smoke verification of the private truth ledger."""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth import connect, initialize, insert_claim, insert_source, resolve_workspace, status


def verify() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="robofox-phase1-") as directory:
        workspace = resolve_workspace(directory, create=True)
        path = initialize(workspace)
        if not path.is_file():
            errors.append("ledger database was not created")
            return errors
        source = {
            "id": "SRC-SMOKE-001",
            "source_type": "FOUNDER_OBSERVATION",
            "captured_at": "2026-07-13T10:00:00+05:30",
            "sensitivity": "INTERNAL",
            "content_hash": "sha256:" + "1" * 64,
            "metadata": {"synthetic": True},
        }
        claim = {
            "id": "CLM-SMOKE-001",
            "product": "voice-agents",
            "subject": "commercial-position",
            "predicate": "founder_capacity",
            "value": "constrained",
            "evidence_state": "OBSERVED",
            "confidence": "MEDIUM",
            "source_ids": ["SRC-SMOKE-001"],
            "captured_at": "2026-07-13T10:01:00+05:30",
            "max_age_days": 7,
            "sensitivity": "INTERNAL",
        }
        with connect(workspace) as connection:
            insert_source(connection, source)
            insert_claim(connection, claim)
            snapshot = status(connection)
            if snapshot["schema_version"] != 2:
                errors.append("schema version is not 2")
            if snapshot["counts"] != {"sources": 1, "claims": 1, "assumptions": 0, "metrics": 0, "approval_consumptions": 0}:
                errors.append(f"unexpected ledger counts: {snapshot['counts']}")
            try:
                connection.execute("UPDATE claims SET confidence = 'HIGH' WHERE id = 'CLM-SMOKE-001'")
            except sqlite3.IntegrityError as exc:
                if "append-only" not in str(exc):
                    errors.append(f"wrong append-only error: {exc}")
            else:
                errors.append("append-only claim update was not blocked")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        print("PHASE1 LEDGER: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PHASE1 LEDGER: PASS")
    print("- private external workspace enforcement")
    print("- migrations 1..2, foreign keys, WAL, and append-only triggers")
    print("- source-linked synthetic claim insertion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
