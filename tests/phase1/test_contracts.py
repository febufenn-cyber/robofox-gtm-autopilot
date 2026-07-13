from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_phase1_contracts import verify  # noqa: E402


class Phase1ContractTests(unittest.TestCase):
    def test_repository_contracts_pass(self) -> None:
        self.assertEqual([], verify(ROOT))

    def test_claim_schema_distinguishes_unknown_from_zero(self) -> None:
        schema = json.loads((ROOT / "schemas/claim-record.schema.json").read_text())
        self.assertIn("UNKNOWN", schema["properties"]["evidence_state"]["enum"])
        self.assertEqual({}, schema["properties"]["value"])

    def test_snapshots_are_derived_and_traceable(self) -> None:
        schema = json.loads((ROOT / "schemas/position-snapshot.schema.json").read_text())
        self.assertIn("input_record_ids", schema["required"])
        self.assertIn("conflicts", schema["required"])
        self.assertIn("stale_claim_ids", schema["required"])

    def test_position_dimensions_are_unique_and_dated(self) -> None:
        data = json.loads((ROOT / "config/position-dimensions.json").read_text())
        keys = [item["key"] for item in data["dimensions"]]
        self.assertEqual(10, len(keys))
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(item["max_age_days"] > 0 for item in data["dimensions"]))
        self.assertTrue(all(item["subject"] == "commercial-position" for item in data["dimensions"]))

    def test_restricted_is_a_first_class_sensitivity(self) -> None:
        for filename in ("source-record.schema.json", "claim-record.schema.json", "assumption-record.schema.json", "metric-record.schema.json"):
            schema = json.loads((ROOT / "schemas" / filename).read_text())
            self.assertIn("RESTRICTED", schema["properties"]["sensitivity"]["enum"])


if __name__ == "__main__":
    unittest.main()
