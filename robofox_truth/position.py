"""Derived commercial-position snapshots for the Robofox truth layer."""
from __future__ import annotations

import html
import json
import os
import sqlite3
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .constants import ENGINE_ROOT
from .store import connect, resolve_workspace
from .validation import TruthStoreError, canonical_json, parse_datetime, require_product

EVIDENCE_RANK = {
    "VERIFIED": 6,
    "OBSERVED": 5,
    "INFERRED": 4,
    "ASSUMED": 2,
    "UNKNOWN": 0,
    "PROHIBITED": -100,
}
CONFIDENCE_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
SOURCE_RANK = {
    "PRODUCT_TELEMETRY": 8,
    "CRM": 7,
    "META_ADS": 7,
    "CUSTOMER_INTERVIEW": 6,
    "CALL_TEST": 6,
    "FOUNDER_OBSERVATION": 5,
    "DOCUMENT": 3,
    "PUBLIC_BENCHMARK": 2,
    "OTHER": 1,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_as_of(value: str | None) -> datetime:
    normalized = parse_datetime(value or utc_now(), "as_of")
    assert normalized is not None
    return datetime.fromisoformat(normalized)


def load_dimensions(path: Path | None = None) -> list[dict[str, Any]]:
    source = path or ENGINE_ROOT / "config" / "position-dimensions.json"
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TruthStoreError(f"cannot load position dimensions: {exc}") from exc
    if data.get("version") != 1 or not isinstance(data.get("dimensions"), list):
        raise TruthStoreError("unsupported position-dimensions contract")
    dimensions = data["dimensions"]
    seen: set[tuple[str, str]] = set()
    for item in dimensions:
        if not isinstance(item, dict):
            raise TruthStoreError("position dimension entries must be objects")
        required = {"key", "subject", "label", "max_age_days"}
        if set(item) != required:
            raise TruthStoreError("position dimension entries must contain only key, subject, label, and max_age_days")
        pair = (item["subject"], item["key"])
        if pair in seen:
            raise TruthStoreError(f"duplicate position dimension: {pair[0]}.{pair[1]}")
        seen.add(pair)
        if not isinstance(item["max_age_days"], int) or isinstance(item["max_age_days"], bool) or item["max_age_days"] < 1:
            raise TruthStoreError("position dimension max_age_days must be a positive integer")
    return dimensions


def _row_datetime(row: dict[str, Any], field: str) -> datetime | None:
    value = row.get(field)
    return datetime.fromisoformat(value) if value else None


def _eligible_at(row: dict[str, Any], as_of: datetime, captured_field: str) -> bool:
    captured = _row_datetime(row, captured_field)
    if captured is None or captured > as_of:
        return False
    valid_from = _row_datetime(row, "valid_from")
    return valid_from is None or valid_from <= as_of


def _active_records(rows: list[dict[str, Any]], as_of: datetime, captured_field: str) -> list[dict[str, Any]]:
    eligible = [row for row in rows if _eligible_at(row, as_of, captured_field)]
    superseded = {row["supersedes_id"] for row in eligible if row.get("supersedes_id")}
    return [row for row in eligible if row["id"] not in superseded]


def _stale_reasons(claim: dict[str, Any], as_of: datetime, default_max_age: int | None) -> list[str]:
    reasons: list[str] = []
    valid_until = _row_datetime(claim, "valid_until")
    if valid_until is not None and valid_until < as_of:
        reasons.append("valid_until_passed")
    max_age = claim.get("max_age_days") or default_max_age
    anchor = _row_datetime(claim, "observed_at") or _row_datetime(claim, "captured_at")
    if max_age and anchor is not None and anchor + timedelta(days=int(max_age)) < as_of:
        reasons.append("maximum_age_exceeded")
    return reasons


def _source_ranks(connection: sqlite3.Connection, claim_ids: Iterable[str]) -> dict[str, int]:
    ids = list(claim_ids)
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    rows = connection.execute(
        f"""SELECT cs.claim_id, s.source_type
             FROM claim_sources cs JOIN sources s ON s.id = cs.source_id
             WHERE cs.claim_id IN ({placeholders})""",
        ids,
    )
    ranks: dict[str, int] = defaultdict(int)
    for claim_id, source_type in rows:
        ranks[claim_id] = max(ranks[claim_id], SOURCE_RANK.get(source_type, 0))
    return dict(ranks)


def _source_ids(connection: sqlite3.Connection, claim_ids: Iterable[str]) -> set[str]:
    ids = list(claim_ids)
    if not ids:
        return set()
    placeholders = ",".join("?" for _ in ids)
    return {
        row[0]
        for row in connection.execute(
            f"SELECT DISTINCT source_id FROM claim_sources WHERE claim_id IN ({placeholders})",
            ids,
        )
    }


def _rank_claim(claim: dict[str, Any], source_rank: int, stale: bool) -> tuple[Any, ...]:
    observed = _row_datetime(claim, "observed_at") or _row_datetime(claim, "captured_at")
    timestamp = observed.timestamp() if observed is not None else 0.0
    return (
        0 if stale else 1,
        EVIDENCE_RANK.get(claim["evidence_state"], -1),
        source_rank,
        CONFIDENCE_RANK.get(claim["confidence"], 0),
        timestamp,
        claim["id"],
    )


def _distinct_values(claims: list[dict[str, Any]]) -> list[Any]:
    values: list[Any] = []
    fingerprints: set[str] = set()
    for claim in claims:
        fingerprint = canonical_json(claim["value"])
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            values.append(claim["value"])
    return values


def _load_claims(connection: sqlite3.Connection, product: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        """SELECT id, product, subject, predicate, value_json, unit, evidence_state,
                  confidence, captured_at, observed_at, valid_from, valid_until,
                  max_age_days, supersedes_id, sensitivity
           FROM claims WHERE product = ? ORDER BY captured_at, id""",
        (product,),
    )
    result = []
    for row in rows:
        item = dict(row)
        item["value"] = json.loads(item.pop("value_json"))
        result.append(item)
    return result


def _load_assumptions(connection: sqlite3.Connection, product: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in connection.execute(
            """SELECT id, product, statement, status, confidence, created_at, review_by,
                      supersedes_id, sensitivity
               FROM assumptions WHERE product = ? ORDER BY created_at, id""",
            (product,),
        )
    ]


def build_snapshot(
    connection: sqlite3.Connection,
    product: str,
    *,
    as_of: str | None = None,
    generated_at: str | None = None,
    dimensions_path: Path | None = None,
) -> dict[str, Any]:
    """Build a traceable, redacted snapshot without mutating the ledger."""
    product = require_product(product)
    as_of_dt = parse_as_of(as_of)
    generated = parse_datetime(generated_at or utc_now(), "generated_at")
    assert generated is not None
    generated_dt = datetime.fromisoformat(generated)
    if as_of_dt > generated_dt:
        raise TruthStoreError("as_of cannot be later than generated_at")
    dimensions_config = load_dimensions(dimensions_path)

    active_claims = _active_records(_load_claims(connection, product), as_of_dt, "captured_at")
    active_assumptions = _active_records(_load_assumptions(connection, product), as_of_dt, "created_at")

    prohibited_claims = [claim for claim in active_claims if claim["evidence_state"] == "PROHIBITED"]
    restricted_claims = [claim for claim in active_claims if claim["sensitivity"] == "RESTRICTED"]
    restricted_assumptions = [item for item in active_assumptions if item["sensitivity"] == "RESTRICTED"]
    usable_claims = [
        claim
        for claim in active_claims
        if claim["evidence_state"] != "PROHIBITED" and claim["sensitivity"] != "RESTRICTED"
    ]
    usable_assumptions = [item for item in active_assumptions if item["sensitivity"] != "RESTRICTED"]

    dimension_lookup = {(item["subject"], item["key"]): item for item in dimensions_config}
    stale_by_id: dict[str, list[str]] = {}
    for claim in usable_claims:
        config = dimension_lookup.get((claim["subject"], claim["predicate"]))
        reasons = _stale_reasons(claim, as_of_dt, config.get("max_age_days") if config else None)
        if reasons:
            stale_by_id[claim["id"]] = reasons

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for claim in usable_claims:
        groups[(claim["subject"], claim["predicate"])].append(claim)

    conflicts: list[dict[str, Any]] = []
    blocking_conflict_keys: set[tuple[str, str]] = set()
    for key, claims in sorted(groups.items()):
        known = [claim for claim in claims if claim["evidence_state"] != "UNKNOWN"]
        current = [claim for claim in known if claim["id"] not in stale_by_id]
        current_values = _distinct_values(current)
        all_values = _distinct_values(known)
        if len(current_values) > 1:
            blocking_conflict_keys.add(key)
            conflicts.append(
                {
                    "subject": key[0],
                    "predicate": key[1],
                    "claim_ids": sorted(claim["id"] for claim in known),
                    "values": all_values,
                    "stale_claim_ids": sorted(claim["id"] for claim in known if claim["id"] in stale_by_id),
                    "resolution": "UNRESOLVED",
                    "blocks_dimension": True,
                }
            )
        elif len(all_values) > 1:
            conflicts.append(
                {
                    "subject": key[0],
                    "predicate": key[1],
                    "claim_ids": sorted(claim["id"] for claim in known),
                    "values": all_values,
                    "stale_claim_ids": sorted(claim["id"] for claim in known if claim["id"] in stale_by_id),
                    "resolution": "STALE_DISAGREEMENT",
                    "blocks_dimension": False,
                }
            )

    source_ranks = _source_ranks(connection, [claim["id"] for claim in usable_claims])
    dimensions: dict[str, dict[str, Any]] = {}
    unknown_dimensions: list[str] = []
    input_record_ids: set[str] = set()

    for config in dimensions_config:
        key = config["key"]
        group_key = (config["subject"], key)
        candidates = groups.get(group_key, [])
        if not candidates:
            dimensions[key] = {"label": config["label"], "status": "UNKNOWN", "claim_ids": []}
            unknown_dimensions.append(key)
            continue
        input_record_ids.update(claim["id"] for claim in candidates)
        if group_key in blocking_conflict_keys:
            dimensions[key] = {
                "label": config["label"],
                "status": "CONFLICTED",
                "claim_ids": sorted(claim["id"] for claim in candidates),
                "value_withheld": True,
            }
            continue
        preferred = max(
            candidates,
            key=lambda claim: _rank_claim(
                claim,
                source_ranks.get(claim["id"], 0),
                claim["id"] in stale_by_id,
            ),
        )
        reasons = stale_by_id.get(preferred["id"], [])
        status = "STALE" if reasons else preferred["evidence_state"]
        if status == "UNKNOWN":
            unknown_dimensions.append(key)
        dimensions[key] = {
            "label": config["label"],
            "status": status,
            "value": preferred["value"],
            "unit": preferred["unit"],
            "claim_id": preferred["id"],
            "evidence_state": preferred["evidence_state"],
            "confidence": preferred["confidence"],
            "observed_at": preferred["observed_at"] or preferred["captured_at"],
            "stale_reasons": reasons,
        }

    conflict_claim_ids = {claim_id for conflict in conflicts for claim_id in conflict["claim_ids"]}
    input_record_ids.update(conflict_claim_ids)
    input_record_ids.update(_source_ids(connection, input_record_ids))

    open_assumptions = [item for item in usable_assumptions if item["status"] == "OPEN"]
    input_record_ids.update(item["id"] for item in open_assumptions)
    overdue_assumptions = [
        item["id"]
        for item in open_assumptions
        if item.get("review_by") and datetime.fromisoformat(item["review_by"]) < as_of_dt
    ]

    return {
        "version": 1,
        "product": product,
        "as_of": as_of_dt.isoformat(),
        "generated_at": generated,
        "dimensions": dimensions,
        "conflicts": conflicts,
        "stale_claim_ids": sorted(stale_by_id),
        "open_assumption_ids": sorted(item["id"] for item in open_assumptions),
        "overdue_assumption_ids": sorted(overdue_assumptions),
        "unknown_dimensions": sorted(set(unknown_dimensions)),
        "restricted_records_excluded": len(restricted_claims) + len(restricted_assumptions),
        "prohibited_claims_excluded": len(prohibited_claims),
        "input_record_ids": sorted(input_record_ids),
    }


def _markdown_cell(value: Any) -> str:
    text = html.escape(canonical_json(value), quote=False)
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        f"# {snapshot['product']} commercial position",
        "",
        f"**As of:** {snapshot['as_of']}",
        f"**Generated:** {snapshot['generated_at']}",
        "",
        "## Position",
        "",
        "| Dimension | Status | Value | Evidence |",
        "|---|---|---|---|",
    ]
    for item in snapshot["dimensions"].values():
        value = "—" if item.get("value_withheld") or "value" not in item else _markdown_cell(item["value"])
        evidence = item.get("claim_id", ", ".join(item.get("claim_ids", [])) or "—")
        lines.append(f"| {item['label']} | {item['status']} | {value} | {evidence} |")
    lines.extend(["", "## Blind spots", ""])
    lines.append(f"- Unknown dimensions: {', '.join(snapshot['unknown_dimensions']) or 'none'}")
    lines.append(f"- Stale claims: {', '.join(snapshot['stale_claim_ids']) or 'none'}")
    lines.append(f"- Open assumptions: {', '.join(snapshot['open_assumption_ids']) or 'none'}")
    lines.append(f"- Overdue assumptions: {', '.join(snapshot['overdue_assumption_ids']) or 'none'}")
    lines.append(f"- Restricted records excluded: {snapshot['restricted_records_excluded']}")
    lines.append(f"- Prohibited claims excluded: {snapshot['prohibited_claims_excluded']}")
    lines.extend(["", "## Conflicts and disagreements", ""])
    if not snapshot["conflicts"]:
        lines.append("None.")
    else:
        for conflict in snapshot["conflicts"]:
            qualifier = "value withheld" if conflict["blocks_dimension"] else "stale disagreement; current value retained"
            lines.append(
                f"- `{conflict['subject']}.{conflict['predicate']}` ({conflict['resolution']}): "
                f"{', '.join(conflict['claim_ids'])}; {qualifier}."
            )
    lines.extend(["", "## Traceability", "", ", ".join(snapshot["input_record_ids"]) or "No input records.", ""])
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _filename_timestamp(value: str) -> str:
    return value.replace(":", "").replace("+", "p").replace(".", "_")


def write_snapshot(workspace: Path, snapshot: dict[str, Any]) -> tuple[Path, Path]:
    output = workspace / "snapshots"
    as_of_stamp = _filename_timestamp(snapshot["as_of"])
    generated_stamp = _filename_timestamp(snapshot["generated_at"])
    stem = f"{snapshot['product']}-position-{as_of_stamp}-generated-{generated_stamp}"
    json_path = output / f"{stem}.json"
    markdown_path = output / f"{stem}.md"
    _atomic_write(json_path, json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    _atomic_write(markdown_path, render_markdown(snapshot))
    return json_path, markdown_path


def build_and_write(
    workspace_path: str | Path | None,
    product: str,
    *,
    as_of: str | None = None,
) -> tuple[dict[str, Any], Path, Path]:
    workspace = resolve_workspace(workspace_path)
    with connect(workspace) as connection:
        snapshot = build_snapshot(connection, product, as_of=as_of)
    json_path, markdown_path = write_snapshot(workspace, snapshot)
    return snapshot, json_path, markdown_path
