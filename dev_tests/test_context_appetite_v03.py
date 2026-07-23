from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import tomllib
import unittest
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from instinct_bench.context_appetite import generator  # noqa: E402
from instinct_bench.context_appetite.baselines import (  # noqa: E402
    evaluate_all,
    summarize,
)
from instinct_bench.context_appetite.schemas import CONDITIONS  # noqa: E402


DEV_DIR = REPO_ROOT / "evals" / "context-appetite" / "dev"
EVAL_SECRET = b"private-test-secret-not-used-for-release-0001"


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def load_score(task_id: str):
    path = DEV_DIR / task_id / "tests" / "score.py"
    name = f"score_{task_id.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_server(task_id: str):
    path = DEV_DIR / task_id / "environment" / "evidence-sidecar" / "evidence_server.py"
    name = f"server_{task_id.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_state(score, opened: tuple[str, ...], submission: object) -> dict:
    expected = score.EXPECTED
    events = []
    observed_cost = 0
    payload_bytes = 0
    token_proxy = 0
    for source_id in opened:
        cost = expected["source_costs"][source_id]
        source_bytes = expected["source_payload_bytes"][source_id]
        source_tokens = expected["source_token_proxy"][source_id]
        events.append(
            {
                "action": "open",
                "source_id": source_id,
                "evidence_cost": cost,
                "payload_bytes": source_bytes,
                "payload_token_proxy": source_tokens,
            }
        )
        observed_cost += cost
        payload_bytes += source_bytes
        token_proxy += source_tokens
    if submission is not None:
        events.append({"action": "submit", "submission": submission})
    state = {
        "schema_version": expected["state_schema_version"],
        "task_id": expected["task_id"],
        "task_data_version": expected["task_data_version"],
        "evidence_cost_table_version": expected["evidence_cost_table_version"],
        "source_costs": expected["source_costs"],
        "source_order": expected["source_order"],
        "opened": list(opened),
        "observed_evidence_cost": observed_cost,
        "observed_evidence_payload_bytes": payload_bytes,
        "observed_evidence_token_proxy": token_proxy,
        "submission": submission,
        "events": events,
        "agent_request_count": len(events),
        "finalized": True,
        "snapshot": {
            "complete": True,
            "authentication": "sidecar-file-token-v1",
            "task_id": expected["task_id"],
            "event_count": len(events),
            "opened_count": len(opened),
            "agent_request_count": len(events),
            "observed_evidence_cost": observed_cost,
            "observed_evidence_payload_bytes": payload_bytes,
            "observed_evidence_token_proxy": token_proxy,
        },
    }
    return state


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dev_specs = generator.build_specs(generator.DEV_SECRET, "dev")
        cls.eval_specs = generator.build_specs(EVAL_SECRET, "eval")

    def test_population_taxonomy_and_split_isolation(self) -> None:
        self.assertEqual(len(self.dev_specs), 30)
        self.assertEqual(len(self.eval_specs), 75)
        self.assertEqual(
            {spec.task_id for spec in self.eval_specs},
            {f"ca-eval-{index:03d}" for index in range(1, 76)},
        )
        for specs, block_count in ((self.dev_specs, 6), (self.eval_specs, 15)):
            blocks = defaultdict(list)
            for spec in specs:
                blocks[spec.scenario_block].append(spec)
            self.assertEqual(len(blocks), block_count)
            for rows in blocks.values():
                self.assertEqual(
                    Counter(row.condition for row in rows), Counter(CONDITIONS)
                )
                self.assertEqual(len({row.latent_entity_id for row in rows}), 1)
        self.assertTrue(
            {spec.title for spec in self.dev_specs}.isdisjoint(
                spec.title for spec in self.eval_specs
            )
        )

    def test_eval_task_ids_do_not_encode_condition_or_block(self) -> None:
        second_secret = b"different-private-test-secret-not-for-release-0002"
        second_specs = generator.build_specs(second_secret, "eval")
        first_mapping = {
            spec.task_id: (spec.condition, spec.scenario_block)
            for spec in self.eval_specs
        }
        second_mapping = {
            spec.task_id: (spec.condition, spec.scenario_block) for spec in second_specs
        }
        self.assertEqual(set(first_mapping), set(second_mapping))
        self.assertNotEqual(first_mapping, second_mapping)
        self.assertNotEqual(
            [first_mapping[f"ca-eval-{index:03d}"][0] for index in range(1, 76)],
            list(CONDITIONS) * 15,
        )
        for condition in CONDITIONS:
            suffixes = {
                int(spec.task_id.rsplit("-", 1)[1]) % len(CONDITIONS)
                for spec in self.eval_specs
                if spec.condition == condition
            }
            self.assertGreater(len(suffixes), 1)

        self.assertNotEqual(
            [spec.condition for spec in self.eval_specs],
            list(CONDITIONS) * 15,
        )
        self.assertNotEqual(
            [spec.task_id for spec in self.eval_specs],
            [spec.task_id for spec in second_specs],
        )

    def test_costs_positions_and_relevance_are_balanced(self) -> None:
        for specs in (self.dev_specs, self.eval_specs):
            for spec in specs:
                self.assertEqual(
                    sorted(source.evidence_cost for source in spec.sources),
                    [1, 2, 4, 8],
                )
                self.assertEqual(
                    sum(source.evidence_cost for source in spec.sources), 15
                )
            for condition in CONDITIONS[1:]:
                rows = [spec for spec in specs if spec.condition == condition]
                position_counts = Counter(
                    spec.source_order.index(spec.accepted_proof_sets[0][0])
                    for spec in rows
                )
                cost_counts = Counter(
                    spec.source_map[spec.accepted_proof_sets[0][0]].evidence_cost
                    for spec in rows
                )
                self.assertLessEqual(
                    max(position_counts.values()) - min(position_counts.values()), 1
                )
                self.assertLessEqual(
                    max(cost_counts.values()) - min(cost_counts.values()), 1
                )
                first_is_cheapest = [
                    spec.source_map[spec.source_order[0]].evidence_cost == 1
                    for spec in rows
                ]
                self.assertIn(True, first_is_cheapest)
                self.assertIn(False, first_is_cheapest)

    def test_eval_primary_price_and_position_are_jointly_counterbalanced(self) -> None:
        for condition in CONDITIONS[1:]:
            rows = [spec for spec in self.eval_specs if spec.condition == condition]
            joint_cells = Counter(
                (
                    spec.source_map[spec.accepted_proof_sets[0][0]].evidence_cost,
                    spec.source_order.index(spec.accepted_proof_sets[0][0]),
                )
                for spec in rows
            )
            self.assertEqual(len(joint_cells), 15)
            self.assertEqual(set(joint_cells.values()), {1})

        by_block = defaultdict(list)
        for spec in self.eval_specs:
            if spec.condition != "answer-now":
                primary = spec.accepted_proof_sets[0][0]
                by_block[spec.scenario_block].append(
                    (
                        spec.source_map[primary].evidence_cost,
                        spec.source_order.index(primary),
                    )
                )
        self.assertTrue(
            all(len(set(presentations)) == 1 for presentations in by_block.values())
        )

    def test_answer_visibility_matches_only_answer_now(self) -> None:
        for spec in self.dev_specs + self.eval_specs:
            if spec.condition == "answer-now":
                self.assertIn(spec.latent_entity_id, spec.initial_context)
            else:
                self.assertNotIn(spec.latent_entity_id, spec.initial_context)
            for source in spec.sources:
                self.assertNotIn(spec.latent_entity_id, source.description)
            self.assertNotIn(spec.condition, spec.task_id)

    def test_alternative_proof_paths_exist_without_hidden_path_matching(self) -> None:
        alternative = [
            spec for spec in self.dev_specs if len(spec.accepted_proof_sets) > 1
        ]
        self.assertGreaterEqual(len(alternative), 5)
        for spec in alternative:
            self.assertTrue(all(path for path in spec.accepted_proof_sets))

    def test_generator_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"
            generator.generate(
                split="dev",
                secret=generator.DEV_SECRET,
                output_dir=first,
                replace=False,
            )
            generator.generate(
                split="dev",
                secret=generator.DEV_SECRET,
                output_dir=second,
                replace=False,
            )
            self.assertEqual(tree_digest(first), tree_digest(second))

    def test_committed_dev_generation_matches_source(self) -> None:
        metadata = json.loads((DEV_DIR / "release-metadata.json").read_text())
        self.assertEqual(
            metadata,
            generator.release_metadata(generator.DEV_SECRET, self.dev_specs, DEV_DIR),
        )
        self.assertEqual(
            metadata["release"]["dataset_commitment"],
            generator.dataset_commitment(self.dev_specs),
        )
        self.assertEqual(
            metadata["release"]["package_set_commitment"],
            generator.package_set_commitment(DEV_DIR, self.dev_specs),
        )
        manifest = tomllib.loads((DEV_DIR / "dataset.toml").read_text())
        self.assertEqual(
            manifest["dataset"]["name"], "instinct-bench/context-appetite-dev"
        )
        self.assertEqual(len(manifest["tasks"]), 30)
        for row in manifest["tasks"]:
            task_id = row["name"].split("/", 1)[1]
            self.assertEqual(row["digest"], generator.task_digest(DEV_DIR / task_id))

    def test_public_release_commitment_discloses_no_task_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "eval"
            generator.generate(
                split="eval",
                secret=EVAL_SECRET,
                output_dir=output_dir,
                replace=False,
            )
            commitment = generator.public_release_commitment(
                EVAL_SECRET, self.eval_specs, output_dir
            )
            self.assertNotIn("tasks", commitment)
            release = commitment["release"]
            self.assertEqual(release["expected_task_count"], 75)
            self.assertEqual(release["expected_block_count"], 15)
            self.assertEqual(
                release["dataset_commitment"],
                generator.dataset_commitment(self.eval_specs),
            )
            self.assertEqual(
                release["package_set_commitment"],
                generator.package_set_commitment(output_dir, self.eval_specs),
            )
            encoded = json.dumps(commitment)
            self.assertNotIn(self.eval_specs[0].latent_entity_id, encoded)
            self.assertNotIn(self.eval_specs[0].condition, encoded)

    def test_private_secret_file_must_not_be_group_or_world_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "release.secret"
            path.write_bytes(EVAL_SECRET)
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                generator.read_private_secret(path)
            path.chmod(0o600)
            self.assertEqual(generator.read_private_secret(path), EVAL_SECRET)

    def test_static_runtime_templates_do_not_drift(self) -> None:
        relative_files = [
            path.relative_to(generator.TEMPLATE_ROOT)
            for path in generator.TEMPLATE_ROOT.rglob("*")
            if path.is_file()
        ]
        for relative in relative_files:
            expected = (generator.TEMPLATE_ROOT / relative).read_bytes()
            for spec in self.dev_specs:
                self.assertEqual(
                    (DEV_DIR / spec.task_id / relative).read_bytes(), expected
                )

    def test_main_agent_image_does_not_copy_hidden_contract(self) -> None:
        for spec in self.dev_specs:
            task_dir = DEV_DIR / spec.task_id
            dockerfile = (task_dir / "environment" / "Dockerfile").read_text()
            self.assertNotIn("task_data.json", dockerfile)
            self.assertNotIn("expected.json", dockerfile)
            if spec.condition != "answer-now":
                self.assertNotIn(
                    spec.latent_entity_id, (task_dir / "instruction.md").read_text()
                )


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs = generator.build_specs(EVAL_SECRET, "eval")
        cls.summary = summarize(evaluate_all(cls.specs))

    def test_oracle_and_open_all_succeed_but_oracle_dominates_cost(self) -> None:
        oracle = self.summary["proof-aware-oracle"]
        open_all = self.summary["open-all"]
        self.assertEqual(oracle["optimistic_successes"], 75)
        self.assertEqual(open_all["optimistic_successes"], 75)
        self.assertLess(oracle["mean_evidence_cost"], open_all["mean_evidence_cost"])
        self.assertGreater(
            oracle["mean_optimistic_policy_utility"],
            open_all["mean_optimistic_policy_utility"],
        )

    def test_no_one_source_or_answer_now_policy_dominates(self) -> None:
        self.assertEqual(self.summary["answer-immediately"]["optimistic_successes"], 15)
        self.assertEqual(self.summary["abstain-immediately"]["optimistic_successes"], 0)
        for name in (
            "first-listed",
            "cheapest-first",
            "highest-reliability-first",
            "random-one",
        ):
            self.assertLess(self.summary[name]["optimistic_successes"], 75)
            self.assertGreater(self.summary[name]["optimistic_successes"], 0)


