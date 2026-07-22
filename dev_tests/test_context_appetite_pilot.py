from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import tomllib
import unittest
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ROOT = REPO_ROOT / "tasks" / "context-appetite"
TASK_NAMES = (
    "deployment-outage",
    "answer-now",
    "complementary-evidence",
    "insufficient-evidence",
    "unreliable-or-conflicting-evidence",
)
IMPLEMENTATION_VERSION = "0.2.1"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class TaskBundle:
    name: str
    root: Path
    server: ModuleType
    scorer: ModuleType
    task_data: dict[str, Any]
    expected: dict[str, Any]


def load_bundles() -> dict[str, TaskBundle]:
    bundles: dict[str, TaskBundle] = {}
    for name in TASK_NAMES:
        root = DOMAIN_ROOT / name
        server = load_module(
            f"{name.replace('-', '_')}_evidence_server",
            root / "environment" / "evidence-sidecar" / "evidence_server.py",
        )
        scorer = load_module(
            f"{name.replace('-', '_')}_scorer",
            root / "tests" / "score.py",
        )
        task_data = json.loads(
            (root / "environment" / "evidence-sidecar" / "task_data.json").read_text()
        )
        expected = json.loads((root / "tests" / "expected.json").read_text())
        bundles[name] = TaskBundle(
            name=name,
            root=root,
            server=server,
            scorer=scorer,
            task_data=task_data,
            expected=expected,
        )
    return bundles


BUNDLES = load_bundles()


def payload_metrics(bundle: TaskBundle, source_id: str) -> tuple[int, int]:
    content = bundle.task_data["sources"][source_id]["content"]
    byte_count = len(content.encode("utf-8"))
    return byte_count, (byte_count + 3) // 4


def scored_state(
    bundle: TaskBundle,
    *,
    opened: list[str] | None = None,
    answer: str | None = None,
    duplicate_source: str | None = None,
    unknown_source: str | None = None,
    list_calls: int = 0,
    status_calls: int = 0,
) -> dict[str, Any]:
    opened = list(opened or [])
    costs = bundle.expected["source_costs"]
    state = bundle.server.initial_state()
    state["opened"] = opened
    state["observed_evidence_cost"] = sum(costs[source_id] for source_id in opened)
    state["events"] = [
        {"action": "list", "evidence_cost": 0} for _ in range(list_calls)
    ]
    state["events"].extend(
        {"action": "status", "evidence_cost": 0} for _ in range(status_calls)
    )

    payload_bytes = 0
    token_proxy = 0
    for source_id in opened:
        source_bytes, source_tokens = payload_metrics(bundle, source_id)
        payload_bytes += source_bytes
        token_proxy += source_tokens
        state["events"].append(
            {
                "action": "open",
                "source_id": source_id,
                "evidence_cost": costs[source_id],
                "payload_bytes": source_bytes,
                "payload_token_proxy": source_tokens,
            }
        )
    if duplicate_source is not None:
        source_bytes, source_tokens = payload_metrics(bundle, duplicate_source)
        payload_bytes += source_bytes
        token_proxy += source_tokens
        state["events"].append(
            {
                "action": "open_duplicate",
                "source_id": duplicate_source,
                "evidence_cost": 0,
                "payload_bytes": source_bytes,
                "payload_token_proxy": source_tokens,
            }
        )
    if unknown_source is not None:
        state["events"].append(
            {
                "action": "open_unknown",
                "source_id": unknown_source,
                "evidence_cost": 0,
            }
        )
    state["observed_evidence_payload_bytes"] = payload_bytes
    state["observed_evidence_token_proxy"] = token_proxy
    state["answer"] = answer
    if answer is not None:
        state["events"].append({"action": "answer", "answer": answer})
    state["agent_request_count"] = len(state["events"])
    state["finalized"] = True
    state["snapshot"] = {
        "complete": True,
        "authentication": "sidecar-file-token-v1",
        "task_id": bundle.expected["task_id"],
        "event_count": len(state["events"]),
        "opened_count": len(opened),
        "agent_request_count": state["agent_request_count"],
        "observed_evidence_cost": state["observed_evidence_cost"],
        "observed_evidence_payload_bytes": payload_bytes,
        "observed_evidence_token_proxy": token_proxy,
    }
    return state


