#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from score import (
    EXPECTED_EVIDENCE_COST_TABLE_VERSION,
    EXPECTED_SOURCE_COSTS,
    EXPECTED_STATE_SCHEMA_VERSION,
    EXPECTED_TASK_DATA_VERSION,
)


STATE_PATH = Path("/var/lib/evidence/state.json")


class SeparateVerifierRuntimeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not STATE_PATH.is_file():
            raise AssertionError(
                "Harbor did not rehydrate the declared evidence-state artifact"
            )
        cls.state = json.loads(STATE_PATH.read_text())

    def test_artifact_schema(self) -> None:
        self.assertEqual(
            self.state.get("schema_version"),
            EXPECTED_STATE_SCHEMA_VERSION,
        )

    def test_server_and_scorer_cost_tables_match(self) -> None:
        self.assertEqual(self.state.get("source_costs"), EXPECTED_SOURCE_COSTS)
        self.assertEqual(
            self.state.get("evidence_cost_table_version"),
            EXPECTED_EVIDENCE_COST_TABLE_VERSION,
        )

    def test_task_data_version(self) -> None:
        self.assertEqual(
            self.state.get("task_data_version"),
            EXPECTED_TASK_DATA_VERSION,
        )

    def test_background_agent_probe_never_observed_verifier_material(self) -> None:
        probe = self.state.get("isolation_probe", {})
        self.assertTrue(probe.get("started"))
        self.assertGreater(int(probe.get("checks", 0)), 0)
        self.assertNotEqual(probe.get("uid"), 0)
        self.assertFalse(probe.get("tests_path_observed"))
        self.assertEqual(int(probe.get("readable_test_files", 0)), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
