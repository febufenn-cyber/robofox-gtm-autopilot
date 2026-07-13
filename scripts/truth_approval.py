#!/usr/bin/env python3
"""Prepare and explicitly approve hash-bound private truth-ledger actions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth import (  # noqa: E402
    TruthStoreError,
    canonical_hash,
    create_approval,
    prepare_manifest,
    resolve_workspace,
)
from robofox_truth.approval import load_json_object, write_private_json  # noqa: E402
from robofox_truth.constants import SCHEMA_VERSION  # noqa: E402

ACTIONS = (
    "initialize_truth_ledger",
    "record_truth_source",
    "record_truth_claim",
    "record_truth_assumption",
    "record_truth_metric",
)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--workspace", help="private workspace path")
    sub = root.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="create an exact action manifest")
    prepare.add_argument("action_type", choices=ACTIONS)
    prepare.add_argument("--record", help="JSON record; omit only for initialize_truth_ledger")
    prepare.add_argument("--requested-by", required=True)
    prepare.add_argument("--task-id", required=True)
    prepare.add_argument("--experiment-id")

    approve = sub.add_parser("approve", help="human-interactively approve one manifest")
    approve.add_argument("manifest")
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--expires-minutes", type=int, default=30)
    return root


def payload_for(action_type: str, record_path: str | None) -> dict:
    if action_type == "initialize_truth_ledger":
        if record_path is not None:
            raise TruthStoreError("initialize_truth_ledger does not accept --record")
        return {"schema_version": SCHEMA_VERSION}
    if record_path is None:
        raise TruthStoreError(f"{action_type} requires --record")
    return load_json_object(record_path)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        workspace = resolve_workspace(args.workspace)
        if args.command == "prepare":
            payload = payload_for(args.action_type, args.record)
            manifest = prepare_manifest(
                workspace,
                args.action_type,
                payload,
                requested_by=args.requested_by,
                task_id=args.task_id,
                experiment_id=args.experiment_id,
            )
            path = workspace / "approvals" / "pending" / f"{manifest['action_id']}.manifest.json"
            write_private_json(path, manifest)
            print(json.dumps({"manifest": str(path), "manifest_hash": canonical_hash(manifest)}, indent=2))
            return 0

        manifest = load_json_object(args.manifest)
        if not sys.stdin.isatty():
            raise TruthStoreError("approval requires an interactive founder-controlled terminal")
        phrase = f"APPROVE {manifest.get('action_id')} {manifest.get('payload_hash')}"
        print(json.dumps({
            "action_type": manifest.get("action_type"),
            "scope": manifest.get("scope"),
            "payload_hash": manifest.get("payload_hash"),
            "manifest_hash": canonical_hash(manifest),
            "expires_minutes": args.expires_minutes,
        }, indent=2))
        typed = input(f"Type exactly:\n{phrase}\n> ")
        if typed != phrase:
            raise TruthStoreError("approval phrase did not match exactly")
        approval = create_approval(
            manifest,
            approved_by=args.approved_by,
            expires_minutes=args.expires_minutes,
        )
        path = workspace / "approvals" / "approved" / f"{approval['approval_id']}.approval.json"
        write_private_json(path, approval)
        print(json.dumps({"approval": str(path), "expires_at": approval["expires_at"]}, indent=2))
        return 0
    except (TruthStoreError, OSError) as exc:
        print(f"TRUTH APPROVAL: FAIL\n- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
