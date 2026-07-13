"""Hash-bound exact approvals for private truth-ledger mutations."""
from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .constants import DB_RELATIVE_PATH, SCHEMA_VERSION
from .store import (
    insert_assumption,
    insert_claim,
    insert_metric,
    insert_source,
    utc_now,
)
from .validation import TruthStoreError, canonical_json, parse_datetime, record_hash

ACTION_TO_KIND = {
    "record_truth_source": "source",
    "record_truth_claim": "claim",
    "record_truth_assumption": "assumption",
    "record_truth_metric": "metric",
}
INSERT_FUNCTIONS: dict[str, Callable[..., str]] = {
    "source": insert_source,
    "claim": insert_claim,
    "assumption": insert_assumption,
    "metric": insert_metric,
}
ACTION_ID_RE = re.compile(r"^ACT-[0-9]{4}-[0-9]{5,}$")
APPROVAL_ID_RE = re.compile(r"^APR-[0-9]{4}-[0-9]{5,}$")
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
MANIFEST_KEYS = {
    "action_id", "action_type", "task_id", "experiment_id", "scope", "payload_hash",
    "requested_by", "created_at", "maximum_records", "maximum_spend", "currency",
}
APPROVAL_KEYS = {
    "approval_id", "action_id", "manifest_hash", "approved_by", "approved_at",
    "expires_at", "single_use", "consumed_at",
}


@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    action_id: str
    action_type: str
    manifest_hash: str
    payload_hash: str
    record_type: str
    record_id: str


