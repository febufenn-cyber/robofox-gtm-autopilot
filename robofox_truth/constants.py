"""Constants for the Robofox Phase 1 truth layer."""
from __future__ import annotations

import re
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_ROOT = ENGINE_ROOT / "truth" / "migrations"
DEFAULT_WORKSPACE = "~/private/robofox-gtm-workspace"
DB_RELATIVE_PATH = Path("truth") / "robofox_truth.sqlite3"
SCHEMA_VERSION = 2

SOURCE_TYPES = {
    "CUSTOMER_INTERVIEW", "CRM", "META_ADS", "CALL_TEST", "PRODUCT_TELEMETRY",
    "FOUNDER_OBSERVATION", "DOCUMENT", "PUBLIC_BENCHMARK", "OTHER",
}
EVIDENCE_STATES = {"VERIFIED", "OBSERVED", "INFERRED", "ASSUMED", "UNKNOWN", "PROHIBITED"}
CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
SENSITIVITY = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}
ASSUMPTION_STATUS = {"OPEN", "SUPPORTED", "REFUTED", "RETIRED"}
PRODUCT_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PREDICATE_RE = re.compile(r"^[a-z][a-z0-9_]{1,79}$")
ID_PATTERNS = {
    "source": re.compile(r"^SRC-[A-Z0-9-]{6,80}$"),
    "claim": re.compile(r"^CLM-[A-Z0-9-]{6,80}$"),
    "assumption": re.compile(r"^ASM-[A-Z0-9-]{6,80}$"),
    "metric": re.compile(r"^MET-[A-Z0-9-]{6,80}$"),
}

SOURCE_KEYS = {"id", "source_type", "external_reference", "captured_at", "observed_at", "sensitivity", "content_hash", "metadata"}
CLAIM_KEYS = {"id", "product", "subject", "predicate", "value", "unit", "evidence_state", "confidence", "source_ids", "captured_at", "observed_at", "valid_from", "valid_until", "max_age_days", "supersedes_id", "sensitivity", "notes"}
ASSUMPTION_KEYS = {"id", "product", "statement", "status", "confidence", "created_at", "review_by", "resolution_claim_ids", "supersedes_id", "sensitivity"}
METRIC_KEYS = {"id", "product", "metric", "value", "unit", "denominator", "sample_size", "segment", "experiment_id", "source_ids", "period_start", "period_end", "captured_at", "sensitivity"}
