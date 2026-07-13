#!/usr/bin/env python3
"""Create a local private workspace outside the public engine."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from truth_store import TruthStoreError, initialize, resolve_workspace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=os.getenv("ROBOFOX_GTM_WORKSPACE", "~/private/robofox-gtm-workspace"))
    args = parser.parse_args()
    try:
        root = resolve_workspace(args.path, create=True)
    except TruthStoreError as exc:
        raise SystemExit(str(exc)) from exc

    for directory in (
        "products", "markets", "customers", "evidence", "experiments", "decisions",
        "outcomes", "snapshots", "drafts", "audit", "truth", "imports", "quarantine",
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(
        ".env\nsecrets/\ncredentials/\n*.log\ntruth/*.sqlite*\nimports/\nquarantine/\n",
        encoding="utf-8",
    )
    (root / "workspace.json").write_text(json.dumps({
        "classification": "INTERNAL",
        "public_repo": False,
        "timezone": "Asia/Kolkata",
        "external_execution": False,
        "customer_identifiers_enabled": False,
        "truth_layer": {
            "schema_version": 1,
            "append_only": True,
            "database": "truth/robofox_truth.sqlite3",
            "restricted_values_in_snapshots": False
        }
    }, indent=2) + "\n", encoding="utf-8")
    database = initialize(root)
    print(json.dumps({"workspace": str(root), "truth_database": str(database)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
