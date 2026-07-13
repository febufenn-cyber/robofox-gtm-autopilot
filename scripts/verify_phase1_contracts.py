#!/usr/bin/env python3
"""Verify Phase 1 public contracts without third-party dependencies."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "PHASE1.md",
    "policies/truth-layer-policy.md",
    "decisions/ADR-0006-immutable-observations.md",
    "decisions/ADR-0007-private-sqlite-ledger.md",
    "decisions/ADR-0008-derived-position-snapshots.md",
    "config/position-dimensions.json",
    "schemas/source-record.schema.json",
    "schemas/claim-record.schema.json",
    "schemas/assumption-record.schema.json",
    "schemas/metric-record.schema.json",
    "schemas/position-snapshot.schema.json",
]

EVIDENCE_STATES = {"VERIFIED", "OBSERVED", "INFERRED", "ASSUMED", "UNKNOWN", "PROHIBITED"}
SENSITIVITY = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}


def verify(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing Phase 1 contract: {relative}")

    schemas: dict[str, dict] = {}
    for relative in [p for p in REQUIRED_FILES if p.endswith(".json")]:
        path = root / relative
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {relative}: {exc}")
            continue
        schemas[relative] = data
        if relative.startswith("schemas/"):
            if data.get("type") != "object":
                errors.append(f"schema is not an object: {relative}")
            if data.get("additionalProperties") is not False:
                errors.append(f"schema must fail closed with additionalProperties=false: {relative}")
            if not data.get("required"):
                errors.append(f"schema has no required fields: {relative}")

    claim = schemas.get("schemas/claim-record.schema.json", {})
    claim_states = set(claim.get("properties", {}).get("evidence_state", {}).get("enum", []))
    if claim_states != EVIDENCE_STATES:
        errors.append(f"claim evidence states differ: {sorted(claim_states)}")
    claim_sensitivity = set(claim.get("properties", {}).get("sensitivity", {}).get("enum", []))
    if claim_sensitivity != SENSITIVITY:
        errors.append("claim sensitivity enum differs")

    dimensions_path = root / "config/position-dimensions.json"
    if dimensions_path.is_file():
        try:
            dimensions = json.loads(dimensions_path.read_text(encoding="utf-8"))
            keys = [item.get("key") for item in dimensions.get("dimensions", [])]
            if dimensions.get("version") != 1:
                errors.append("position dimensions version must be 1")
            if len(keys) != 10 or len(set(keys)) != len(keys):
                errors.append("position dimensions must contain 10 unique keys")
            if any(not isinstance(item.get("max_age_days"), int) or item["max_age_days"] < 1 for item in dimensions.get("dimensions", [])):
                errors.append("every position dimension needs a positive max_age_days")
            if any(item.get("subject") != "commercial-position" for item in dimensions.get("dimensions", [])):
                errors.append("every position dimension must bind to commercial-position")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid position dimensions: {exc}")

    policy = root / "policies/truth-layer-policy.md"
    if policy.is_file():
        text = policy.read_text(encoding="utf-8")
        for phrase in ("Append-only history", "Missing, zero, and unknown", "Contradiction", "Staleness", "External instructions", "Fail closed"):
            if phrase not in text:
                errors.append(f"truth policy missing section: {phrase}")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        print("PHASE1 CONTRACTS: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PHASE1 CONTRACTS: PASS")
    print("- immutable source, claim, assumption, metric, and snapshot contracts")
    print("- 10 dated position dimensions")
    print("- closed schemas and fail-closed truth policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
