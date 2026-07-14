"""Strict validation and canonical hashing for Phase 4 records."""
from __future__ import annotations
import hashlib, json
from datetime import datetime
from math import isfinite
from typing import Any
from .constants import ACTION_TO_ADAPTER, ADAPTERS, HASH_RE, IDEMPOTENCY_RE, ID_PATTERNS, MODES, OUTCOMES, ROLLBACK_OUTCOMES, TARGET_RE

class ExecutionError(ValueError):
    pass

def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ExecutionError(f"value is not canonical JSON: {exc}") from exc

def canonical_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()

def parse_time(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ExecutionError(f"{field} must be a timezone-aware date-time")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try: parsed = datetime.fromisoformat(normalized)
    except ValueError as exc: raise ExecutionError(f"{field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExecutionError(f"{field} must include timezone")
    return parsed.isoformat()

def exact(record: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    if not isinstance(record, dict): raise ExecutionError("record must be an object")
    missing=required-set(record); unknown=set(record)-allowed
    if missing or unknown: raise ExecutionError(f"invalid fields; missing={sorted(missing)} unknown={sorted(unknown)}")

def identifier(value: Any, kind: str) -> str:
    if not isinstance(value, str) or not ID_PATTERNS[kind].fullmatch(value): raise ExecutionError(f"invalid {kind} id")
    return value

def finite_number(value: Any, field: str, minimum: float=0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not isfinite(float(value)) or float(value)<minimum:
        raise ExecutionError(f"{field} must be finite and >= {minimum}")
    return float(value)

def validate_envelope(raw: dict[str, Any]) -> dict[str, Any]:
    keys={"id","experiment_id","action_type","adapter","mode","idempotency_key","target_keys","content_hash","payload","batch_size","canary_for_id","maximum_spend_usd","currency","rate_limit_per_hour","rollback_plan","created_at","sensitivity"}
    required=keys-{"canary_for_id"}
    exact(raw,keys,required)
    action=raw["action_type"]
    if action not in ACTION_TO_ADAPTER: raise ExecutionError("unsupported action_type")
    adapter=raw["adapter"]
    if adapter!=ACTION_TO_ADAPTER[action] or adapter not in ADAPTERS: raise ExecutionError("adapter does not match action_type")
    if raw["mode"] not in MODES: raise ExecutionError("only SIMULATOR mode is supported")
    if not isinstance(raw["experiment_id"],str) or not raw["experiment_id"].startswith("EXP-"): raise ExecutionError("experiment_id is required")
    if not isinstance(raw["idempotency_key"],str) or not IDEMPOTENCY_RE.fullmatch(raw["idempotency_key"]): raise ExecutionError("invalid idempotency_key")
    targets=raw["target_keys"]
    if not isinstance(targets,list) or not targets or any(not isinstance(x,str) or not TARGET_RE.fullmatch(x) for x in targets): raise ExecutionError("target_keys must be pseudonymous TGT identifiers")
    if len(targets)!=len(set(targets)): raise ExecutionError("target_keys contain duplicates")
    batch=raw["batch_size"]
    if isinstance(batch,bool) or not isinstance(batch,int) or batch!=len(targets): raise ExecutionError("batch_size must equal target_keys length")
    if batch>ADAPTERS[adapter]["max_records"]: raise ExecutionError("batch_size exceeds adapter maximum")
    canary=raw.get("canary_for_id")
    if batch==1 and canary is not None: raise ExecutionError("one-record canary cannot reference another canary")
    if batch>1 and (not isinstance(canary,str) or not ID_PATTERNS["envelope"].fullmatch(canary)): raise ExecutionError("bounded batch requires canary_for_id")
    if not isinstance(raw["content_hash"],str) or not HASH_RE.fullmatch(raw["content_hash"]): raise ExecutionError("invalid content_hash")
    if not isinstance(raw["payload"],dict): raise ExecutionError("payload must be an object")
    if any(k.lower() in {"email","phone","name","address","token","secret"} for k in raw["payload"]): raise ExecutionError("payload contains direct identifier or secret field")
    spend=finite_number(raw["maximum_spend_usd"],"maximum_spend_usd")
    if spend!=0: raise ExecutionError("Phase 4 simulator cannot authorize spending")
    if raw["currency"]!="USD": raise ExecutionError("currency must be USD")
    rate=raw["rate_limit_per_hour"]
    if isinstance(rate,bool) or not isinstance(rate,int) or not 1<=rate<=ADAPTERS[adapter]["max_per_hour"]: raise ExecutionError("invalid rate_limit_per_hour")
    rollback=raw["rollback_plan"]
    exact(rollback,{"required","strategy","timeout_seconds"},{"required","strategy","timeout_seconds"})
    if not isinstance(rollback["required"],bool) or not isinstance(rollback["strategy"],str) or len(rollback["strategy"])<3: raise ExecutionError("invalid rollback_plan")
    if isinstance(rollback["timeout_seconds"],bool) or not isinstance(rollback["timeout_seconds"],int) or not 1<=rollback["timeout_seconds"]<=3600: raise ExecutionError("invalid rollback timeout")
    if ADAPTERS[adapter]["reversible"] and not rollback["required"]: raise ExecutionError("reversible adapters require a rollback plan")
    if not ADAPTERS[adapter]["reversible"] and rollback["required"]: raise ExecutionError("irreversible adapters cannot promise rollback")
    if raw["sensitivity"] not in {"INTERNAL","CONFIDENTIAL"}: raise ExecutionError("invalid sensitivity")
    return {**raw,"canary_for_id":canary,"maximum_spend_usd":spend,"created_at":parse_time(raw["created_at"],"created_at")}

def validate_result(raw: dict[str,Any]) -> dict[str,Any]:
    keys={"id","envelope_id","outcome","affected_records","spend_usd","external_reference","reversible","completed_at","details"}
    exact(raw,keys,keys)
    if raw["outcome"] not in OUTCOMES: raise ExecutionError("invalid outcome")
    if isinstance(raw["affected_records"],bool) or not isinstance(raw["affected_records"],int) or raw["affected_records"]<0: raise ExecutionError("invalid affected_records")
    if finite_number(raw["spend_usd"],"spend_usd")!=0: raise ExecutionError("simulator result cannot spend")
    if raw["external_reference"] is not None: raise ExecutionError("simulator cannot return external reference")
    if not isinstance(raw["reversible"],bool) or not isinstance(raw["details"],dict): raise ExecutionError("invalid result fields")
    return {**raw,"completed_at":parse_time(raw["completed_at"],"completed_at"),"spend_usd":0.0}

def validate_rollback(raw:dict[str,Any])->dict[str,Any]:
    keys={"id","envelope_id","result_id","outcome","occurred_at","details"}; exact(raw,keys,keys)
    if raw["outcome"] not in ROLLBACK_OUTCOMES: raise ExecutionError("invalid rollback outcome")
    if not isinstance(raw["details"],dict): raise ExecutionError("rollback details must be an object")
    return {**raw,"occurred_at":parse_time(raw["occurred_at"],"occurred_at")}
