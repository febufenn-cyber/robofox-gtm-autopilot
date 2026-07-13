from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth import (  # noqa: E402
    TruthStoreError,
    build_snapshot,
    connect,
    initialize,
    insert_assumption,
    insert_claim,
    insert_source,
    render_markdown,
    resolve_workspace,
    write_snapshot,
)


class PositionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="robofox-position-test-")
        self.workspace = resolve_workspace(self.temp.name, create=True)
        initialize(self.workspace)
        self.connection_context = connect(self.workspace)
        self.connection = self.connection_context.__enter__()
        self.source_counter = 0
        self.claim_counter = 0
        self.assumption_counter = 0

    def tearDown(self) -> None:
        self.connection_context.__exit__(None, None, None)
        self.temp.cleanup()

    def add_source(self, *, source_type: str = "FOUNDER_OBSERVATION", sensitivity: str = "INTERNAL") -> str:
        self.source_counter += 1
        source_id = f"SRC-POS-{self.source_counter:04d}"
        insert_source(self.connection, {
            "id": source_id,
            "source_type": source_type,
            "captured_at": "2026-07-01T09:00:00+05:30",
            "sensitivity": sensitivity,
            "content_hash": "sha256:" + f"{self.source_counter:064x}",
            "metadata": {"synthetic": True},
        })
        return source_id

    def add_claim(
        self,
        predicate: str,
        value,
        *,
        source_type: str = "FOUNDER_OBSERVATION",
        evidence_state: str = "OBSERVED",
        confidence: str = "MEDIUM",
        captured_at: str = "2026-07-01T09:05:00+05:30",
        observed_at: str | None = None,
        valid_from: str | None = None,
        valid_until: str | None = None,
        max_age_days: int | None = None,
        supersedes_id: str | None = None,
        sensitivity: str = "INTERNAL",
        subject: str = "commercial-position",
        source_id: str | None = None,
    ) -> str:
        self.claim_counter += 1
        claim_id = f"CLM-POS-{self.claim_counter:04d}"
        source_ids: list[str] = []
        if evidence_state in {"VERIFIED", "OBSERVED", "INFERRED"}:
            source_ids = [source_id or self.add_source(source_type=source_type)]
        record = {
            "id": claim_id,
            "product": "voice-agents",
            "subject": subject,
            "predicate": predicate,
            "value": value,
            "evidence_state": evidence_state,
            "confidence": confidence,
            "source_ids": source_ids,
            "captured_at": captured_at,
            "sensitivity": sensitivity,
        }
        optional = {
            "observed_at": observed_at,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_age_days": max_age_days,
            "supersedes_id": supersedes_id,
        }
        record.update({key: item for key, item in optional.items() if item is not None})
        insert_claim(self.connection, record)
        return claim_id

    def add_assumption(
        self,
        *,
        status: str = "OPEN",
        created_at: str = "2026-07-01T09:00:00+05:30",
        review_by: str | None = None,
        supersedes_id: str | None = None,
        sensitivity: str = "INTERNAL",
    ) -> str:
        self.assumption_counter += 1
        assumption_id = f"ASM-POS-{self.assumption_counter:04d}"
        record = {
            "id": assumption_id,
            "product": "voice-agents",
            "statement": f"Synthetic assumption {self.assumption_counter}",
            "status": status,
            "confidence": "LOW",
            "created_at": created_at,
            "sensitivity": sensitivity,
        }
        if review_by is not None:
            record["review_by"] = review_by
        if supersedes_id is not None:
            record["supersedes_id"] = supersedes_id
        insert_assumption(self.connection, record)
        return assumption_id

    def snapshot(self, as_of: str = "2026-07-13T12:00:00+05:30") -> dict:
        return build_snapshot(
            self.connection,
            "voice-agents",
            as_of=as_of,
            generated_at="2026-07-13T12:01:00+05:30",
        )

    def test_empty_ledger_makes_all_dimensions_unknown(self) -> None:
        snapshot = self.snapshot()
        self.assertEqual(10, len(snapshot["unknown_dimensions"]))
        self.assertTrue(all(item["status"] == "UNKNOWN" for item in snapshot["dimensions"].values()))
        self.assertEqual([], snapshot["input_record_ids"])

    def test_observed_zero_is_not_missing_or_unknown(self) -> None:
        claim_id = self.add_claim("customer_access", 0, max_age_days=30)
        snapshot = self.snapshot(as_of="2026-07-02T12:00:00+05:30")
        dimension = snapshot["dimensions"]["customer_access"]
        self.assertEqual(0, dimension["value"])
        self.assertEqual("OBSERVED", dimension["status"])
        self.assertNotIn("customer_access", snapshot["unknown_dimensions"])
        self.assertIn(claim_id, snapshot["input_record_ids"])

    def test_default_dimension_age_marks_claim_stale(self) -> None:
        claim_id = self.add_claim("founder_capacity", "available")
        snapshot = self.snapshot()
        self.assertEqual("STALE", snapshot["dimensions"]["founder_capacity"]["status"])
        self.assertIn("maximum_age_exceeded", snapshot["dimensions"]["founder_capacity"]["stale_reasons"])
        self.assertIn(claim_id, snapshot["stale_claim_ids"])

    def test_valid_until_marks_claim_stale(self) -> None:
        self.add_claim(
            "delivery_readiness",
            "ready",
            valid_until="2026-07-02T09:00:00+05:30",
            max_age_days=365,
        )
        snapshot = self.snapshot()
        self.assertEqual("STALE", snapshot["dimensions"]["delivery_readiness"]["status"])
        self.assertIn("valid_until_passed", snapshot["dimensions"]["delivery_readiness"]["stale_reasons"])

    def test_two_current_values_block_dimension(self) -> None:
        first = self.add_claim("customer_trust", "weak", max_age_days=30)
        second = self.add_claim("customer_trust", "strong", max_age_days=30)
        snapshot = self.snapshot(as_of="2026-07-02T12:00:00+05:30")
        self.assertEqual("CONFLICTED", snapshot["dimensions"]["customer_trust"]["status"])
        self.assertTrue(snapshot["dimensions"]["customer_trust"]["value_withheld"])
        conflict = next(item for item in snapshot["conflicts"] if item["predicate"] == "customer_trust")
        self.assertEqual("UNRESOLVED", conflict["resolution"])
        self.assertTrue(conflict["blocks_dimension"])
        self.assertEqual({first, second}, set(conflict["claim_ids"]))

    def test_stale_disagreement_is_visible_but_does_not_block_fresh_value(self) -> None:
        old = self.add_claim("proof_strength", "none", max_age_days=1)
        fresh = self.add_claim(
            "proof_strength",
            "anecdotal",
            captured_at="2026-07-12T09:05:00+05:30",
            observed_at="2026-07-12T09:00:00+05:30",
            max_age_days=45,
        )
        snapshot = self.snapshot()
        dimension = snapshot["dimensions"]["proof_strength"]
        self.assertEqual("anecdotal", dimension["value"])
        self.assertEqual(fresh, dimension["claim_id"])
        disagreement = next(item for item in snapshot["conflicts"] if item["predicate"] == "proof_strength")
        self.assertEqual("STALE_DISAGREEMENT", disagreement["resolution"])
        self.assertFalse(disagreement["blocks_dimension"])
        self.assertIn(old, disagreement["stale_claim_ids"])

    def test_successor_resolves_current_position_but_not_historical_snapshot(self) -> None:
        original = self.add_claim("icp_clarity", "weak", max_age_days=90)
        successor = self.add_claim(
            "icp_clarity",
            "strong",
            captured_at="2026-07-10T09:05:00+05:30",
            observed_at="2026-07-10T09:00:00+05:30",
            max_age_days=90,
            supersedes_id=original,
        )
        historical = self.snapshot(as_of="2026-07-05T12:00:00+05:30")
        current = self.snapshot()
        self.assertEqual(original, historical["dimensions"]["icp_clarity"]["claim_id"])
        self.assertEqual("weak", historical["dimensions"]["icp_clarity"]["value"])
        self.assertEqual(successor, current["dimensions"]["icp_clarity"]["claim_id"])
        self.assertEqual("strong", current["dimensions"]["icp_clarity"]["value"])

    def test_restricted_and_prohibited_records_are_not_leaked(self) -> None:
        secret_value = "clinic-secret-alpha"
        restricted = self.add_claim(
            "problem_urgency",
            secret_value,
            sensitivity="RESTRICTED",
            max_age_days=60,
        )
        prohibited = self.add_claim(
            "problem_urgency",
            "do-not-use",
            evidence_state="PROHIBITED",
            max_age_days=60,
        )
        snapshot = self.snapshot(as_of="2026-07-02T12:00:00+05:30")
        serialized = json.dumps(snapshot)
        markdown = render_markdown(snapshot)
        self.assertNotIn(secret_value, serialized)
        self.assertNotIn(secret_value, markdown)
        self.assertNotIn(restricted, snapshot["input_record_ids"])
        self.assertNotIn(prohibited, snapshot["input_record_ids"])
        self.assertEqual(1, snapshot["restricted_records_excluded"])
        self.assertEqual(1, snapshot["prohibited_claims_excluded"])
        self.assertEqual("UNKNOWN", snapshot["dimensions"]["problem_urgency"]["status"])

    def test_open_overdue_and_superseded_assumptions_are_separated(self) -> None:
        old = self.add_assumption(review_by="2026-07-02T09:00:00+05:30")
        replacement = self.add_assumption(
            created_at="2026-07-10T09:00:00+05:30",
            review_by="2026-07-20T09:00:00+05:30",
            supersedes_id=old,
        )
        restricted = self.add_assumption(sensitivity="RESTRICTED")
        snapshot = self.snapshot()
        self.assertEqual([replacement], snapshot["open_assumption_ids"])
        self.assertEqual([], snapshot["overdue_assumption_ids"])
        self.assertNotIn(old, snapshot["input_record_ids"])
        self.assertNotIn(restricted, snapshot["input_record_ids"])
        self.assertEqual(1, snapshot["restricted_records_excluded"])

    def test_overdue_active_assumption_is_reported(self) -> None:
        assumption = self.add_assumption(review_by="2026-07-02T09:00:00+05:30")
        snapshot = self.snapshot()
        self.assertIn(assumption, snapshot["open_assumption_ids"])
        self.assertIn(assumption, snapshot["overdue_assumption_ids"])

    def test_evidence_and_source_precedence_choose_stronger_same_value_claim(self) -> None:
        weak = self.add_claim(
            "unit_economics",
            "provisional",
            evidence_state="INFERRED",
            confidence="LOW",
            source_type="PUBLIC_BENCHMARK",
            max_age_days=30,
        )
        strong = self.add_claim(
            "unit_economics",
            "provisional",
            evidence_state="VERIFIED",
            confidence="HIGH",
            source_type="PRODUCT_TELEMETRY",
            max_age_days=30,
        )
        snapshot = self.snapshot(as_of="2026-07-02T12:00:00+05:30")
        self.assertEqual(strong, snapshot["dimensions"]["unit_economics"]["claim_id"])
        self.assertNotEqual(weak, strong)
        self.assertEqual([], [item for item in snapshot["conflicts"] if item["predicate"] == "unit_economics"])

    def test_unrelated_subject_does_not_fill_position_dimension(self) -> None:
        self.add_claim("customer_access", "high", subject="campaign-alpha", max_age_days=30)
        snapshot = self.snapshot(as_of="2026-07-02T12:00:00+05:30")
        self.assertEqual("UNKNOWN", snapshot["dimensions"]["customer_access"]["status"])

    def test_future_as_of_is_rejected(self) -> None:
        with self.assertRaisesRegex(TruthStoreError, "as_of cannot be later"):
            build_snapshot(
                self.connection,
                "voice-agents",
                as_of="2026-07-14T12:00:00+05:30",
                generated_at="2026-07-13T12:00:00+05:30",
            )

    def test_snapshot_traceability_includes_claim_and_source_ids(self) -> None:
        source = self.add_source(source_type="CRM")
        claim_id = self.add_claim("data_quality", "mixed", source_id=source, max_age_days=14)
        snapshot = self.snapshot(as_of="2026-07-02T12:00:00+05:30")
        self.assertIn(claim_id, snapshot["input_record_ids"])
        self.assertIn(source, snapshot["input_record_ids"])

    def test_markdown_escapes_untrusted_html_and_table_delimiters(self) -> None:
        self.add_claim("problem_urgency", "<script>alert(1)</script>|urgent", max_age_days=60)
        snapshot = self.snapshot(as_of="2026-07-02T12:00:00+05:30")
        markdown = render_markdown(snapshot)
        self.assertNotIn("<script>", markdown)
        self.assertIn("&lt;script&gt;", markdown)
        self.assertIn("\\|urgent", markdown)

    def test_write_snapshot_uses_unique_generated_timestamp_and_private_workspace(self) -> None:
        snapshot_one = build_snapshot(
            self.connection,
            "voice-agents",
            as_of="2026-07-02T12:00:00+05:30",
            generated_at="2026-07-13T12:00:00+05:30",
        )
        snapshot_two = dict(snapshot_one)
        snapshot_two["generated_at"] = "2026-07-13T12:00:01+05:30"
        first_json, first_md = write_snapshot(self.workspace, snapshot_one)
        second_json, second_md = write_snapshot(self.workspace, snapshot_two)
        self.assertNotEqual(first_json, second_json)
        self.assertNotEqual(first_md, second_md)
        for path in (first_json, first_md, second_json, second_md):
            self.assertTrue(path.is_file())
            path.resolve().relative_to(self.workspace.resolve())


if __name__ == "__main__":
    unittest.main()
