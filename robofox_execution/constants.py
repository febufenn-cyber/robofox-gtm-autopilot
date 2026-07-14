"""Constants for the Phase 4 controlled execution gateway."""
from __future__ import annotations
import re

SCHEMA_VERSION = 1
MODES = {"SIMULATOR"}
OUTCOMES = {"SUCCESS", "PARTIAL", "FAILURE", "AMBIGUOUS"}
ROLLBACK_OUTCOMES = {"ROLLED_BACK", "ROLLBACK_FAILED"}
ACTION_TO_ADAPTER = {
    "PREPARE_CRM_TASK": "internal.crm_task",
    "SEND_EMAIL": "email",
    "SEND_WHATSAPP": "whatsapp",
    "PLACE_PHONE_CALL": "phone",
    "PUBLISH_CONTENT": "publish",
    "CHANGE_META_CAMPAIGN": "meta_ads",
}
ADAPTERS = {
    "internal.crm_task": {"live_enabled": False, "reversible": True, "max_records": 10, "max_per_hour": 20},
    "email": {"live_enabled": False, "reversible": False, "max_records": 10, "max_per_hour": 10},
    "whatsapp": {"live_enabled": False, "reversible": False, "max_records": 10, "max_per_hour": 10},
    "phone": {"live_enabled": False, "reversible": False, "max_records": 1, "max_per_hour": 5},
    "publish": {"live_enabled": False, "reversible": True, "max_records": 1, "max_per_hour": 3},
    "meta_ads": {"live_enabled": False, "reversible": True, "max_records": 1, "max_per_hour": 3},
}
ID_PATTERNS = {
    "envelope": re.compile(r"^EXR-[A-Z0-9-]{6,80}$"),
    "attempt": re.compile(r"^XAT-[A-Z0-9-]{6,80}$"),
    "result": re.compile(r"^XRS-[A-Z0-9-]{6,80}$"),
    "rollback": re.compile(r"^XRB-[A-Z0-9-]{6,80}$"),
    "circuit": re.compile(r"^XCB-[A-Z0-9-]{6,80}$"),
}
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:-]{16,160}$")
TARGET_RE = re.compile(r"^TGT-[A-Z0-9-]{6,80}$")