def metrics_for(
    bundle: TaskBundle,
    *,
    opened: list[str] | None = None,
    answer: str | None = None,
) -> dict[str, float | int]:
    metrics, _ = bundle.scorer.calculate_metrics(
        scored_state(bundle, opened=opened, answer=answer)
    )
    return metrics


@contextmanager
def isolated_service(bundle: TaskBundle) -> Iterator[tuple[ModuleType, Path]]:
    server = bundle.server
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        original_paths = (
            server.STATE_PATH,
            server.SNAPSHOT_PATH,
            server.SNAPSHOT_TOKEN_PATH,
        )
        server.STATE_PATH = root / "state.json"
        server.SNAPSHOT_PATH = root / "snapshot.json"
        server.SNAPSHOT_TOKEN_PATH = root / "snapshot-token"
        try:
            yield server, root
        finally:
            (
                server.STATE_PATH,
                server.SNAPSHOT_PATH,
                server.SNAPSHOT_TOKEN_PATH,
            ) = original_paths


class SpecificationTests(unittest.TestCase):
    def test_taxonomy_has_exactly_five_tasks_directly_under_domain(self) -> None:
        actual = {
            path.name
            for path in DOMAIN_ROOT.iterdir()
            if path.is_dir() and (path / "task.toml").is_file()
        }
        self.assertEqual(actual, set(TASK_NAMES))
        self.assertFalse((DOMAIN_ROOT / "answer-or-look").exists())
        self.assertFalse((DOMAIN_ROOT / "evidence-acquisition").exists())

    def test_five_row_specification_names_every_task(self) -> None:
        specification = (DOMAIN_ROOT / "README.md").read_text()
        for name in TASK_NAMES:
            self.assertIn(f"`{name}`", specification)

    def test_public_data_and_hidden_contract_match(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                costs = {
                    source_id: source["evidence_cost"]
                    for source_id, source in bundle.task_data["sources"].items()
                }
                payload_bytes = {}
                token_proxy = {}
                for source_id in costs:
                    payload_bytes[source_id], token_proxy[source_id] = payload_metrics(
                        bundle, source_id
                    )
                self.assertEqual(
                    bundle.task_data["task_id"], bundle.expected["task_id"]
                )
                self.assertEqual(
                    bundle.task_data["task_data_version"],
                    bundle.expected["task_data_version"],
                )
                self.assertEqual(costs, bundle.expected["source_costs"])
                self.assertEqual(payload_bytes, bundle.expected["source_payload_bytes"])
                self.assertEqual(token_proxy, bundle.expected["source_token_proxy"])
                self.assertEqual(
                    bundle.task_data["source_order"],
                    bundle.expected["source_order"],
                )
                self.assertEqual(set(costs), set(bundle.task_data["source_order"]))
                self.assertEqual(bundle.expected["task_cost_cap"], sum(costs.values()))
                self.assertEqual(
                    bundle.expected["hindsight_minimum_cost"],
                    sum(costs[item] for item in bundle.expected["required_sources"]),
                )

    def test_harbor_020_sidecar_and_separate_verifier_configuration(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                config = tomllib.loads((bundle.root / "task.toml").read_text())
                self.assertEqual(config["schema_version"], "1.3")
                self.assertEqual(
                    config["metadata"]["implementation_version"],
                    IMPLEMENTATION_VERSION,
                )
                self.assertEqual(config["verifier"]["environment_mode"], "separate")
                self.assertEqual(
                    config["artifacts"],
                    [
                        {
                            "source": "/evidence-artifacts/state.json",
                            "service": "evidence",
                        }
                    ],
                )
                self.assertEqual(config["agent"]["user"], "agent")
                self.assertEqual(config["environment"]["network_mode"], "public")
                self.assertEqual(
                    config["verifier"]["environment"]["network_mode"],
                    "no-network",
                )
                self.assertEqual(
                    config["verifier"]["collect"][0]["service"], "evidence"
                )
                self.assertIn(
                    "snapshot.py", config["verifier"]["collect"][0]["command"]
                )
                self.assertTrue(
                    (bundle.root / "environment" / "docker-compose.yaml").is_file()
                )
                self.assertTrue((bundle.root / "tests" / "Dockerfile").is_file())
                self.assertTrue(
                    os.access(bundle.root / "solution" / "solve.sh", os.X_OK)
                )

    def test_shared_runtime_templates_do_not_drift(self) -> None:
        shared_paths = (
            "environment/Dockerfile",
            "environment/docker-compose.yaml",
            "environment/entrypoint.sh",
            "environment/evidence_cli.py",
            "environment/evidence-sidecar/Dockerfile",
            "environment/evidence-sidecar/evidence_server.py",
            "environment/evidence-sidecar/snapshot.py",
            "tests/Dockerfile",
            "tests/runtime_checks.py",
            "tests/score.py",
            "tests/test.sh",
        )
        reference = BUNDLES["deployment-outage"].root
        for relative_path in shared_paths:
            expected = (reference / relative_path).read_bytes()
            for bundle in BUNDLES.values():
                with self.subTest(task=bundle.name, path=relative_path):
                    self.assertEqual(
                        (bundle.root / relative_path).read_bytes(), expected
                    )

    def test_runtime_images_and_terminus_dependencies_are_pinned(self) -> None:
        digest = (
            "@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d"
        )
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                main = (bundle.root / "environment" / "Dockerfile").read_text()
                sidecar = (
                    bundle.root / "environment" / "evidence-sidecar" / "Dockerfile"
                ).read_text()
                verifier = (bundle.root / "tests" / "Dockerfile").read_text()
                self.assertIn(digest, main)
                self.assertIn(digest, sidecar)
                self.assertIn(digest, verifier)
                self.assertIn("asciinema=2.2.0-1", main)
                self.assertIn("tmux=3.3a-3", main)
                self.assertIn("USER evidence", sidecar)

    def test_agent_image_excludes_hidden_contract_and_probe_code(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                environment = bundle.root / "environment"
                dockerfile = (environment / "Dockerfile").read_text()
                compose = (environment / "docker-compose.yaml").read_text()
                for protected_name in ("expected.json", "score.py", "task_data.json"):
                    self.assertNotIn(protected_name, dockerfile)
                self.assertNotIn("probe", dockerfile.lower())
                self.assertFalse((environment / "isolation_probe.py").exists())
                self.assertFalse((environment / "probe_launcher.py").exists())
                self.assertNotIn("docker.sock", compose)
                self.assertNotIn("privileged", compose)
                self.assertNotIn("cap_add", compose)

    def test_snapshot_credential_is_sidecar_local(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                environment = bundle.root / "environment"
                snapshot = (
                    environment / "evidence-sidecar" / "snapshot.py"
                ).read_text()
                server = (
                    environment / "evidence-sidecar" / "evidence_server.py"
                ).read_text()
                main_files = (
                    (environment / "Dockerfile").read_text()
                    + (environment / "docker-compose.yaml").read_text()
                    + (bundle.root / "task.toml").read_text()
                )
                self.assertIn("SNAPSHOT_TOKEN_PATH", snapshot)
                self.assertIn("secrets.token_urlsafe", server)
                self.assertIn("hmac.compare_digest", server)
                self.assertNotIn("snapshot-token", main_files)

    def test_prompts_describe_optional_catalog_and_separate_cost(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                instruction = (bundle.root / "instruction.md").read_text()
                self.assertIn("You may inspect", instruction)
                self.assertIn(
                    "Evidence use and cost are reported separately", instruction
                )
                self.assertNotIn("Among successful answers", instruction)

    def test_run_manifest_scaffold_separates_execution_and_task_outcome(self) -> None:
        schema_path = REPO_ROOT / "results" / "manifests" / "schema-v1.json"
        template_path = REPO_ROOT / "results" / "manifests" / "template.json"
        schema = json.loads(schema_path.read_text())
        template = json.loads(template_path.read_text())
        self.assertEqual(schema["$id"], "instinct-bench/run-manifest/v1")
        self.assertEqual(template["schema_version"], "1.0")
        self.assertIn("execution_state", schema["$defs"]["trial"]["properties"])
        self.assertIn("task_outcome", schema["$defs"]["trial"]["properties"])
        self.assertIn("agent_egress", schema["properties"])
        self.assertIn("contract_visibility", schema["properties"])
        self.assertIn("provider_routing", schema["properties"]["runner"]["properties"])
        self.assertIn("seed", schema["$defs"]["trial"]["properties"])
        self.assertIn("telemetry", schema["$defs"]["trial"]["properties"])


class ScoringTests(unittest.TestCase):
    def test_reference_paths_have_binary_success_and_reward(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                metrics = metrics_for(
                    bundle,
                    opened=bundle.expected["required_sources"],
                    answer=bundle.expected["expected_answer"],
                )
                self.assertEqual(metrics["task_success"], 1)
                self.assertEqual(metrics["verifier_integrity"], 1)
                self.assertEqual(metrics["reward"], 1)

    def test_no_answer_and_wrong_answer_always_fail(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                opened = bundle.expected["required_sources"]
                no_answer = metrics_for(bundle, opened=opened)
                wrong = metrics_for(bundle, opened=opened, answer="definitely-wrong")
                self.assertEqual(no_answer["reward"], 0)
                self.assertEqual(wrong["reward"], 0)

    def test_correct_answer_without_required_evidence_only_passes_answer_now(
        self,
    ) -> None:
        succeeded = []
        for bundle in BUNDLES.values():
            metrics = metrics_for(bundle, answer=bundle.expected["expected_answer"])
            if metrics["task_success"]:
                succeeded.append(bundle.name)
        self.assertEqual(succeeded, ["answer-now"])

    def test_wasteful_success_remains_binary_success(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                metrics = metrics_for(
                    bundle,
                    opened=bundle.expected["source_order"],
                    answer=bundle.expected["expected_answer"],
                )
                self.assertEqual(metrics["task_success"], 1)
                self.assertEqual(metrics["reward"], 1)
                self.assertEqual(metrics["cost_score"], 0)

    def test_cost_and_hindsight_remain_diagnostics(self) -> None:
        bundle = BUNDLES["deployment-outage"]
        metrics = metrics_for(
            bundle,
            opened=["record-c", "record-a"],
            answer=bundle.expected["expected_answer"],
        )
        expected_cost_score = 1 - 2300 / 22300
        self.assertAlmostEqual(metrics["cost_score"], expected_cost_score, places=6)
        self.assertEqual(metrics["hindsight_cost_gap"], 300)
        self.assertEqual(metrics["sources_outside_hindsight_minimum"], 1)
        self.assertEqual(metrics["reward"], 1)

    def test_selective_decision_is_distinct_from_answer_correctness(self) -> None:
        answerable = BUNDLES["deployment-outage"]
        wrong = metrics_for(answerable, opened=["record-a"], answer="wrong-id")
        abstain = metrics_for(answerable, opened=["record-a"], answer="INSUFFICIENT")
        insufficient = BUNDLES["insufficient-evidence"]
        structured = metrics_for(
            insufficient,
            opened=insufficient.expected["required_sources"],
            answer=insufficient.expected["expected_answer"],
        )
        self.assertEqual(wrong["selective_decision_correct"], 1)
        self.assertEqual(wrong["correctness"], 0)
        self.assertEqual(abstain["selective_decision_correct"], 0)
        self.assertEqual(structured["selective_decision_correct"], 1)
        self.assertEqual(structured["task_success"], 1)

    def test_payload_and_zero_cost_tool_metrics_are_visible(self) -> None:
        bundle = BUNDLES["deployment-outage"]
        state = scored_state(
            bundle,
            opened=["record-a"],
            answer=bundle.expected["expected_answer"],
            list_calls=1,
            status_calls=2,
        )
        metrics, details = bundle.scorer.calculate_metrics(state)
        self.assertEqual(metrics["list_calls"], 1)
        self.assertEqual(metrics["status_calls"], 2)
        self.assertEqual(metrics["zero_cost_tool_calls"], 3)
        self.assertEqual(metrics["evidence_payload_bytes"], 331)
        self.assertEqual(metrics["evidence_token_proxy"], 83)
        self.assertEqual(metrics["verifier_integrity"], 1, details["integrity_errors"])

    def test_old_or_misleading_metric_names_are_gone(self) -> None:
        metrics = metrics_for(
            BUNDLES["deployment-outage"],
            opened=["record-a"],
            answer="checkout-api-2026.07.22.4",
        )
        for old_name in (
            "unnecessary_sources",
            "evidence_efficiency",
            "optimal_evidence_cost",
            "abstention_validity",
        ):
            self.assertNotIn(old_name, metrics)


class ContractPathTests(unittest.TestCase):
    def successes(self, policy: str) -> list[str]:
        successes: list[str] = []
        for bundle in BUNDLES.values():
            if policy == "answer-immediately":
                opened: list[str] = []
                answer = bundle.expected["expected_answer"]
            elif policy == "abstain-immediately":
                opened = []
                answer = "INSUFFICIENT"
            elif policy == "open-all":
                opened = bundle.expected["source_order"]
                answer = bundle.expected["expected_answer"]
            elif policy == "cheapest-first":
                opened = [
                    min(
                        bundle.expected["source_costs"],
                        key=bundle.expected["source_costs"].get,
                    )
                ]
                answer = bundle.expected["expected_answer"]
            elif policy == "fixed-order":
                opened = bundle.expected["source_order"][:2]
                answer = bundle.expected["expected_answer"]
            elif policy == "stop-after-one":
                opened = bundle.expected["source_order"][:1]
                answer = bundle.expected["expected_answer"]
            else:
                raise AssertionError(f"Unknown contract path: {policy}")
            if metrics_for(bundle, opened=opened, answer=answer)["task_success"]:
                successes.append(bundle.name)
        return successes

    def test_adversarial_and_canned_contract_paths(self) -> None:
        self.assertEqual(self.successes("answer-immediately"), ["answer-now"])
        self.assertEqual(self.successes("abstain-immediately"), [])
        self.assertEqual(self.successes("open-all"), list(TASK_NAMES))
        self.assertEqual(self.successes("cheapest-first"), ["answer-now"])
        self.assertEqual(
            self.successes("fixed-order"),
            ["deployment-outage", "answer-now"],
        )
        self.assertEqual(self.successes("stop-after-one"), ["answer-now"])


class EvidenceServiceTests(unittest.TestCase):
    def exercise_service(self, bundle: TaskBundle) -> None:
        with isolated_service(bundle) as (server, _):
            server.initialize_runtime()
            token = server.SNAPSHOT_TOKEN_PATH.read_text().strip()
            source_id = bundle.expected["source_order"][0]

            forged_probe = server.process(
                {
                    "action": "probe",
                    "report": {"started": True, "checks": 99, "uid": 999},
                }
            )
            unauthenticated_snapshot = server.process({"action": "snapshot"})
            wrong_snapshot = server.process(
                {"action": "snapshot", "snapshot_token": "wrong"}
            )
            listed = server.process({"action": "list"})
            status = server.process({"action": "status"})
            first = server.process({"action": "open", "source_id": source_id})
            duplicate = server.process({"action": "open", "source_id": source_id})
            unknown = server.process({"action": "open", "source_id": "record-missing"})
            submitted = server.process(
                {"action": "answer", "answer": bundle.expected["expected_answer"]}
            )
            later_open = server.process(
                {"action": "open", "source_id": bundle.expected["source_order"][-1]}
            )
            authenticated_snapshot = server.process(
                {"action": "snapshot", "snapshot_token": token}
            )
            repeated_snapshot = server.process(
                {"action": "snapshot", "snapshot_token": token}
            )
            state = json.loads(server.SNAPSHOT_PATH.read_text())

        self.assertFalse(forged_probe["ok"])
        self.assertFalse(unauthenticated_snapshot["ok"])
        self.assertFalse(wrong_snapshot["ok"])
        self.assertTrue(listed["ok"])
        self.assertTrue(status["ok"])
        self.assertEqual(
            first["charged_evidence_cost"],
            bundle.expected["source_costs"][source_id],
        )
        self.assertEqual(duplicate["charged_evidence_cost"], 0)
        self.assertFalse(unknown["ok"])
        self.assertTrue(submitted["ok"])
        self.assertFalse(later_open["ok"])
        self.assertTrue(authenticated_snapshot["ok"])
        self.assertFalse(repeated_snapshot["ok"])
        self.assertTrue(state["finalized"])
        self.assertNotIn("isolation_probe", state)
        self.assertTrue(state["snapshot"]["complete"])
        self.assertEqual(state["snapshot"]["authentication"], "sidecar-file-token-v1")
        self.assertEqual(state["opened"], [source_id])
        self.assertEqual(
            [event["action"] for event in state["events"]],
            ["list", "status", "open", "open_duplicate", "open_unknown", "answer"],
        )
        source_bytes, source_tokens = payload_metrics(bundle, source_id)
        self.assertEqual(state["observed_evidence_payload_bytes"], source_bytes * 2)
        self.assertEqual(state["observed_evidence_token_proxy"], source_tokens * 2)

    def test_all_task_services_enforce_the_same_state_contract(self) -> None:
        for bundle in BUNDLES.values():
            with self.subTest(task=bundle.name):
                self.exercise_service(bundle)

    def test_loopback_caller_cannot_snapshot_without_sidecar_credential(self) -> None:
        bundle = BUNDLES["deployment-outage"]
        with isolated_service(bundle) as (server, _):
            server.initialize_runtime()
            response = server.process({"action": "snapshot"})
            self.assertFalse(response["ok"])
            self.assertFalse(server.SNAPSHOT_PATH.exists())
            self.assertFalse(server.load_state()["finalized"])

    def test_startup_removes_stale_state_snapshot_and_credential(self) -> None:
        bundle = BUNDLES["deployment-outage"]
        with isolated_service(bundle) as (server, _):
            server.STATE_PATH.write_text('{"stale": true}\n')
            server.SNAPSHOT_PATH.write_text('{"stale": true}\n')
            server.SNAPSHOT_TOKEN_PATH.write_text("old-token\n")
            server.initialize_runtime()
            token = server.SNAPSHOT_TOKEN_PATH.read_text().strip()
            state = json.loads(server.STATE_PATH.read_text())
            self.assertNotEqual(token, "old-token")
            self.assertGreater(len(token), 40)
            self.assertEqual(server.SNAPSHOT_TOKEN_PATH.stat().st_mode & 0o777, 0o600)
            self.assertFalse(server.SNAPSHOT_PATH.exists())
            self.assertEqual(state, server.initial_state())


class IntegrityTests(unittest.TestCase):
    def assert_integrity_failure(
        self, state: dict[str, Any], bundle: TaskBundle
    ) -> None:
        metrics, details = bundle.scorer.calculate_metrics(state)
        self.assertEqual(metrics["verifier_integrity"], 0)
        self.assertEqual(metrics["reward"], 0)
        self.assertTrue(details["integrity_errors"])

    def test_tampered_cost_event_snapshot_payload_and_probe_fail_closed(self) -> None:
        bundle = BUNDLES["deployment-outage"]
        base = scored_state(
            bundle,
            opened=["record-a"],
            answer=bundle.expected["expected_answer"],
        )
        mutations = []
        cost = json.loads(json.dumps(base))
        cost["observed_evidence_cost"] = 0
        mutations.append(cost)
        event = json.loads(json.dumps(base))
        event["events"][0]["evidence_cost"] = 1
        mutations.append(event)
        payload = json.loads(json.dumps(base))
        payload["events"][0]["payload_bytes"] += 1
        mutations.append(payload)
        snapshot = json.loads(json.dumps(base))
        snapshot["snapshot"]["authentication"] = "loopback"
        mutations.append(snapshot)
        probe = json.loads(json.dumps(base))
        probe["isolation_probe"] = {"started": True, "checks": 99, "uid": 999}
        mutations.append(probe)
        for state in mutations:
            self.assert_integrity_failure(state, bundle)

    def test_duplicate_and_unknown_attempts_are_diagnostics(self) -> None:
        bundle = BUNDLES["deployment-outage"]
        state = scored_state(
            bundle,
            opened=["record-a"],
            answer=bundle.expected["expected_answer"],
            duplicate_source="record-a",
            unknown_source="record-missing",
        )
        metrics, details = bundle.scorer.calculate_metrics(state)
        self.assertEqual(metrics["verifier_integrity"], 1, details["integrity_errors"])
        self.assertEqual(metrics["duplicate_open_attempts"], 1)
        self.assertEqual(metrics["unknown_source_attempts"], 1)
        self.assertEqual(metrics["observed_evidence_cost"], 2000)
        self.assertEqual(metrics["evidence_payload_bytes"], 662)

    def test_open_event_after_final_answer_fails_integrity(self) -> None:
        bundle = BUNDLES["deployment-outage"]
        state = scored_state(
            bundle,
            opened=["record-a"],
            answer=bundle.expected["expected_answer"],
        )
        source_bytes, source_tokens = payload_metrics(bundle, "record-c")
        state["events"].append(
            {
                "action": "open",
                "source_id": "record-c",
                "evidence_cost": 300,
                "payload_bytes": source_bytes,
                "payload_token_proxy": source_tokens,
            }
        )
        state["snapshot"]["event_count"] += 1
        state["agent_request_count"] += 1
        state["snapshot"]["agent_request_count"] += 1
        self.assert_integrity_failure(state, bundle)

    def test_missing_malformed_and_non_object_artifacts_fail_closed(self) -> None:
        bundle = BUNDLES["answer-now"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cases = (("missing.json", None), ("broken.json", "{"), ("list.json", "[]"))
            for name, content in cases:
                with self.subTest(case=name):
                    path = root / name
                    if content is not None:
                        path.write_text(content)
                    state, artifact_errors = bundle.scorer.load_state_artifact(path)
                    metrics, details = bundle.scorer.calculate_metrics(
                        state,
                        external_integrity_errors=artifact_errors,
                    )
                    self.assertEqual(metrics["verifier_integrity"], 0)
                    self.assertEqual(metrics["reward"], 0)
                    self.assertTrue(details["integrity_errors"])

    def test_verifier_check_failure_zeroes_success(self) -> None:
        bundle = BUNDLES["answer-now"]
        state = scored_state(bundle, answer=bundle.expected["expected_answer"])
        metrics, _ = bundle.scorer.calculate_metrics(
            state,
            verifier_checks_passed=False,
        )
        self.assertEqual(metrics["verifier_integrity"], 0)
        self.assertEqual(metrics["reward"], 0)


if __name__ == "__main__":
    unittest.main()
