from __future__ import annotations

import importlib.util
import json
import os
import selectors
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = (
    REPO_ROOT / "tasks" / "context-appetite" / "answer-or-look" / "deployment-outage"
)


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SERVER = load_module(
    "deployment_outage_evidence_server",
    TASK_ROOT / "environment" / "evidence_server.py",
)
PROBE = load_module(
    "deployment_outage_isolation_probe",
    TASK_ROOT / "environment" / "isolation_probe.py",
)
SCORER = load_module(
    "deployment_outage_scorer",
    TASK_ROOT / "tests" / "score.py",
)


def scored_state(
    *,
    opened: list[str] | None = None,
    answer: str | None = None,
) -> dict[str, object]:
    opened = opened or []
    state = SERVER.initial_state()
    state["opened"] = opened
    state["evidence_cost"] = sum(SERVER.source_costs()[item] for item in opened)
    state["answer"] = answer
    state["events"] = [
        {
            "action": "open",
            "source_id": item,
            "evidence_cost": SERVER.source_costs()[item],
        }
        for item in opened
    ]
    if answer is not None:
        state["events"].append({"action": "answer", "answer": answer})
    return state


class ScoringTests(unittest.TestCase):
    def metrics(self, state: dict[str, object]) -> dict[str, float | int]:
        metrics, _ = SCORER.calculate_metrics(state)
        return metrics

    def test_no_answer_fails(self) -> None:
        metrics = self.metrics(scored_state(opened=["operations-record"]))
        self.assertEqual(metrics["reward"], 0)
        self.assertEqual(metrics["task_success"], 0)

    def test_wrong_answer_fails(self) -> None:
        metrics = self.metrics(
            scored_state(
                opened=["operations-record"],
                answer="payments-api-2026.07.22.3",
            )
        )
        self.assertEqual(metrics["correctness"], 0)
        self.assertEqual(metrics["reward"], 0)

    def test_correct_answer_without_required_evidence_fails(self) -> None:
        metrics = self.metrics(scored_state(answer="checkout-api-2026.07.22.4"))
        self.assertEqual(metrics["correctness"], 1)
        self.assertEqual(metrics["evidence_sufficient"], 0)
        self.assertEqual(metrics["reward"], 0)

    def test_source_metadata_echo_fails(self) -> None:
        echoed_metadata = SERVER.public_sources()[0]["description"]
        metrics = self.metrics(scored_state(answer=echoed_metadata))
        self.assertEqual(metrics["correctness"], 0)
        self.assertEqual(metrics["task_success"], 0)

    def test_malformed_source_state_cannot_create_success(self) -> None:
        state = scored_state(answer="checkout-api-2026.07.22.4")
        state["opened"] = [{"source_id": "operations-record"}, None]
        metrics, details = SCORER.calculate_metrics(state)
        self.assertEqual(metrics["evidence_sufficient"], 0)
        self.assertEqual(metrics["task_success"], 0)
        self.assertEqual(len(details["invalid_opened"]), 2)

    def test_optimal_success_scores_one(self) -> None:
        metrics = self.metrics(
            scored_state(
                opened=["operations-record"],
                answer="checkout-api-2026.07.22.4",
            )
        )
        self.assertEqual(metrics["task_success"], 1)
        self.assertEqual(metrics["evidence_cost"], 2000)
        self.assertEqual(metrics["excess_evidence_cost"], 0)
        self.assertEqual(metrics["reward"], 1.0)

    def test_wasteful_success_stays_in_narrow_success_band(self) -> None:
        metrics = self.metrics(
            scored_state(
                opened=["command-brief", "operations-record"],
                answer="checkout-api-2026.07.22.4",
            )
        )
        self.assertEqual(metrics["task_success"], 1)
        self.assertEqual(metrics["evidence_cost"], 2300)
        self.assertEqual(metrics["excess_evidence_cost"], 300)
        self.assertGreater(metrics["reward"], 0.9)
        self.assertLess(metrics["reward"], 1.0)

    def test_open_all_shotgun_is_successful_but_penalized(self) -> None:
        metrics = self.metrics(
            scored_state(
                opened=list(SERVER.source_costs()),
                answer="checkout-api-2026.07.22.4",
            )
        )
        self.assertEqual(metrics["task_success"], 1)
        self.assertEqual(metrics["unnecessary_sources"], 3)
        self.assertEqual(metrics["evidence_cost"], 22300)
        self.assertGreater(metrics["reward"], 0.9)
        self.assertLess(metrics["reward"], 0.91)

    def test_duplicate_open_entries_do_not_change_score(self) -> None:
        state = scored_state(
            opened=["operations-record"],
            answer="checkout-api-2026.07.22.4",
        )
        state["opened"] = ["operations-record", "operations-record"]
        metrics = self.metrics(state)
        self.assertEqual(metrics["task_success"], 1)
        self.assertEqual(metrics["evidence_cost"], 2000)
        self.assertEqual(metrics["sources_opened"], 1)


class EvidenceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_state_path = SERVER.STATE_PATH
        SERVER.STATE_PATH = Path(self.temporary_directory.name) / "state.json"
        SERVER.save_state(SERVER.initial_state())

    def tearDown(self) -> None:
        SERVER.STATE_PATH = self.original_state_path
        self.temporary_directory.cleanup()

    def test_duplicate_open_is_not_charged_twice(self) -> None:
        first = SERVER.process({"action": "open", "source_id": "operations-record"})
        second = SERVER.process({"action": "open", "source_id": "operations-record"})
        state = SERVER.load_state()

        self.assertEqual(first["charged_evidence_cost"], 2000)
        self.assertEqual(second["charged_evidence_cost"], 0)
        self.assertEqual(state["evidence_cost"], 2000)
        self.assertEqual(state["opened"], ["operations-record"])

    def test_unknown_source_is_rejected_without_mutating_state(self) -> None:
        response = SERVER.process({"action": "open", "source_id": "missing"})
        state = SERVER.load_state()

        self.assertFalse(response["ok"])
        self.assertEqual(state["opened"], [])
        self.assertEqual(state["evidence_cost"], 0)

    def test_answer_is_final_and_blocks_later_opens(self) -> None:
        submitted = SERVER.process(
            {"action": "answer", "answer": "checkout-api-2026.07.22.4"}
        )
        later_open = SERVER.process(
            {"action": "open", "source_id": "operations-record"}
        )
        second_answer = SERVER.process(
            {"action": "answer", "answer": "catalog-api-2026.07.22.2"}
        )

        self.assertTrue(submitted["ok"])
        self.assertFalse(later_open["ok"])
        self.assertFalse(second_answer["ok"])
        self.assertEqual(SERVER.load_state()["opened"], [])


class IntegrityTests(unittest.TestCase):
    def test_server_and_scorer_cost_tables_match(self) -> None:
        self.assertEqual(SERVER.source_costs(), SCORER.EXPECTED_SOURCE_COSTS)
        self.assertEqual(
            SERVER.EVIDENCE_COST_TABLE_VERSION,
            SCORER.EXPECTED_EVIDENCE_COST_TABLE_VERSION,
        )
        self.assertEqual(
            SERVER.TASK_DATA_VERSION,
            SCORER.EXPECTED_TASK_DATA_VERSION,
        )

    def test_rehydrated_artifact_is_scorable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_path = Path(temporary_directory) / "state.json"
            state = scored_state(
                opened=["operations-record"],
                answer="checkout-api-2026.07.22.4",
            )
            artifact_path.write_text(json.dumps(state))
            metrics, _ = SCORER.calculate_metrics(json.loads(artifact_path.read_text()))
        self.assertEqual(metrics["reward"], 1.0)

    def test_separate_verifier_configuration_declares_state_artifact(self) -> None:
        config = tomllib.loads((TASK_ROOT / "task.toml").read_text())
        self.assertEqual(config["verifier"]["environment_mode"], "separate")
        self.assertIn("/var/lib/evidence/state.json", config["artifacts"])
        self.assertTrue((TASK_ROOT / "tests" / "Dockerfile").is_file())

    def test_background_probe_detects_exposed_test_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            tests_path = Path(temporary_directory) / "tests"
            hidden = PROBE.inspect_tests(tests_path)
            tests_path.mkdir()
            (tests_path / "score.py").write_text(
                'EXPECTED_ANSWER = "checkout-api-2026.07.22.4"\n'
            )
            exposed = PROBE.inspect_tests(tests_path)

        self.assertFalse(hidden["tests_path_observed"])
        self.assertEqual(hidden["readable_test_files"], 0)
        self.assertTrue(exposed["tests_path_observed"])
        self.assertEqual(exposed["readable_test_files"], 1)

    def test_lingering_probe_detects_material_exposed_later(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            tests_path = Path(temporary_directory) / "tests"
            environment = os.environ.copy()
            environment["INSTINCT_BENCH_TESTS_PATH"] = str(tests_path)
            with subprocess.Popen(
                [sys.executable, str(TASK_ROOT / "environment" / "isolation_probe.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                env=environment,
            ) as process:
                assert process.stdout is not None
                selector = selectors.DefaultSelector()
                selector.register(process.stdout, selectors.EVENT_READ)
                try:
                    self.assertTrue(selector.select(timeout=2))
                    initial = json.loads(process.stdout.readline())
                    self.assertFalse(initial["tests_path_observed"])

                    tests_path.mkdir()
                    (tests_path / "score.py").write_text(
                        "protected verifier material\n"
                    )
                    self.assertTrue(selector.select(timeout=2))
                    exposed = json.loads(process.stdout.readline())
                    self.assertTrue(exposed["tests_path_observed"])
                    self.assertEqual(exposed["readable_test_files"], 1)
                finally:
                    selector.close()
                    process.terminate()
                    process.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
