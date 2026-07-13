#!/usr/bin/env python3
"""Create a private Robofox GTM workspace without lifting its kill switch."""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth import TruthStoreError, resolve_workspace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=os.getenv("ROBOFOX_GTM_WORKSPACE", "~/private/robofox-gtm-workspace"))
    args = parser.parse_args()
    try:
        root = resolve_workspace(args.path, create=True)
    except TruthStoreError as exc:
        raise SystemExit(str(exc)) from exc

    try:
        root.chmod(0o700)
    except OSError:
        pass

    for directory in (
        "products", "markets", "customers", "evidence", "experiments", "decisions",
        "outcomes", "snapshots", "drafts", "audit", "truth", "imports", "quarantine",
        "approvals/pending", "approvals/approved", "approvals/rejected",
    ):
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        try:
            target.chmod(0o700)
        except OSError:
            pass
    (root / ".gitignore").write_text(
        ".env\nsecrets/\ncredentials/\n*.log\ntruth/*.sqlite*\nimports/\nquarantine/\napprovals/\n",
        encoding="utf-8",
    )
    workspace_file = root / "workspace.json"
    if workspace_file.exists():
        workspace = json.loads(workspace_file.read_text(encoding="utf-8"))
    else:
        workspace = {
            "workspace_id": "WS-" + secrets.token_hex(8).upper(),
            "classification": "INTERNAL",
            "public_repo": False,
            "timezone": "Asia/Kolkata",
            "external_execution": False,
            "customer_identifiers_enabled": False,
            "truth_layer": {
                "schema_version": 2,
                "append_only": True,
                "database": "truth/robofox_truth.sqlite3",
                "restricted_values_in_snapshots": False
            }
        }
        workspace_file.write_text(json.dumps(workspace, indent=2) + "\n", encoding="utf-8")
        try:
            workspace_file.chmod(0o600)
        except OSError:
            pass

    state_file = root / "system-state.json"
    if not state_file.exists():
        state_file.write_text(json.dumps({
            "version": 1,
            "autonomy_level": "L1",
            "execution_enabled": False,
            "kill_switch": True,
            "timezone": "Asia/Kolkata",
            "workspace_mode": "private_external_path",
            "workspace_id": workspace["workspace_id"],
            "disabled_capabilities": [
                "crm_write", "email_send", "whatsapp_send", "phone_call", "public_publish",
                "meta_campaign_write", "meta_budget_write", "contact_export"
            ]
        }, indent=2) + "\n", encoding="utf-8")
        try:
            state_file.chmod(0o600)
        except OSError:
            pass

    print(json.dumps({
        "workspace": str(root),
        "workspace_id": workspace["workspace_id"],
        "system_state": str(state_file),
        "kill_switch": True,
        "truth_database_initialized": False,
        "next": "Prepare and approve initialize_truth_ledger, deliberately lift only the private kill switch, then run truth_store.py init.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
