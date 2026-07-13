#!/usr/bin/env python3
"""CLI for the private, append-only Robofox SQLite truth ledger."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase0_policy import authorize  # noqa: E402
from robofox_truth import (  # noqa: E402
    TruthStoreError,
    approved_insert,
    connect,
    initialize,
    integrity_report,
    resolve_workspace,
    status,
    validate_approval,
)
from robofox_truth.approval import consume_approval, load_json_object  # noqa: E402
from robofox_truth.constants import SCHEMA_VERSION  # noqa: E402

COMMAND_ACTIONS = {
    "add-source": "record_truth_source",
    "add-claim": "record_truth_claim",
    "add-assumption": "record_truth_assumption",
    "add-metric": "record_truth_metric",
}


def load_record(path: str) -> dict:
    if path == "-":
        try:
            value = json.loads(sys.stdin.read())
        except json.JSONDecodeError as exc:
            raise TruthStoreError(f"invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise TruthStoreError("record must be a JSON object")
        return value
    return load_json_object(path)


def add_approval_args(child: argparse.ArgumentParser) -> None:
    child.add_argument("--manifest", required=True, help="exact action manifest JSON")
    child.add_argument("--approval", required=True, help="single-use exact approval JSON")
    child.add_argument("--state", required=True, help="private system-state JSON with kill switch deliberately lifted")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help="private workspace path; defaults to ROBOFOX_GTM_WORKSPACE")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="initialize or migrate the private SQLite ledger")
    add_approval_args(init)
    for command in COMMAND_ACTIONS:
        child = subparsers.add_parser(command)
        child.add_argument("record", help="JSON record file or - for stdin")
        add_approval_args(child)
    subparsers.add_parser("status", help="show schema version and record counts")
    subparsers.add_parser("integrity", help="verify SQLite, foreign keys, triggers, migrations, and record hashes")
    return parser


def require_policy(workspace: Path, action_type: str, state_path: str) -> None:
    resolved = Path(state_path).expanduser().resolve()
    try:
        resolved.relative_to(workspace.resolve())
    except ValueError as exc:
        raise TruthStoreError("system-state file must be inside the private workspace") from exc
    state = load_json_object(resolved)
    workspace_data = load_json_object(workspace / "workspace.json")
    if state.get("workspace_id") != workspace_data.get("workspace_id"):
        raise TruthStoreError("system-state workspace_id does not match workspace.json")
    decision = authorize(action_type, approval=True, state_path=resolved)
    if not decision.allowed:
        raise TruthStoreError(f"policy denied {action_type}: {decision.code}: {decision.reason}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        workspace = resolve_workspace(args.workspace)
        if args.command in {"status", "integrity"}:
            with connect(workspace) as connection:
                output = status(connection) if args.command == "status" else integrity_report(connection)
            print(json.dumps(output, indent=2, sort_keys=True))
            return 0 if output.get("ok", True) else 1

        action_type = "initialize_truth_ledger" if args.command == "init" else COMMAND_ACTIONS[args.command]
        require_policy(workspace, action_type, args.state)
        payload = {"schema_version": SCHEMA_VERSION} if args.command == "init" else load_record(args.record)
        manifest = load_json_object(args.manifest)
        approval = load_json_object(args.approval)

        if args.command == "init":
            decision = validate_approval(workspace, action_type, payload, manifest, approval)
            initialize(workspace)
            with connect(workspace) as connection:
                with connection:
                    consume_approval(connection, decision)
            print(json.dumps({"initialized": str(workspace), "schema_version": SCHEMA_VERSION}, indent=2))
            return 0

        with connect(workspace) as connection:
            inserted = approved_insert(connection, workspace, action_type, payload, manifest, approval)
        print(json.dumps({"inserted": inserted, "approval_id": approval["approval_id"]}, indent=2))
        return 0
    except (TruthStoreError, OSError, sqlite3.IntegrityError) as exc:
        print(f"TRUTH STORE: FAIL\n- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