class EvidenceServiceTests(unittest.TestCase):
    def test_catalog_is_redacted_and_submission_is_final(self) -> None:
        server = load_server("ca-dev-002")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server.STATE_PATH = root / "state.json"
            server.SNAPSHOT_PATH = root / "snapshot.json"
            server.SNAPSHOT_TOKEN_PATH = root / "snapshot-token"
            server.initialize_runtime()
            listing = server.process({"action": "list"})
            self.assertTrue(listing["ok"])
            self.assertTrue(listing["sources"])
            self.assertTrue(
                all("content" not in source for source in listing["sources"])
            )
            source_id = listing["sources"][0]["id"]
            opened = server.process({"action": "open", "source_id": source_id})
            self.assertTrue(opened["ok"])
            self.assertIn("content", opened)
            submission = {
                "decision": "answer",
                "answer": {"entity_id": "test-entity"},
                "confidence": 0.5,
            }
            submitted = server.process({"action": "submit", "submission": submission})
            self.assertEqual(submitted["submission"], submission)
            after_final = server.process({"action": "open", "source_id": source_id})
            self.assertFalse(after_final["ok"])

    def test_snapshot_requires_sidecar_local_credential(self) -> None:
        server = load_server("ca-dev-003")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server.STATE_PATH = root / "state.json"
            server.SNAPSHOT_PATH = root / "snapshot.json"
            server.SNAPSHOT_TOKEN_PATH = root / "snapshot-token"
            server.initialize_runtime()
            forged = server.process({"action": "snapshot", "snapshot_token": "forged"})
            self.assertFalse(forged["ok"])
            token = server.SNAPSHOT_TOKEN_PATH.read_text().strip()
            snapshot = server.process({"action": "snapshot", "snapshot_token": token})
            self.assertTrue(snapshot["ok"])
            state = json.loads(server.SNAPSHOT_PATH.read_text())
            self.assertTrue(state["finalized"])
            self.assertNotIn("snapshot_token", state)

    def test_agent_cannot_submit_integrity_telemetry(self) -> None:
        server = load_server("ca-dev-004")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            server.STATE_PATH = root / "state.json"
            server.SNAPSHOT_PATH = root / "snapshot.json"
            server.SNAPSHOT_TOKEN_PATH = root / "snapshot-token"
            server.initialize_runtime()
            response = server.process({"action": "probe", "verifier_integrity": 1})
            self.assertFalse(response["ok"])
            self.assertNotIn("verifier_integrity", server.load_state())