def canonical_hash(payload: object) -> str:
    return "sha256:" + __import__("hashlib").sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TruthStoreError(f"cannot load JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TruthStoreError(f"JSON document must be an object: {path}")
    return value


def workspace_id(workspace: Path) -> str:
    path = workspace / "workspace.json"
    data = load_json_object(path)
    value = data.get("workspace_id")
    if not isinstance(value, str) or not re.fullmatch(r"^WS-[A-Z0-9-]{8,80}$", value):
        raise TruthStoreError("workspace.json must contain a valid workspace_id")
    if data.get("public_repo") is not False:
        raise TruthStoreError("truth approvals require a private workspace")
    return value


def _identifier(prefix: str, now: datetime) -> str:
    return f"{prefix}-{now.year}-{secrets.randbelow(10**10):010d}"


def _now(value: str | None = None) -> datetime:
    normalized = parse_datetime(value or utc_now(), "now")
    assert normalized is not None
    return datetime.fromisoformat(normalized)


def expected_scope(workspace: Path, action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    scope: dict[str, Any] = {
        "workspace_id": workspace_id(workspace),
        "database": DB_RELATIVE_PATH.as_posix(),
    }
    if action_type == "initialize_truth_ledger":
        scope["schema_version"] = SCHEMA_VERSION
    else:
        record_id = payload.get("id")
        if not isinstance(record_id, str):
            raise TruthStoreError("truth record payload must contain an id")
        scope["record_id"] = record_id
    return scope


def prepare_manifest(
    workspace: Path,
    action_type: str,
    payload: dict[str, Any],
    *,
    requested_by: str,
    task_id: str,
    experiment_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    if action_type != "initialize_truth_ledger" and action_type not in ACTION_TO_KIND:
        raise TruthStoreError(f"unsupported truth action: {action_type}")
    if not requested_by.strip() or not task_id.strip():
        raise TruthStoreError("requested_by and task_id are required")
    now = _now(created_at)
    return {
        "action_id": _identifier("ACT", now),
        "action_type": action_type,
        "task_id": task_id,
        "experiment_id": experiment_id,
        "scope": expected_scope(workspace, action_type, payload),
        "payload_hash": canonical_hash(payload),
        "requested_by": requested_by,
        "created_at": now.isoformat(),
        "maximum_records": 0 if action_type == "initialize_truth_ledger" else 1,
        "maximum_spend": 0,
        "currency": None,
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    unknown = set(manifest) - MANIFEST_KEYS
    required = {"action_id", "action_type", "task_id", "scope", "payload_hash", "requested_by", "created_at"}
    missing = required - set(manifest)
    if unknown or missing:
        raise TruthStoreError(f"invalid manifest fields; missing={sorted(missing)} unknown={sorted(unknown)}")
    if not isinstance(manifest["action_id"], str) or not ACTION_ID_RE.fullmatch(manifest["action_id"]):
        raise TruthStoreError("invalid action_id")
    if manifest["action_type"] != "initialize_truth_ledger" and manifest["action_type"] not in ACTION_TO_KIND:
        raise TruthStoreError("unsupported manifest action_type")
    if not isinstance(manifest["task_id"], str) or not manifest["task_id"].strip():
        raise TruthStoreError("manifest task_id is required")
    if not isinstance(manifest["requested_by"], str) or not manifest["requested_by"].strip():
        raise TruthStoreError("manifest requested_by is required")
    if not isinstance(manifest["scope"], dict):
        raise TruthStoreError("manifest scope must be an object")
    if not isinstance(manifest["payload_hash"], str) or not HASH_RE.fullmatch(manifest["payload_hash"]):
        raise TruthStoreError("manifest payload_hash is invalid")
    parse_datetime(manifest["created_at"], "manifest.created_at")
    expected_maximum = 0 if manifest["action_type"] == "initialize_truth_ledger" else 1
    if manifest.get("maximum_records") != expected_maximum:
        raise TruthStoreError(f"manifest maximum_records must be {expected_maximum}")
    if manifest.get("maximum_spend", 0) != 0:
        raise TruthStoreError("truth actions cannot authorize spending")
    if manifest.get("currency") is not None:
        raise TruthStoreError("truth actions must not specify currency")


def create_approval(
    manifest: dict[str, Any],
    *,
    approved_by: str,
    approved_at: str | None = None,
    expires_minutes: int = 30,
) -> dict[str, Any]:
    validate_manifest(manifest)
    if not approved_by.strip():
        raise TruthStoreError("approved_by is required")
    if not 1 <= expires_minutes <= 1440:
        raise TruthStoreError("approval expiry must be 1..1440 minutes")
    now = _now(approved_at)
    return {
        "approval_id": _identifier("APR", now),
        "action_id": manifest["action_id"],
        "manifest_hash": canonical_hash(manifest),
        "approved_by": approved_by,
        "approved_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=expires_minutes)).isoformat(),
        "single_use": True,
        "consumed_at": None,
    }


def validate_approval(
    workspace: Path,
    action_type: str,
    payload: dict[str, Any],
    manifest: dict[str, Any],
    approval: dict[str, Any],
    *,
    now: str | None = None,
) -> ApprovalDecision:
    validate_manifest(manifest)
    unknown = set(approval) - APPROVAL_KEYS
    required = {"approval_id", "action_id", "manifest_hash", "approved_by", "approved_at", "expires_at", "single_use"}
    missing = required - set(approval)
    if unknown or missing:
        raise TruthStoreError(f"invalid approval fields; missing={sorted(missing)} unknown={sorted(unknown)}")
    if not isinstance(approval["approval_id"], str) or not APPROVAL_ID_RE.fullmatch(approval["approval_id"]):
        raise TruthStoreError("invalid approval_id")
    if approval.get("action_id") != manifest["action_id"]:
        raise TruthStoreError("approval action_id does not match manifest")
    if approval.get("manifest_hash") != canonical_hash(manifest):
        raise TruthStoreError("approval manifest_hash does not match manifest")
    if manifest["action_type"] != action_type:
        raise TruthStoreError("manifest action_type does not match requested action")
    if manifest["payload_hash"] != canonical_hash(payload):
        raise TruthStoreError("manifest payload_hash does not match payload")
    if manifest["scope"] != expected_scope(workspace, action_type, payload):
        raise TruthStoreError("manifest scope does not match workspace and payload")
    if approval.get("single_use") is not True:
        raise TruthStoreError("approval must be single-use")
    if approval.get("consumed_at") is not None:
        raise TruthStoreError("approval file is already marked consumed")
    if not isinstance(approval.get("approved_by"), str) or not approval["approved_by"].strip():
        raise TruthStoreError("approval approved_by is required")
    created = datetime.fromisoformat(parse_datetime(manifest["created_at"], "manifest.created_at") or "")
    approved = datetime.fromisoformat(parse_datetime(approval["approved_at"], "approval.approved_at") or "")
    expires = datetime.fromisoformat(parse_datetime(approval["expires_at"], "approval.expires_at") or "")
    current = _now(now)
    if approved < created:
        raise TruthStoreError("approval predates the action manifest")
    if approved > current:
        raise TruthStoreError("approval is from the future")
    if expires <= approved or current >= expires:
        raise TruthStoreError("approval has expired")
    if expires - approved > timedelta(minutes=1440):
        raise TruthStoreError("approval validity exceeds 1440 minutes")
    record_type = "ledger" if action_type == "initialize_truth_ledger" else ACTION_TO_KIND[action_type]
    record_id = f"SCHEMA-{SCHEMA_VERSION}" if action_type == "initialize_truth_ledger" else str(payload["id"])
    return ApprovalDecision(
        approval_id=approval["approval_id"],
        action_id=manifest["action_id"],
        action_type=action_type,
        manifest_hash=approval["manifest_hash"],
        payload_hash=manifest["payload_hash"],
        record_type=record_type,
        record_id=record_id,
    )


def consume_approval(connection: sqlite3.Connection, decision: ApprovalDecision) -> None:
    connection.execute(
        """INSERT INTO approval_consumptions(
               approval_id, action_id, action_type, manifest_hash, payload_hash,
               record_type, record_id, consumed_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            decision.approval_id,
            decision.action_id,
            decision.action_type,
            decision.manifest_hash,
            decision.payload_hash,
            decision.record_type,
            decision.record_id,
            utc_now(),
        ),
    )


def approved_insert(
    connection: sqlite3.Connection,
    workspace: Path,
    action_type: str,
    payload: dict[str, Any],
    manifest: dict[str, Any],
    approval: dict[str, Any],
    *,
    now: str | None = None,
) -> str:
    decision = validate_approval(workspace, action_type, payload, manifest, approval, now=now)
    kind = ACTION_TO_KIND.get(action_type)
    if kind is None:
        raise TruthStoreError(f"approved_insert does not support {action_type}")
    insert = INSERT_FUNCTIONS[kind]
    with connection:
        record_id = insert(connection, payload, commit=False)
        consume_approval(connection, decision)
    return record_id


def write_private_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
