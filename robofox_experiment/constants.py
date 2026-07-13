"""Constants for the Phase 3 experiment operating system."""
from __future__ import annotations
import re

SCHEMA_VERSION = 1
STATES = {"DRAFT", "REVIEWED", "APPROVED", "LIVE", "PAUSED", "COMPLETED", "KILLED"}
TERMINAL_STATES = {"COMPLETED", "KILLED"}
ACTIVE_STATES = STATES - TERMINAL_STATES
GENERIC_TRANSITIONS = {
    ("DRAFT", "REVIEWED"),
    ("REVIEWED", "APPROVED"),
    ("APPROVED", "LIVE"),
    ("LIVE", "PAUSED"),
    ("PAUSED", "LIVE"),
}
OUTCOME_TO_STATE = {
    "SUCCESS": "COMPLETED",
    "FAILED": "KILLED",
    "SAFETY_STOP": "KILLED",
    "CANCELLED": "KILLED",
}
CHANGE_DIMENSIONS = {
    "SEGMENT", "OFFER", "MESSAGE", "PRICE", "CHANNEL",
    "PRODUCT", "ONBOARDING", "SALES_PROCESS",
}
OPERATORS = {"GTE", "LTE", "GT", "LT", "EQ"}
CRITERION_STATUSES = {"MET", "NOT_MET", "INSUFFICIENT_DATA"}
SENSITIVITY = {"INTERNAL", "CONFIDENTIAL"}
ACTION_TO_KIND = {
    "register_experiment_definition": "experiment",
    "record_experiment_transition": "transition",
    "record_experiment_execution": "execution",
    "record_experiment_observation": "observation",
    "finalize_experiment": "outcome",
}
ACTION_MAX_RECORDS = {
    "register_experiment_definition": 1,
    "record_experiment_transition": 1,
    "record_experiment_execution": 1,
    "record_experiment_observation": 1,
    "finalize_experiment": 2,
}
ID_PATTERNS = {
    "experiment": re.compile(r"^EXP-[A-Z0-9-]{6,80}$"),
    "transition": re.compile(r"^XTR-[A-Z0-9-]{6,80}$"),
    "execution": re.compile(r"^EXE-[A-Z0-9-]{6,80}$"),
    "observation": re.compile(r"^OBS-[A-Z0-9-]{6,80}$"),
    "outcome": re.compile(r"^OUT-[A-Z0-9-]{6,80}$"),
}
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
