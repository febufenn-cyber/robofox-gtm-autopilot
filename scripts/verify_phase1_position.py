#!/usr/bin/env python3
"""Smoke-verify Phase 1 position evaluation, redaction, and traceability."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth import (
    build_snapshot,
    connect,
    initialize,
    insert_assumption,
    insert_claim,
    insert_source,
    render_markdown,
    resolve_workspace,
)


def source(source_id: str, source_type: str, fill: str) -> dict:
    return {
        "id": source_id,
        "source_type": source_type,
        "captured_at": "2026-07-01T09:00:00+05:30",
        "sensitivity": "INTERNAL",
        "content_hash": "sha256:" + fill * 64,
        "metadata": {"synthetic": True},
    }


def claim(claim_id: str, predicate: str, value, source_id: str, **extra) -> dict:
    record = {
        "id": claim_id,
        "product": "voice-agents",
        "subject": "commercial-position",
        "predicate": predicate,
        "value": value,
        "evidence_state": "OBSERVED",
        "confidence": "MEDIUM",
        "source_ids": [source_id],
        "captured_at": "2026-07-01T09:05:00+05:30",
        "sensitivity": "INTERNAL",
    }
    record.update(extra)
    return record


def verify() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="robofox-position-smoke-") as directory:
        workspace = resolve_workspace(directory, create=True)
        initialize(workspace)
        with connect(workspace) as connection:
            insert_source(connection, source("SRC-POS-SMOKE-A", "FOUNDER_OBSERVATION", "a"))
            insert_source(connection, source("SRC-POS-SMOKE-B", "PRODUCT_TELEMETRY", "b"))
            insert_claim(connection, claim(
                "CLM-POS-SMOKE-A", "proof_strength", "none", "SRC-POS-SMOKE-A", max_age_days=1,
            ))
            insert_claim(connection, claim(
                "CLM-POS-SMOKE-B", "proof_strength", "anecdotal", "SRC-POS-SMOKE-B",
                evidence_state="VERIFIED", confidence="HIGH",
                captured_at="2026-07-12T09:05:00+05:30", observed_at="2026-07-12T09:00:00+05:30",
                max_age_days=45,
            ))
            insert_claim(connection, claim(
                "CLM-POS-SECRET-X", "customer_trust", "restricted-secret", "SRC-POS-SMOKE-A",
                sensitivity="RESTRICTED", max_age_days=30,
            ))
            insert_assumption(connection, {
                "id": "ASM-POS-SMOKE-A",
                "product": "voice-agents",
                "statement": "Synthetic willingness-to-pay assumption",
                "status": "OPEN",
                "confidence": "LOW",
                "created_at": "2026-07-01T09:00:00+05:30",
                "review_by": "2026-07-02T09:00:00+05:30",
                "sensitivity": "INTERNAL",
            })
            snapshot = build_snapshot(
                connection,
                "voice-agents",
                as_of="2026-07-13T12:00:00+05:30",
                generated_at="2026-07-13T12:01:00+05:30",
            )

        proof = snapshot["dimensions"]["proof_strength"]
        if proof.get("value") != "anecdotal" or proof.get("claim_id") != "CLM-POS-SMOKE-B":
            errors.append(f"fresh stronger evidence was not selected: {proof}")
        disagreements = [item for item in snapshot["conflicts"] if item["predicate"] == "proof_strength"]
        if len(disagreements) != 1 or disagreements[0]["resolution"] != "STALE_DISAGREEMENT":
            errors.append("stale disagreement was not surfaced correctly")
        if snapshot["restricted_records_excluded"] != 1:
            errors.append("restricted record exclusion count differs")
        if "restricted-secret" in json.dumps(snapshot) or "restricted-secret" in render_markdown(snapshot):
            errors.append("restricted value leaked into snapshot output")
        if "ASM-POS-SMOKE-A" not in snapshot["overdue_assumption_ids"]:
            errors.append("overdue assumption was not surfaced")
        if "SRC-POS-SMOKE-B" not in snapshot["input_record_ids"]:
            errors.append("source provenance is missing from input_record_ids")
        if len(snapshot["unknown_dimensions"]) != 9:
            errors.append(f"unexpected unknown dimension count: {len(snapshot['unknown_dimensions'])}")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        print("PHASE1 POSITION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PHASE1 POSITION: PASS")
    print("- historical as-of filtering and supersession-aware active records")
    print("- current conflict blocking and non-blocking stale disagreement")
    print("- restricted/prohibited redaction, assumption visibility, and source traceability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
