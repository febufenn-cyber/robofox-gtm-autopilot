"""Strict zero-dependency validation for truth records."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any

from .constants import (
    ASSUMPTION_KEYS,
    ASSUMPTION_STATUS,
    CLAIM_KEYS,
    CONFIDENCE,
    EVIDENCE_STATES,
    ID_PATTERNS,
    METRIC_KEYS,
    PREDICATE_RE,
    PRODUCT_RE,
    SENSITIVITY,
    SOURCE_KEYS,
    SOURCE_TYPES,
)


class TruthStoreError(ValueError):
    """Raised when a record or workspace violates Phase 1 constraints."""


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise TruthStoreError(f"value is not canonical JSON: {exc}") from exc


def record_hash(record: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def parse_datetime(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise TruthStoreError(f"{field} must be a timezone-aware date-time string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TruthStoreError(f"{field} is not a valid ISO-8601 date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TruthStoreError(f"{field} must include a timezone offset")
    return parsed.isoformat()


def require_exact_keys(record: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    unknown = set(record) - allowed
    missing = required - set(record)
    if unknown:
        raise TruthStoreError(f"unknown fields: {sorted(unknown)}")
    if missing:
        raise TruthStoreError(f"missing fields: {sorted(missing)}")


def require_string(value: Any, field: str, *, minimum: int = 1, maximum: int = 2000, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise TruthStoreError(f"{field} must be a string of length {minimum}..{maximum}")
    return value


def require_id(value: Any, kind: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not ID_PATTERNS[kind].fullmatch(value):
        raise TruthStoreError(f"invalid {kind} id")
    return value


def require_product(value: Any) -> str:
    if not isinstance(value, str) or not PRODUCT_RE.fullmatch(value):
        raise TruthStoreError("product must be lowercase kebab-case")
    return value


def require_enum(value: Any, field: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise TruthStoreError(f"{field} must be one of {sorted(allowed)}")
    return str(value)


def require_string_list(value: Any, field: str, prefix: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.startswith(prefix) for item in value):
        raise TruthStoreError(f"{field} must be a list of {prefix} identifiers")
    if len(value) != len(set(value)):
        raise TruthStoreError(f"{field} contains duplicates")
    return sorted(value)


def validate_source(record: dict[str, Any]) -> dict[str, Any]:
    require_exact_keys(record, SOURCE_KEYS, {"id", "source_type", "captured_at", "sensitivity", "content_hash"})
    content_hash = require_string(record["content_hash"], "content_hash", minimum=71, maximum=71)
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", content_hash or ""):
        raise TruthStoreError("content_hash must be sha256:<64 lowercase hex chars>")
    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        raise TruthStoreError("metadata must be an object")
    return {
        "id": require_id(record["id"], "source"),
        "source_type": require_enum(record["source_type"], "source_type", SOURCE_TYPES),
        "external_reference": require_string(record.get("external_reference"), "external_reference", maximum=500, nullable=True),
        "captured_at": parse_datetime(record["captured_at"], "captured_at"),
        "observed_at": parse_datetime(record.get("observed_at"), "observed_at", nullable=True),
        "sensitivity": require_enum(record["sensitivity"], "sensitivity", SENSITIVITY),
        "content_hash": content_hash,
        "metadata": metadata,
    }


def validate_claim(record: dict[str, Any]) -> dict[str, Any]:
    required = {"id", "product", "subject", "predicate", "value", "evidence_state", "confidence", "captured_at", "sensitivity"}
    require_exact_keys(record, CLAIM_KEYS, required)
    state = require_enum(record["evidence_state"], "evidence_state", EVIDENCE_STATES)
    source_ids = require_string_list(record.get("source_ids", []), "source_ids", "SRC-")
    if state in {"VERIFIED", "OBSERVED", "INFERRED"} and not source_ids:
        raise TruthStoreError(f"{state} claims require at least one source_id")
    predicate = require_string(record["predicate"], "predicate", maximum=80)
    if not PREDICATE_RE.fullmatch(predicate or ""):
        raise TruthStoreError("predicate must be lowercase snake_case")
    max_age = record.get("max_age_days")
    if max_age is not None and (not isinstance(max_age, int) or isinstance(max_age, bool) or not 1 <= max_age <= 3650):
        raise TruthStoreError("max_age_days must be an integer from 1 to 3650")
    valid_from = parse_datetime(record.get("valid_from"), "valid_from", nullable=True)
    valid_until = parse_datetime(record.get("valid_until"), "valid_until", nullable=True)
    if valid_from is not None and valid_until is not None and datetime.fromisoformat(valid_until) < datetime.fromisoformat(valid_from):
        raise TruthStoreError("valid_until cannot precede valid_from")
    return {
        "id": require_id(record["id"], "claim"),
        "product": require_product(record["product"]),
        "subject": require_string(record["subject"], "subject", maximum=120),
        "predicate": predicate,
        "value": record["value"],
        "unit": require_string(record.get("unit"), "unit", maximum=40, nullable=True),
        "evidence_state": state,
        "confidence": require_enum(record["confidence"], "confidence", CONFIDENCE),
        "source_ids": source_ids,
        "captured_at": parse_datetime(record["captured_at"], "captured_at"),
        "observed_at": parse_datetime(record.get("observed_at"), "observed_at", nullable=True),
        "valid_from": valid_from,
        "valid_until": valid_until,
        "max_age_days": max_age,
        "supersedes_id": require_id(record.get("supersedes_id"), "claim", nullable=True),
        "sensitivity": require_enum(record["sensitivity"], "sensitivity", SENSITIVITY),
        "notes": require_string(record.get("notes"), "notes", maximum=2000, nullable=True),
    }


def validate_assumption(record: dict[str, Any]) -> dict[str, Any]:
    required = {"id", "product", "statement", "status", "confidence", "created_at", "sensitivity"}
    require_exact_keys(record, ASSUMPTION_KEYS, required)
    return {
        "id": require_id(record["id"], "assumption"),
        "product": require_product(record["product"]),
        "statement": require_string(record["statement"], "statement", maximum=2000),
        "status": require_enum(record["status"], "status", ASSUMPTION_STATUS),
        "confidence": require_enum(record["confidence"], "confidence", CONFIDENCE),
        "created_at": parse_datetime(record["created_at"], "created_at"),
        "review_by": parse_datetime(record.get("review_by"), "review_by", nullable=True),
        "resolution_claim_ids": require_string_list(record.get("resolution_claim_ids", []), "resolution_claim_ids", "CLM-"),
        "supersedes_id": require_id(record.get("supersedes_id"), "assumption", nullable=True),
        "sensitivity": require_enum(record["sensitivity"], "sensitivity", SENSITIVITY),
    }


def validate_metric(record: dict[str, Any]) -> dict[str, Any]:
    required = {"id", "product", "metric", "value", "unit", "period_start", "period_end", "captured_at", "sensitivity"}
    require_exact_keys(record, METRIC_KEYS, required)
    source_ids = require_string_list(record.get("source_ids", []), "source_ids", "SRC-")
    if not source_ids:
        raise TruthStoreError("metrics require at least one source_id")
    metric = require_string(record["metric"], "metric", maximum=80)
    if not PREDICATE_RE.fullmatch(metric or ""):
        raise TruthStoreError("metric must be lowercase snake_case")
    value = record["value"]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TruthStoreError("value must be numeric")
    denominator = record.get("denominator")
    if denominator is not None and (not isinstance(denominator, (int, float)) or isinstance(denominator, bool) or denominator < 0):
        raise TruthStoreError("denominator must be a non-negative number")
    sample_size = record.get("sample_size")
    if sample_size is not None and (not isinstance(sample_size, int) or isinstance(sample_size, bool) or sample_size < 0):
        raise TruthStoreError("sample_size must be a non-negative integer")
    period_start = parse_datetime(record["period_start"], "period_start")
    period_end = parse_datetime(record["period_end"], "period_end")
    if datetime.fromisoformat(period_end) < datetime.fromisoformat(period_start):
        raise TruthStoreError("period_end cannot precede period_start")
    return {
        "id": require_id(record["id"], "metric"),
        "product": require_product(record["product"]),
        "metric": metric,
        "value": float(value),
        "unit": require_string(record["unit"], "unit", maximum=40),
        "denominator": float(denominator) if denominator is not None else None,
        "sample_size": sample_size,
        "segment": require_string(record.get("segment"), "segment", maximum=120, nullable=True),
        "experiment_id": require_string(record.get("experiment_id"), "experiment_id", maximum=100, nullable=True),
        "source_ids": source_ids,
        "period_start": period_start,
        "period_end": period_end,
        "captured_at": parse_datetime(record["captured_at"], "captured_at"),
        "sensitivity": require_enum(record["sensitivity"], "sensitivity", SENSITIVITY),
    }
