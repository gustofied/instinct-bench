from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
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
from instinct_bench.context_appetite.semantic_audit import (  # noqa: E402
    EVENT_PATTERN,
    SemanticAuditError,
    audit_dataset,
    audit_task_package,
)


DEV_DIR = REPO_ROOT / "evals" / "context-appetite" / "dev"
OFFICIAL_RUN = REPO_ROOT / "evals" / "context-appetite" / "official-run-v0.3.1.json"
V031_RELEASE = REPO_ROOT / "evals" / "context-appetite" / "release-v0.3.1.json"
V031_ORACLE_GATE = (
    REPO_ROOT / "results" / "reports" / "context-appetite-v0.3.1" / "oracle-gate.json"
)
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


def load_release_validator():
    path = REPO_ROOT / "tools" / "validate_context_appetite_release.py"
    spec = importlib.util.spec_from_file_location(
        "validate_context_appetite_release", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_locked_runner():
    path = REPO_ROOT / "tools" / "run_context_appetite_v031.py"
    spec = importlib.util.spec_from_file_location("run_context_appetite_v031", path)
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
        self.assertEqual(generator.RELEASE_VERSION, "0.3.1")
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

    def test_official_run_protocol_is_locked_and_truth_free(self) -> None:
        config = json.loads(OFFICIAL_RUN.read_text())
        self.assertEqual(config["schema_version"], "1.1")
        benchmark = config["benchmark"]
        commitment = json.loads(V031_RELEASE.read_text())["release"]
        for field in (
            "seed_commitment",
            "dataset_commitment",
            "package_set_commitment",
        ):
            self.assertEqual(benchmark[field], commitment[field])
        self.assertRegex(benchmark["task_release_commit"], r"^[0-9a-f]{7,40}$")
        self.assertEqual(benchmark["contract_visibility_at_run"], "unpublished")

        agent = config["agent"]
        self.assertEqual(agent["model"], "openrouter/z-ai/glm-5.2")
        self.assertEqual(agent["harness"], "terminus-2")
        self.assertEqual(agent["harness_version"], "2.0.0")
        self.assertRegex(agent["prompt_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(agent["sampling"], {"temperature": 0, "seed": None})
        self.assertEqual(
            agent["provider_request"],
            {
                "router": "openrouter",
                "endpoint_tag": "z-ai/fp8",
                "allow_fallbacks": False,
                "require_parameters": True,
            },
        )
        self.assertEqual(agent["skills"], [])

        execution = config["execution"]
        self.assertEqual(execution["attempts_per_task"], 1)
        self.assertEqual(execution["agent_timeout_seconds"], 300)
        self.assertEqual(execution["concurrency"], 4)
        self.assertEqual(execution["agent_concurrency"], 4)
        self.assertEqual(execution["max_retries"], 0)
        self.assertFalse(execution["selective_retries"])
        self.assertEqual(execution["file_umask"], "077")
        self.assertEqual(execution["evaluation"]["expected_trials"], 75)
        self.assertEqual(execution["canary"]["expected_trials"], 5)
        self.assertEqual(len(set(execution["canary"]["task_ids"])), 5)
        self.assertNotIn('"condition"', OFFICIAL_RUN.read_text())
        self.assertNotIn('"scenario_block"', OFFICIAL_RUN.read_text())

    def test_locked_runner_builds_exact_non_uploading_protocol(self) -> None:
        runner = load_locked_runner()
        lock = json.loads(OFFICIAL_RUN.read_text())
        command = runner.build_command(
            lock,
            phase="canary",
            harbor_executable="/usr/bin/harbor",
        )
        self.assertEqual(command[:3], ["/usr/bin/harbor", "run", "-p"])
        self.assertEqual(command.count("-i"), 5)
        self.assertIn("openrouter/z-ai/glm-5.2", command)
        self.assertIn("terminus-2", command)
        self.assertIn("temperature=0", command)
        self.assertIn("modal_vm_runtime=true", command)
        routing_arg = next(
            value for value in command if value.startswith("llm_call_kwargs=")
        )
        self.assertEqual(
            json.loads(routing_arg.split("=", 1)[1]),
            {
                "extra_body": {
                    "provider": {
                        "order": ["z-ai/fp8"],
                        "allow_fallbacks": False,
                        "require_parameters": True,
                    }
                }
            },
        )
        self.assertNotIn("--upload", command)
        self.assertNotIn("--public", command)
        self.assertNotIn("--private", command)

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

    def test_insufficient_proof_contract_matches_plain_abstention(self) -> None:
        for spec in self.dev_specs + self.eval_specs:
            if spec.condition != "insufficient-evidence":
                continue
            self.assertEqual(len(spec.accepted_proof_sets), 1)
            proof_sources = {
                spec.source_map[source_id].authority_class
                for source_id in spec.accepted_proof_sets[0]
            }
            self.assertEqual(
                proof_sources,
                {"signed-operational-log", "independent-audit-record"},
            )
            self.assertEqual(len(spec.accepted_proof_sets[0]), 2)

    def test_instruction_does_not_anchor_confidence(self) -> None:
        for spec in self.dev_specs + self.eval_specs:
            text = generator.instruction(spec)
            self.assertIn("--confidence PROBABILITY", text)
            self.assertNotIn("--confidence 0.84", text)

    def test_instruction_states_plural_tool_and_material_support_contract(
        self,
    ) -> None:
        for spec in self.dev_specs + self.eval_specs:
            text = generator.instruction(spec)
            self.assertIn("open sources\none at a time", text)
            self.assertNotIn("open one\nsource", text)
            self.assertIn("event-to-entity link", text)
            self.assertIn("event-specific ambiguity", text)
            self.assertIn("corpus is complete", text)

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
            for path in (output_dir, *output_dir.rglob("*")):
                mode = path.stat().st_mode & 0o777
                if path.is_dir():
                    expected_mode = 0o755 if path.name == "solution" else 0o700
                    self.assertEqual(mode, expected_mode, path)
                elif mode & 0o111:
                    self.assertEqual(mode, 0o755, path)
                else:
                    self.assertEqual(mode, 0o600, path)

    def test_committed_v031_release_commitment_is_truth_free(self) -> None:
        commitment = json.loads(V031_RELEASE.read_text())
        self.assertEqual(commitment["schema_version"], "1.0")
        self.assertNotIn("tasks", commitment)
        release = commitment["release"]
        self.assertEqual(
            release,
            {
                "name": "Instinct Bench: Context Appetite v0.3.1",
                "version": "0.3.1",
                "split": "eval",
                "generator_version": "0.3.1",
                "seed_commitment": release["seed_commitment"],
                "dataset_commitment": release["dataset_commitment"],
                "package_set_commitment": release["package_set_commitment"],
                "expected_task_count": 75,
                "expected_block_count": 15,
            },
        )
        for key in (
            "seed_commitment",
            "dataset_commitment",
            "package_set_commitment",
        ):
            self.assertRegex(release[key], r"^sha256:[0-9a-f]{64}$")

    def test_v031_oracle_gate_is_aggregate_and_commitment_bound(self) -> None:
        gate = json.loads(V031_ORACLE_GATE.read_text())
        encoded = json.dumps(gate, sort_keys=True)
        self.assertNotIn("ca-eval-", encoded)
        dev_release = json.loads((DEV_DIR / "release-metadata.json").read_text())[
            "release"
        ]
        private_release = json.loads(V031_RELEASE.read_text())["release"]
        for key in (
            "seed_commitment",
            "dataset_commitment",
            "package_set_commitment",
        ):
            self.assertEqual(gate["public_release"][key], dev_release[key])
            self.assertEqual(gate["private_release"][key], private_release[key])
        self.assertEqual(gate["public_counts"]["planned"], 30)
        self.assertEqual(gate["public_counts"]["task_success"], 30)
        self.assertEqual(gate["public_counts"]["runtime_checks_passed"], 150)
        self.assertEqual(gate["private_counts"]["planned"], 75)
        self.assertEqual(gate["private_counts"]["task_success"], 75)
        self.assertEqual(gate["private_counts"]["runtime_checks_passed"], 375)
        self.assertFalse(gate["privacy"]["raw_jobs_committed"])
        self.assertFalse(gate["privacy"]["private_release_metadata_committed"])
        self.assertFalse(gate["privacy"]["normalized_trial_manifests_committed"])

    def test_private_secret_file_must_not_be_group_or_world_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "release.secret"
            path.write_bytes(EVAL_SECRET)
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                generator.read_private_secret(path)
            path.chmod(0o600)
            self.assertEqual(generator.read_private_secret(path), EVAL_SECRET)

    def test_private_release_validator_rejects_symlinks(self) -> None:
        validator = load_release_validator()
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "eval"
            generator.generate(
                split="eval",
                secret=EVAL_SECRET,
                output_dir=output_dir,
                replace=False,
            )
            link = output_dir / "linked-readme"
            link.symlink_to(output_dir / "README.md")
            with self.assertRaisesRegex(ValueError, "must not contain symlinks"):
                validator.validate_permissions(output_dir)

    def test_package_digest_commits_to_executable_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "dev"
            generator.generate(
                split="dev",
                secret=generator.DEV_SECRET,
                output_dir=output_dir,
                replace=False,
            )
            task_dir = output_dir / self.dev_specs[0].task_id
            solve_path = task_dir / "solution" / "solve.sh"
            executable_digest = generator.task_digest(task_dir)
            solve_path.chmod(0o644)
            self.assertNotEqual(generator.task_digest(task_dir), executable_digest)
            solve_path.chmod(0o755)
            executable_digest = generator.task_digest(task_dir)
            solve_path.parent.chmod(0o700)
            self.assertNotEqual(generator.task_digest(task_dir), executable_digest)

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

    def test_authority_aware_sequential_reader_covers_all_tasks_at_lower_cost(
        self,
    ) -> None:
        sequential = self.summary["authority-aware-sequential"]
        open_all = self.summary["open-all"]
        self.assertEqual(sequential["optimistic_successes"], 75)
        self.assertLess(
            sequential["mean_evidence_cost"], open_all["mean_evidence_cost"]
        )


class IndependentSemanticAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.eval_dir = Path(cls.temporary.name) / "eval"
        generator.generate(
            split="eval",
            secret=EVAL_SECRET,
            output_dir=cls.eval_dir,
            replace=False,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_all_public_and_eval_packages_have_materially_exact_proof_sets(
        self,
    ) -> None:
        self.assertEqual(len(audit_dataset(DEV_DIR)), 30)
        self.assertEqual(len(audit_dataset(self.eval_dir)), 75)

    def copy_task(self, task_id: str, destination: Path) -> Path:
        task_dir = destination / task_id
        shutil.copytree(DEV_DIR / task_id, task_dir)
        return task_dir

    def test_audit_rejects_missing_material_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            task_dir = self.copy_task("ca-dev-002", Path(temporary))
            expected = json.loads((task_dir / "tests" / "expected.json").read_text())
            proof_id = expected["accepted_proof_sets"][0][0]
            task_data_path = (
                task_dir / "environment" / "evidence-sidecar" / "task_data.json"
            )
            task_data = json.loads(task_data_path.read_text())
            task_data["sources"][proof_id]["content"] = (
                "The record is present but contains no attribution claim."
            )
            generator.write_json(task_data_path, task_data)
            with self.assertRaisesRegex(
                SemanticAuditError, "do not match verifier paths"
            ):
                audit_task_package(task_dir)

    def test_audit_rejects_unintended_shortcut(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            task_dir = self.copy_task("ca-dev-003", Path(temporary))
            expected = json.loads((task_dir / "tests" / "expected.json").read_text())
            expected_id = expected["expected_entity_id"]
            task_data_path = (
                task_dir / "environment" / "evidence-sidecar" / "task_data.json"
            )
            task_data = json.loads(task_data_path.read_text())
            event_id = EVENT_PATTERN.search(task_data["question"]).group()
            accepted = {
                source_id
                for path in expected["accepted_proof_sets"]
                for source_id in path
            }
            shortcut_id = next(
                source_id
                for source_id in task_data["sources"]
                if source_id not in accepted
            )
            task_data["sources"][shortcut_id].update(
                {
                    "authority_class": "primary-control-record",
                    "declared_reliability": 0.99,
                    "content": (
                        f"The signed decision for {event_id} names {expected_id} "
                        "as the controlling entity."
                    ),
                }
            )
            generator.write_json(task_data_path, task_data)
            with self.assertRaisesRegex(
                SemanticAuditError, "do not match verifier paths"
            ):
                audit_task_package(task_dir)

    def test_audit_rejects_incomplete_abstention_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            task_dir = self.copy_task("ca-dev-004", Path(temporary))
            task_data_path = (
                task_dir / "environment" / "evidence-sidecar" / "task_data.json"
            )
            task_data = json.loads(task_data_path.read_text())
            completeness_id = next(
                source_id
                for source_id, source in task_data["sources"].items()
                if source["authority_class"] == "independent-audit-record"
            )
            task_data["sources"][completeness_id]["content"] = (
                "The audit covers routine bookkeeping only."
            )
            generator.write_json(task_data_path, task_data)
            with self.assertRaisesRegex(
                SemanticAuditError, "do not match verifier paths"
            ):
                audit_task_package(task_dir)

    def test_audit_rejects_unaccepted_non_binding_abstention_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            task_dir = self.copy_task("ca-dev-004", Path(temporary))
            expected = json.loads((task_dir / "tests" / "expected.json").read_text())
            accepted = {
                source_id
                for path in expected["accepted_proof_sets"]
                for source_id in path
            }
            task_data_path = (
                task_dir / "environment" / "evidence-sidecar" / "task_data.json"
            )
            task_data = json.loads(task_data_path.read_text())
            event_id = EVENT_PATTERN.search(task_data["question"]).group()
            shortcut_id = next(
                source_id
                for source_id, source in task_data["sources"].items()
                if source_id not in accepted
                and source["authority_class"] == "primary-control-record"
            )
            task_data["sources"][shortcut_id]["content"] = (
                "A valid control action occurred, but the record does not bind "
                f"that action uniquely to {event_id}."
            )
            generator.write_json(task_data_path, task_data)
            with self.assertRaisesRegex(
                SemanticAuditError, "do not match verifier paths"
            ):
                audit_task_package(task_dir)


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

    def test_insufficient_proof_uses_ambiguity_and_completeness(self) -> None:
        score = self.score_for_condition("insufficient-evidence")
        task_data = json.loads(
            (
                DEV_DIR
                / "ca-dev-004"
                / "environment"
                / "evidence-sidecar"
                / "task_data.json"
            ).read_text()
        )
        by_authority = defaultdict(list)
        for source_id, source in task_data["sources"].items():
            by_authority[source["authority_class"]].append(source_id)
        material_path = tuple(score.EXPECTED["accepted_proof_sets"][0])
        self.assertEqual(
            set(material_path),
            {
                by_authority["signed-operational-log"][0],
                by_authority["independent-audit-record"][0],
            },
        )
        submission = {
            "decision": "insufficient",
            "answer": None,
            "confidence": 0.9,
        }
        material_metrics, _ = score.calculate_metrics(
            valid_state(score, material_path, submission)
        )
        self.assertEqual(material_metrics["task_success"], 1)

        missing_completeness = tuple(
            by_authority["primary-control-record"]
            + by_authority["signed-operational-log"]
        )
        unsupported_metrics, _ = score.calculate_metrics(
            valid_state(score, missing_completeness, submission)
        )
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
