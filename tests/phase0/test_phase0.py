#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from phase0_policy import authorize, canonical_hash, load_json_yaml, most_restrictive_contact_status, scan_public_repo, verify


class Phase0PolicyTests(unittest.TestCase):
    def safe_state(self) -> dict:
        return {
            "version": 1,
            "autonomy_level": "L1",
            "execution_enabled": False,
            "kill_switch": False,
            "disabled_capabilities": [],
        }

    def write_state(self, directory: Path, state: dict) -> Path:
        path = directory / "state.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        return path

    def test_repository_verifies(self):
        self.assertEqual(verify(ROOT), [])

    def test_unknown_action_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_state(Path(tmp), self.safe_state())
            decision = authorize("invented_action", state_path=path)
            self.assertFalse(decision.allowed)
            self.assertEqual(decision.code, "UNKNOWN_ACTION")

    def test_kill_switch_blocks_even_safe_action(self):
        decision = authorize("generate_channel_plan")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "KILL_SWITCH")

    def test_l1_allows_advice_when_kill_switch_is_deliberately_lifted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_state(Path(tmp), self.safe_state())
            with patch.dict(os.environ, {"ROBOFOX_GTM_KILL_SWITCH": "0"}, clear=False):
                decision = authorize("generate_channel_plan", state_path=path)
            self.assertTrue(decision.allowed)

    def test_external_send_remains_disabled_with_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self.safe_state()
            state["autonomy_level"] = "L4"
            state["execution_enabled"] = True
            path = self.write_state(Path(tmp), state)
            decision = authorize("send_email", approval=True, state_path=path)
            self.assertFalse(decision.allowed)
            self.assertEqual(decision.code, "ACTION_DISABLED")

    def test_contact_export_is_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = self.safe_state()
            state["autonomy_level"] = "L4"
            state["execution_enabled"] = True
            path = self.write_state(Path(tmp), state)
            decision = authorize("export_contacts", approval=True, state_path=path)
            self.assertFalse(decision.allowed)

    def test_canonical_hash_is_order_independent(self):
        self.assertEqual(canonical_hash({"a": 1, "b": 2}), canonical_hash({"b": 2, "a": 1}))

    def test_scanner_blocks_private_paths_and_pii_in_operating_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace").mkdir()
            (root / "workspace/customer.txt").write_text("private", encoding="utf-8")
            (root / "plans").mkdir()
            (root / "plans/live.md").write_text("Contact person@example.org", encoding="utf-8")
            findings = scan_public_repo(root)
            self.assertTrue(any("blocked private-data path" in item for item in findings))
            self.assertTrue(any("personal email" in item for item in findings))

    def test_scanner_skips_initialized_gitlink_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gitlink = root / "vendor/agent-gtm-skills"
            gitlink.mkdir(parents=True)
            with patch("phase0_policy.tracked_files", return_value=[gitlink]):
                self.assertEqual(scan_public_repo(root), [])

    def test_contactability_uses_most_restrictive_status(self):
        self.assertEqual(
            most_restrictive_contact_status(["opted_in", "opted_out", "unknown"]),
            "opted_out",
        )
        self.assertEqual(most_restrictive_contact_status([]), "unknown")

    def test_action_registry_defaults_to_deny(self):
        registry = load_json_yaml(ROOT / "policies/action-registry.yaml")
        self.assertEqual(registry["default_decision"], "deny")


if __name__ == "__main__":
    unittest.main()
