from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from truth_store import require_policy  # noqa: E402
from robofox_truth import (  # noqa: E402
    TruthStoreError, connect, create_approval, prepare_manifest, status,
)
from robofox_truth.approval import write_private_json  # noqa: E402
from robofox_truth.constants import SCHEMA_VERSION  # noqa: E402


class CliPolicyBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="robofox-cli-policy-")
        self.workspace = Path(self.temp.name) / "workspace"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/bootstrap_private_workspace.py"), str(self.workspace)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.output = json.loads(result.stdout)
        self.workspace_data = json.loads((self.workspace / "workspace.json").read_text())
        self.state_path = self.workspace / "system-state.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_bootstrap_keeps_kill_switch_active_and_does_not_initialize_database(self) -> None:
        state = json.loads(self.state_path.read_text())
        self.assertTrue(state["kill_switch"])
        self.assertEqual(self.workspace_data["workspace_id"], state["workspace_id"])
        self.assertFalse((self.workspace / "truth/robofox_truth.sqlite3").exists())
        self.assertFalse(self.output["truth_database_initialized"])

    def test_state_file_must_be_inside_workspace(self) -> None:
        outside = Path(self.temp.name) / "outside-state.json"
        outside.write_text(self.state_path.read_text())
        with self.assertRaisesRegex(TruthStoreError, "inside the private workspace"):
            require_policy(self.workspace, "record_truth_source", str(outside))

    def test_state_workspace_identity_must_match(self) -> None:
        state = json.loads(self.state_path.read_text())
        state["workspace_id"] = "WS-WRONG-IDENTITY"
        self.state_path.write_text(json.dumps(state))
        with self.assertRaisesRegex(TruthStoreError, "workspace_id does not match"):
            require_policy(self.workspace, "record_truth_source", str(self.state_path))

    def test_kill_switch_blocks_mutation_until_deliberately_lifted(self) -> None:
        with self.assertRaisesRegex(TruthStoreError, "KILL_SWITCH"):
            require_policy(self.workspace, "record_truth_source", str(self.state_path))
        state = json.loads(self.state_path.read_text())
        state["kill_switch"] = False
        self.state_path.write_text(json.dumps(state))
        require_policy(self.workspace, "record_truth_source", str(self.state_path))


    def test_cli_initialization_and_record_write_consume_separate_approvals(self) -> None:
        state = json.loads(self.state_path.read_text())
        state["kill_switch"] = False
        self.state_path.write_text(json.dumps(state))

        init_payload = {"schema_version": SCHEMA_VERSION}
        init_manifest = prepare_manifest(
            self.workspace, "initialize_truth_ledger", init_payload,
            requested_by="cli-test", task_id="TASK-CLI-INIT",
            created_at="2026-07-13T10:00:00+05:30",
        )
        init_approval = create_approval(
            init_manifest, approved_by="cli-founder",
            approved_at="2026-07-13T10:01:00+05:30", expires_minutes=1440,
        )
        # Use a current validity window for subprocess validation.
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        init_manifest["created_at"] = now
        init_approval = create_approval(init_manifest, approved_by="cli-founder", approved_at=now, expires_minutes=30)
        init_manifest_path = self.workspace / "approvals/pending/init.manifest.json"
        init_approval_path = self.workspace / "approvals/approved/init.approval.json"
        write_private_json(init_manifest_path, init_manifest)
        write_private_json(init_approval_path, init_approval)
        subprocess.run([
            sys.executable, str(ROOT / "scripts/truth_store.py"),
            "--workspace", str(self.workspace), "init",
            "--manifest", str(init_manifest_path), "--approval", str(init_approval_path),
            "--state", str(self.state_path),
        ], check=True, capture_output=True, text=True)

        source = {
            "id": "SRC-CLI-POLICY-01",
            "source_type": "FOUNDER_OBSERVATION",
            "captured_at": now,
            "sensitivity": "INTERNAL",
            "content_hash": "sha256:" + "e" * 64,
            "metadata": {"synthetic": True},
        }
        source_path = self.workspace / "source.json"
        source_path.write_text(json.dumps(source))
        manifest = prepare_manifest(
            self.workspace, "record_truth_source", source,
            requested_by="cli-test", task_id="TASK-CLI-SOURCE", created_at=now,
        )
        approval = create_approval(manifest, approved_by="cli-founder", approved_at=now, expires_minutes=30)
        manifest_path = self.workspace / "approvals/pending/source.manifest.json"
        approval_path = self.workspace / "approvals/approved/source.approval.json"
        write_private_json(manifest_path, manifest)
        write_private_json(approval_path, approval)
        subprocess.run([
            sys.executable, str(ROOT / "scripts/truth_store.py"),
            "--workspace", str(self.workspace), "add-source", str(source_path),
            "--manifest", str(manifest_path), "--approval", str(approval_path),
            "--state", str(self.state_path),
        ], check=True, capture_output=True, text=True)

        with connect(self.workspace) as connection:
            snapshot = status(connection)
        self.assertEqual(1, snapshot["counts"]["sources"])
        self.assertEqual(2, snapshot["counts"]["approval_consumptions"])

    def test_agent_approval_action_is_registry_forbidden(self) -> None:
        registry = json.loads((ROOT / "policies/action-registry.yaml").read_text())
        action = registry["actions"]["approve_truth_action"]
        self.assertFalse(action["enabled"])
        self.assertEqual("forbidden", action["approval"])


if __name__ == "__main__":
    unittest.main()