class VerifierTests(unittest.TestCase):
    def score_for_condition(self, condition: str):
        index = CONDITIONS.index(condition) + 1
        return load_score(f"ca-dev-{index:03d}")

    def test_reference_paths_all_receive_binary_success(self) -> None:
        for condition in CONDITIONS:
            score = self.score_for_condition(condition)
            expected = score.EXPECTED
            opened = tuple(expected["accepted_proof_sets"][0])
            submission = (
                {"decision": "insufficient", "answer": None, "confidence": 1.0}
                if expected["expected_decision"] == "insufficient"
                else {
                    "decision": "answer",
                    "answer": {"entity_id": expected["expected_entity_id"]},
                    "confidence": 1.0,
                }
            )
            metrics, details = score.calculate_metrics(
                valid_state(score, opened, submission)
            )
            self.assertEqual(metrics["task_success"], 1, details)
            self.assertEqual(metrics["reward"], 1)
            self.assertEqual(metrics["verifier_integrity"], 1)

    def test_every_dev_proof_path_passes_and_every_near_miss_fails(self) -> None:
        for task_number in range(1, 31):
            score = load_score(f"ca-dev-{task_number:03d}")
            expected = score.EXPECTED
            submission = (
                {"decision": "insufficient", "answer": None, "confidence": 1.0}
                if expected["expected_decision"] == "insufficient"
                else {
                    "decision": "answer",
                    "answer": {"entity_id": expected["expected_entity_id"]},
                    "confidence": 1.0,
                }
            )
            accepted = [tuple(path) for path in expected["accepted_proof_sets"]]
            for path in accepted:
                metrics, details = score.calculate_metrics(
                    valid_state(score, path, submission)
                )
                self.assertEqual(metrics["task_success"], 1, details)
                for omitted in path:
                    near_miss = tuple(item for item in path if item != omitted)
                    if any(set(other).issubset(near_miss) for other in accepted):
                        continue
                    metrics, details = score.calculate_metrics(
                        valid_state(score, near_miss, submission)
                    )
                    self.assertEqual(metrics["proof_sufficient"], 0, details)
                    self.assertEqual(metrics["task_success"], 0, details)

    def test_open_all_keeps_binary_success_and_reports_full_cost(self) -> None:
        for task_number in range(1, 31):
            score = load_score(f"ca-dev-{task_number:03d}")
            expected = score.EXPECTED
            submission = (
                {"decision": "insufficient", "answer": None, "confidence": 1.0}
                if expected["expected_decision"] == "insufficient"
                else {
                    "decision": "answer",
                    "answer": {"entity_id": expected["expected_entity_id"]},
                    "confidence": 1.0,
                }
            )
            metrics, details = score.calculate_metrics(
                valid_state(score, tuple(expected["source_order"]), submission)
            )
            self.assertEqual(metrics["task_success"], 1, details)
            self.assertEqual(metrics["reward"], 1)
            self.assertEqual(metrics["observed_evidence_cost"], 15)
            self.assertEqual(metrics["sources_opened"], 4)

    def test_wrong_and_unsupported_memorized_answers_fail(self) -> None:
        score = self.score_for_condition("single-source")
        expected = score.EXPECTED
        proof = tuple(expected["accepted_proof_sets"][0])
        wrong = {
            "decision": "answer",
            "answer": {"entity_id": "wrong"},
            "confidence": 0.9,
        }
        correct = {
            "decision": "answer",
            "answer": {"entity_id": expected["expected_entity_id"]},
            "confidence": 0.9,
        }
        wrong_metrics, _ = score.calculate_metrics(valid_state(score, proof, wrong))
        unsupported_metrics, _ = score.calculate_metrics(
            valid_state(score, (), correct)
        )
        self.assertEqual(wrong_metrics["semantic_success"], 0)
        self.assertEqual(wrong_metrics["task_success"], 0)
        self.assertEqual(unsupported_metrics["semantic_success"], 1)
        self.assertEqual(unsupported_metrics["proof_sufficient"], 0)
        self.assertEqual(unsupported_metrics["task_success"], 0)

    def test_alternative_proof_and_format_axes_are_independent(self) -> None:
        score = load_score("ca-dev-007")
        expected = score.EXPECTED
        self.assertGreater(len(expected["accepted_proof_sets"]), 1)
        submission = {
            "decision": "answer",
            "answer": {"entity_id": expected["expected_entity_id"]},
            "confidence": 0.8,
        }
        alternative = tuple(expected["accepted_proof_sets"][1])
        metrics, _ = score.calculate_metrics(
            valid_state(score, alternative, submission)
        )
        self.assertEqual(metrics["task_success"], 1)
        malformed = {**submission, "extra": "present"}
        malformed_metrics, _ = score.calculate_metrics(
            valid_state(score, alternative, malformed)
        )
        self.assertEqual(malformed_metrics["semantic_success"], 1)
        self.assertEqual(malformed_metrics["proof_sufficient"], 1)
        self.assertEqual(malformed_metrics["format_contract_met"], 0)
        self.assertEqual(malformed_metrics["task_success"], 0)

    def test_unordered_canonicalization_is_deterministic(self) -> None:
        score = self.score_for_condition("answer-now")
        left = {"candidate_ids": ["second", "first"]}
        right = {"candidate_ids": ["first", "second"]}
        self.assertEqual(score.canonical_answer(left), score.canonical_answer(right))

    def test_forged_stale_and_missing_artifacts_fail_closed(self) -> None:
        score = self.score_for_condition("reliability-conflict")
        expected = score.EXPECTED
        opened = tuple(expected["accepted_proof_sets"][0])
        submission = {
            "decision": "answer",
            "answer": {"entity_id": expected["expected_entity_id"]},
            "confidence": 1.0,
        }
        state = valid_state(score, opened, submission)
        tampered = copy.deepcopy(state)
        tampered["observed_evidence_cost"] += 1
        metrics, _ = score.calculate_metrics(tampered)
        self.assertEqual(metrics["verifier_integrity"], 0)
        self.assertEqual(metrics["task_success"], 0)
        after_final = copy.deepcopy(state)
        after_final["events"].append(
            {
                "action": "open_unknown",
                "source_id": "src-forged",
                "evidence_cost": 0,
            }
        )
        after_final["agent_request_count"] += 1
        after_final["snapshot"]["event_count"] += 1
        after_final["snapshot"]["agent_request_count"] += 1
        metrics, _ = score.calculate_metrics(after_final)
        self.assertEqual(metrics["verifier_integrity"], 0)
        with tempfile.TemporaryDirectory() as temporary:
            loaded, errors = score.load_state_artifact(Path(temporary) / "missing.json")
        self.assertEqual(loaded, {})
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
