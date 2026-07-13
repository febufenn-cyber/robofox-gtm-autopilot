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

from robofox_truth import (  # noqa: E402
    TruthStoreError,
    connect,
    initialize,
    insert_assumption,
    insert_claim,
    insert_metric,
    insert_source,
    resolve_workspace,
    status,
)
from robofox_truth.constants import SCHEMA_VERSION  # noqa: E402


def load_record(path: str) -> dict:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TruthStoreError(f"invalid JSON: {exc}") from exc
    if not isinstance(record, dict):
        raise TruthStoreError("record must be a JSON object")
    return record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help="private workspace path; defaults to ROBOFOX_GTM_WORKSPACE")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="initialize the private SQLite ledger")
    for command in ("add-source", "add-claim", "add-assumption", "add-metric"):
        child = subparsers.add_parser(command)
        child.add_argument("record", help="JSON record file or - for stdin")
    subparsers.add_parser("status", help="show schema version and record counts")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        workspace = resolve_workspace(args.workspace, create=args.command == "init")
        if args.command == "init":
            path = initialize(workspace)
            print(json.dumps({"initialized": str(path), "schema_version": SCHEMA_VERSION}, indent=2))
            return 0
        raw = load_record(args.record) if hasattr(args, "record") else None
        with connect(workspace) as connection:
            if args.command == "add-source":
                inserted = insert_source(connection, raw)
            elif args.command == "add-claim":
                inserted = insert_claim(connection, raw)
            elif args.command == "add-assumption":
                inserted = insert_assumption(connection, raw)
            elif args.command == "add-metric":
                inserted = insert_metric(connection, raw)
            elif args.command == "status":
                print(json.dumps(status(connection), indent=2, sort_keys=True))
                return 0
            else:  # pragma: no cover
                parser.error("unknown command")
        print(json.dumps({"inserted": inserted}, indent=2))
        return 0
    except (TruthStoreError, OSError, sqlite3.IntegrityError) as exc:
        print(f"TRUTH STORE: FAIL\n- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
