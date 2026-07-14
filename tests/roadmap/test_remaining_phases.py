from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "verify_autonomous_build_plan", ROOT / "scripts/verify_autonomous_build_plan.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class RemainingPhasesPlanTests(unittest.TestCase):
    def test_contract_is_valid(self) -> None:
        self.assertEqual([], module.verify_contract(module.load_plan()))

    def test_phase_numbers_and_classification(self) -> None:
        plan = module.load_plan()
        self.assertEqual([4, 5, 6, 7, 8, 9], [p["phase"] for p in plan["phases"]])
        self.assertEqual(["core"] * 4 + ["advanced"] * 2, [p["classification"] for p in plan["phases"]])

    def test_real_world_actions_are_never_autonomous(self) -> None:
        plan = module.load_plan()
        denied = set(plan["never_autonomous_actions"])
        for action in ("send_email", "mutate_live_crm", "spend_money", "deploy_production", "weaken_constitution"):
            self.assertIn(action, denied)

    def test_phase_four_is_ready_after_phase_three(self) -> None:
        self.assertEqual([], module.verify_readiness(module.load_plan(), 4))

    def test_advanced_phase_requires_readiness_report(self) -> None:
        errors = module.verify_readiness(module.load_plan(), 8)
        self.assertTrue(any("DEFERRED" in error or "readiness file missing" in error for error in errors))

    def test_build_command_is_stable(self) -> None:
        self.assertEqual("build", module.load_plan()["build_command"])


if __name__ == "__main__":
    unittest.main()
