#!/usr/bin/env python3
from __future__ import annotations

import unittest

from score import EXPECTED, STATE_PATH, calculate_metrics, load_state_artifact


class SeparateVerifierRuntimeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.state, artifact_errors = load_state_artifact(STATE_PATH)
        if artifact_errors:
            raise AssertionError("; ".join(artifact_errors))

    def test_sidecar_snapshot_identity_and_versions(self) -> None:
        self.assertEqual(self.state.get("task_id"), EXPECTED["task_id"])
        self.assertEqual(
            self.state.get("schema_version"),
            EXPECTED["state_schema_version"],
        )
        self.assertEqual(
            self.state.get("task_data_version"),
            EXPECTED["task_data_version"],
        )
        self.assertEqual(
            self.state.get("evidence_cost_table_version"),
            EXPECTED["evidence_cost_table_version"],
        )

    def test_sidecar_and_scorer_contracts_match(self) -> None:
        self.assertEqual(self.state.get("source_costs"), EXPECTED["source_costs"])
        self.assertEqual(self.state.get("source_order"), EXPECTED["source_order"])

    def test_snapshot_is_authenticated_and_complete(self) -> None:
        self.assertTrue(self.state.get("finalized"))
        snapshot = self.state.get("snapshot", {})
        self.assertTrue(snapshot.get("complete"))
        self.assertEqual(snapshot.get("task_id"), EXPECTED["task_id"])
        self.assertEqual(
            snapshot.get("authentication"),
            "sidecar-file-token-v1",
        )
        self.assertEqual(
            snapshot.get("observed_evidence_payload_bytes"),
            self.state.get("observed_evidence_payload_bytes"),
        )
        self.assertEqual(
            snapshot.get("observed_evidence_token_proxy"),
            self.state.get("observed_evidence_token_proxy"),
        )

    def test_agent_authored_probe_telemetry_is_absent(self) -> None:
        self.assertNotIn("isolation_probe", self.state)

    def test_event_ledger_is_internally_consistent(self) -> None:
        metrics, details = calculate_metrics(self.state)
        self.assertEqual(metrics["verifier_integrity"], 1, details["integrity_errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
