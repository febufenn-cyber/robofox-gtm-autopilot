#!/usr/bin/env python3
"""Zero-dependency Phase 0 policy gate for Robofox GTM Autopilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
LEVELS = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
CONTACT_RESTRICTION = {
    "opted_in": 0, "legitimate_existing_relationship": 1, "not_requested": 2,
    "unknown": 3, "expired": 4, "requires_manual_review": 5,
    "opted_out": 6, "do_not_contact": 7,
}
BLOCKED_DIR_NAMES = {
    "workspace", "private", "customers", "exports", "hubspot-data", "meta-data",
    "call-recordings", "transcripts", "secrets", "credentials", "tokens"
}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".csv", ".xlsx", ".sqlite", ".sqlite3", ".db"}
TEXT_SUFFIXES = {"", ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".sh", ".toml", ".xml", ".gitignore", ".example"}
PII_DIRECTORIES = {"context", "plans", "reviews", "drafts", "approvals"}
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{30,}\b"),
    "openai-style-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "hubspot-private-token": re.compile(r"\bpat-[a-z0-9-]{20,}\b", re.I),
    "aws-access-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str
    reason: str


def load_json_yaml(path: Path) -> dict:
    """Load JSON-compatible YAML using the Python standard library."""
    return json.loads(path.read_text(encoding="utf-8"))


def system_state(path: Path | None = None) -> dict:
    state = load_json_yaml(path or ROOT / "config/system-state.example.yaml")
    env_level = os.getenv("ROBOFOX_GTM_AUTONOMY")
    if env_level:
        state["autonomy_level"] = env_level
    if os.getenv("ROBOFOX_GTM_KILL_SWITCH", "").strip().lower() in {"1", "true", "yes", "on"}:
        state["kill_switch"] = True
    return state


def authorize(action_type: str, *, approval: bool = False, state_path: Path | None = None) -> Decision:
    registry = load_json_yaml(ROOT / "policies/action-registry.yaml")
    action = registry.get("actions", {}).get(action_type)
    if action is None:
        return Decision(False, "UNKNOWN_ACTION", "Action is not registered; default deny applies.")

    state = system_state(state_path)
    if state.get("kill_switch", True):
        return Decision(False, "KILL_SWITCH", "Kill switch is active.")
    if not action.get("enabled", False):
        return Decision(False, "ACTION_DISABLED", "Action is disabled by policy.")
    if action.get("external") and not state.get("execution_enabled", False):
        return Decision(False, "EXECUTION_DISABLED", "External execution is disabled.")

    current = state.get("autonomy_level", "L1")
    required = action.get("minimum_level", "L4")
    if current not in LEVELS or required not in LEVELS:
        return Decision(False, "INVALID_LEVEL", "Autonomy level is invalid.")
    if LEVELS[current] < LEVELS[required]:
        return Decision(False, "AUTONOMY_TOO_LOW", f"{action_type} requires {required}; current level is {current}.")

    approval_mode = action.get("approval", "exact")
    if approval_mode == "forbidden":
        return Decision(False, "FORBIDDEN", "Policy permanently forbids this action.")
    if approval_mode == "exact" and not approval:
        return Decision(False, "APPROVAL_REQUIRED", "Exact action-bound approval is required.")
    return Decision(True, "ALLOW", "Action is registered and permitted by the current state.")


def most_restrictive_contact_status(statuses: Iterable[str]) -> str:
    values = list(statuses)
    if not values:
        return "unknown"
    invalid = [value for value in values if value not in CONTACT_RESTRICTION]
    if invalid:
        return "requires_manual_review"
    return max(values, key=CONTACT_RESTRICTION.__getitem__)


def canonical_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def tracked_files(root: Path = ROOT) -> list[Path]:
    try:
        output = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"], stderr=subprocess.DEVNULL)
        return [root / p.decode("utf-8") for p in output.split(b"\0") if p]
    except Exception:
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def is_text_candidate(path: Path) -> bool:
    if path.name in {".gitignore", ".env.example", "CLAUDE.md"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= 2_000_000


def scan_public_repo(root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    for path in tracked_files(root):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in BLOCKED_DIR_NAMES for part in relative.parts):
            findings.append(f"blocked private-data path: {relative}")
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            findings.append(f"blocked sensitive/export file type: {relative}")
        if not path.exists() or not is_text_candidate(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"possible {label}: {relative}")
        if relative.parts and relative.parts[0] in PII_DIRECTORIES:
            if EMAIL_PATTERN.search(text):
                findings.append(f"possible personal email in operating content: {relative}")
            if PHONE_PATTERN.search(text):
                findings.append(f"possible Indian phone number in operating content: {relative}")
    return sorted(set(findings))


def validate_schema_documents(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in sorted((root / "schemas").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON schema {path.relative_to(root)}: {exc}")
            continue
        if data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"unexpected schema draft: {path.relative_to(root)}")
        if data.get("type") != "object" or data.get("additionalProperties") is not False:
            errors.append(f"schema must be closed object: {path.relative_to(root)}")
    return errors


def validate_registry(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    registry = load_json_yaml(root / "policies/action-registry.yaml")
    if registry.get("default_decision") != "deny":
        errors.append("action registry must default to deny")
    for name, action in registry.get("actions", {}).items():
        for field in ("risk", "minimum_level", "approval", "enabled", "external", "reversible"):
            if field not in action:
                errors.append(f"action {name} missing {field}")
        if action.get("minimum_level") not in LEVELS:
            errors.append(f"action {name} has invalid autonomy level")
        if action.get("external") and action.get("enabled"):
            errors.append(f"external action unexpectedly enabled: {name}")
    return errors


def check_submodule_lock(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    lock = load_json_yaml(root / "vendor/approved-sources.lock")
    approved = lock["sources"]["agent-gtm-skills"]
    if approved.get("auto_update") is not False:
        errors.append("upstream source must not auto-update")
    gitmodules = root / ".gitmodules"
    if gitmodules.exists() and approved["repository"] not in gitmodules.read_text(encoding="utf-8"):
        errors.append(".gitmodules URL does not match approved source")
    try:
        output = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-s", "vendor/agent-gtm-skills"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if output:
            mode, sha, *_ = output.split()
            if mode == "160000" and sha != approved["approved_commit"]:
                errors.append(f"submodule moved: {sha} != {approved['approved_commit']}")
    except Exception:
        pass
    return errors


def validate_required_files(root: Path = ROOT) -> list[str]:
    required = [
        "CLAUDE.md", ".env.example", "policies/constitution.md", "policies/autonomy-levels.md",
        "policies/action-registry.yaml", "policies/data-classification.md", "policies/evidence-policy.md",
        "policies/approval-policy.md", "policies/external-action-policy.md", "policies/prompt-injection-policy.md",
        "policies/claims-policy.md", "policies/contactability-policy.md", "policies/retention-policy.md", "policies/incident-response.md",
        "policies/supply-chain-policy.md", "config/system-state.example.yaml", "config/tool-profiles.example.yaml",
        "config/workspace.example.yaml", "vendor/approved-sources.lock",
    ]
    return [f"missing required Phase 0 file: {name}" for name in required if not (root / name).exists()]


def verify(root: Path = ROOT) -> list[str]:
    errors = []
    errors.extend(validate_required_files(root))
    errors.extend(validate_schema_documents(root))
    errors.extend(validate_registry(root))
    errors.extend(check_submodule_lock(root))
    errors.extend(scan_public_repo(root))

    state = load_json_yaml(root / "config/system-state.example.yaml")
    if state.get("autonomy_level") != "L1":
        errors.append("safe default autonomy must be L1")
    if state.get("execution_enabled") is not False:
        errors.append("execution must default to disabled")
    if state.get("kill_switch") is not True:
        errors.append("kill switch must default to active")

    ignore = (root / ".gitignore").read_text(encoding="utf-8")
    for marker in ("workspace/", "private/", "*.pem", "*.csv", "*.sqlite"):
        if marker not in ignore:
            errors.append(f".gitignore missing Phase 0 marker: {marker}")
    return sorted(set(errors))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    auth = sub.add_parser("authorize", help="Evaluate one registered action")
    auth.add_argument("action")
    auth.add_argument("--approval", action="store_true")
    sub.add_parser("scan", help="Scan the public repository for prohibited material")
    sub.add_parser("verify", help="Run all Phase 0 checks")
    hash_parser = sub.add_parser("hash", help="Hash canonical JSON from stdin")
    hash_parser.add_argument("--file", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "authorize":
        decision = authorize(args.action, approval=args.approval)
        print(json.dumps(decision.__dict__, indent=2))
        return 0 if decision.allowed else 2
    if args.command == "scan":
        findings = scan_public_repo()
        if findings:
            print("PHASE0 SCAN: FAIL")
            for finding in findings:
                print(f"- {finding}")
            return 1
        print("PHASE0 SCAN: PASS")
        return 0
    if args.command == "verify":
        errors = verify()
        if errors:
            print("PHASE0 VERIFY: FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("PHASE0 VERIFY: PASS")
        print("- public/private boundary enforced")
        print("- L1 advisory default and active kill switch")
        print("- unknown actions default-denied")
        print("- external and financial actions disabled")
        print("- schemas, source lock, and public-repo scan valid")
        return 0
    if args.command == "hash":
        raw = args.file.read_text(encoding="utf-8") if args.file else sys.stdin.read()
        print(canonical_hash(json.loads(raw)))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
