from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

SPEC = importlib.util.spec_from_file_location(
    "normalize_harbor_job_v2", TOOLS_DIR / "normalize_harbor_job_v2.py"
)
assert SPEC and SPEC.loader
NORMALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NORMALIZER)

V1_MANIFEST = (
    REPO_ROOT
    / "results"
    / "manifests"
    / "context-appetite-v0.2.1-model-pilot-3x-001.json"
)
V2_MANIFEST = V1_MANIFEST.with_suffix(".v2.json")
RAW_JOB = REPO_ROOT / "jobs" / "context-appetite-v0.2.1-model-pilot-3x-001"
V03_MANIFEST_DIR = REPO_ROOT / "results" / "manifests"
V03_MANIFESTS = (
    "context-appetite-v0.3.0-modal-t2-preflight-001.json",
    "context-appetite-v0.3.0-oracle-smoke-001.json",
    "context-appetite-v0.3.0-glm52-t2-canary-001.json",
    "context-appetite-v0.3.0-glm52-t2-eval-001.json",
)


class ClassificationTests(unittest.TestCase):
    def test_manifest_writer_is_atomic_and_private(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            NORMALIZER.write_json_atomic(path, {"version": 1})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text()), {"version": 1})
            NORMALIZER.write_json_atomic(path, {"version": 2})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text()), {"version": 2})
            self.assertEqual(
                [item for item in path.parent.iterdir() if item != path],
                [],
            )

    def test_deadline_preserves_provider_and_terminal_failure_stage(self) -> None:
        provider = {
            "exception_info": {
                "exception_type": "AgentTimeoutError",
                "exception_message": "timed out",
                "exception_traceback": "await self._query_llm via litellm",
            }
        }
        terminal = {
            "exception_info": {
                "exception_type": "AgentTimeoutError",
                "exception_message": "timed out",
                "exception_traceback": "capture_pane terminal output",
            }
        }
        self.assertEqual(
            NORMALIZER.execution_classification(provider)[:2],
            ("deadline", "provider_wait"),
        )
        self.assertEqual(
            NORMALIZER.execution_classification(terminal)[:2],
            ("deadline", "terminal_io"),
        )
        unknown = {
            "exception_info": {
                "exception_type": "AgentTimeoutError",
                "exception_message": "timed out",
            }
        }
        self.assertEqual(
            NORMALIZER.execution_classification(unknown)[:2],
            ("deadline", "agent_execution"),
        )

    def test_verifier_download_is_infrastructure_after_agent_completion(self) -> None:
        result = {
            "exception_info": {
                "exception_type": "DownloadVerifierDirError",
                "exception_message": "Failed to download verifier directory",
            },
            "agent_result": {"n_input_tokens": 1},
        }
        self.assertEqual(
            NORMALIZER.execution_classification(result)[:2],
            ("infrastructure_error", "verifier"),
        )
        self.assertEqual(NORMALIZER.verifier_status(result), "error")

    def test_verifier_integrity_is_required_and_fails_closed(self) -> None:
        missing = {"verifier_result": {"rewards": {"task_success": 1}}}
        missing_task_success = {
            "verifier_result": {"rewards": {"verifier_integrity": 1}}
        }
        failed = {
            "verifier_result": {"rewards": {"task_success": 0, "verifier_integrity": 0}}
        }
        self.assertEqual(NORMALIZER.verifier_status(missing), "error")
        self.assertEqual(NORMALIZER.verifier_status(missing_task_success), "error")
        self.assertEqual(NORMALIZER.verifier_status(failed), "fail")

    def test_failed_verifier_is_not_benchmark_valid(self) -> None:
        trial = {
            "execution_status": "completed",
            "verifier_status": "fail",
            "benchmark_valid": False,
            "strict_task_success": None,
            "domain_success": None,
            "diagnostics": {
                "recovered_strict_task_success": 0,
                "recovered_domain_success": 0,
            },
            "answer_observed": True,
            "harness_completion": "confirmed",
        }
        counts = NORMALIZER.build_counts([trial], 1)
        self.assertEqual(counts["completed"], 1)
        self.assertEqual(counts["benchmark_valid"], 0)
        self.assertEqual(counts["verifier_invalid"], 1)

    def test_unordered_insufficient_candidates_are_semantically_equal(self) -> None:
        state = {
            "answer": "INSUFFICIENT:second,first",
            "expected_answer": "INSUFFICIENT:first,second",
        }
        rewards = {
            "correctness": 0,
            "evidence_sufficient": 1,
            "task_success": 0,
            "verifier_integrity": 1,
        }
        semantic, method = NORMALIZER.semantic_outcome(rewards, state)
        proof = NORMALIZER.proof_outcome(rewards)
        formatting = NORMALIZER.format_outcome(rewards, state, semantic, proof)
        self.assertEqual((semantic, proof, formatting), ("pass", "pass", "fail"))
        self.assertEqual(method, "canonicalized_unordered")

    def test_no_observed_answer_cannot_be_a_semantic_pass(self) -> None:
        rewards = {"correctness": 1, "verifier_integrity": 1}
        self.assertEqual(
            NORMALIZER.semantic_outcome(rewards, {}), ("fail", "no_submission")
        )

    def test_signed_cost_delta_is_not_clamped(self) -> None:
        metrics = NORMALIZER.normalized_metrics(
            {
                "observed_evidence_cost": 2,
                "hindsight_minimum_cost": 4,
                "hindsight_cost_gap": 0,
                "selective_decision_correct": 1,
            },
            semantic="fail",
            proof="fail",
        )
        self.assertEqual(metrics["signed_cost_delta"], -2)
        self.assertIsNone(metrics["successful_excess_cost"])
        self.assertEqual(metrics["abstention_mode_match"], 1)
        self.assertNotIn("hindsight_cost_gap", metrics)
        self.assertNotIn("selective_decision_correct", metrics)

    def test_public_metrics_are_allowlisted_and_numeric(self) -> None:
        metrics = NORMALIZER.normalized_metrics(
            {
                "reward": 1,
                "task_success": 1,
                "hidden_expected_answer": "do-not-publish",
                "semantic_outcome": "pass",
                "policy_utility": float("inf"),
            },
            semantic="pass",
            proof="pass",
        )
        self.assertEqual(metrics["harbor_reward"], 1)
        self.assertEqual(metrics["verifier_task_success"], 1)
        self.assertNotIn("hidden_expected_answer", metrics)
        self.assertNotIn("semantic_outcome", metrics)
        self.assertNotIn("policy_utility", metrics)

    def test_command_and_failure_details_are_sanitized(self) -> None:
        command = NORMALIZER.sanitize_command(
            "/Users/example/.local/bin/harbor run --api-key secret "
            "OPENROUTER_TOKEN=another-secret"
        )
        self.assertEqual(
            command,
            "harbor run --api-key '[redacted]' 'OPENROUTER_TOKEN=[redacted]'",
        )
        result = {
            "exception_info": {
                "exception_type": "ProviderAuthenticationError",
                "exception_message": "secret-token-was-here",
            }
        }
        classification = NORMALIZER.execution_classification(result)
        self.assertEqual(classification[2], "ProviderAuthenticationError")
        self.assertNotIn("secret-token-was-here", classification[2])

    def test_invalid_verifier_cannot_become_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            trial_dir = Path(temp_dir) / "trial"
            trial_dir.mkdir()
            result_path = trial_dir / "result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "id": "trial-id",
                        "trial_name": "task__trial",
                        "task_name": "task",
                        "started_at": "2026-01-01T00:00:00+00:00",
                        "finished_at": "2026-01-01T00:00:01+00:00",
                        "config": {
                            "agent": {
                                "name": "terminus-2",
                                "model_name": "openrouter/test",
                                "kwargs": {},
                            }
                        },
                        "agent_result": {"metadata": {}},
                        "agent_info": {},
                        "verifier_result": {
                            "rewards": {
                                "task_success": 1,
                                "correctness": 1,
                                "evidence_sufficient": 1,
                                "verifier_integrity": 0,
                            }
                        },
                    }
                )
            )
            trial = NORMALIZER.build_trial(result_path, attempt=1, metadata={})
        self.assertEqual(trial["execution_status"], "infrastructure_error")
        self.assertEqual(trial["verifier_status"], "fail")
        self.assertFalse(trial["benchmark_valid"])
        self.assertIsNone(trial["strict_task_success"])
        self.assertIsNone(trial["domain_success"])
        self.assertIsNone(trial["diagnostics"]["recovered_strict_task_success"])
        self.assertIsNone(trial["diagnostics"]["recovered_domain_success"])
        counts = NORMALIZER.build_counts([trial], 1)
        self.assertEqual(counts["benchmark_valid"], 0)
        self.assertEqual(counts["strict_pass"], 0)
        self.assertEqual(counts["domain_pass"], 0)
        self.assertEqual(counts["infrastructure_error"], 1)


class ReleaseContractTests(unittest.TestCase):
    def test_sampling_seed_is_separate_and_reads_nested_llm_kwargs(self) -> None:
        self.assertEqual(
            NORMALIZER.sampling_seed({"kwargs": {"seed": 7}}),
            7,
        )
        self.assertEqual(
            NORMALIZER.sampling_seed(
                {"kwargs": {"llm_call_kwargs": {"seed": "release-1"}}}
            ),
            "release-1",
        )
        self.assertIsNone(
            NORMALIZER.sampling_seed({"kwargs": {"seed": None, "llm_call_kwargs": {}}})
        )

    def evaluation_metadata(self) -> tuple[argparse.Namespace, dict, dict, set[str]]:
        args = argparse.Namespace(implementation_version="0.3.0", run_kind="evaluation")
        release = {
            "name": "Instinct Bench: Context Appetite v0.3.0",
            "version": "0.3.0",
            "split": "eval",
            "generator_version": "0.3.0",
            "seed_commitment": "sha256:" + "a" * 64,
            "dataset_commitment": "sha256:" + "b" * 64,
            "package_set_commitment": "sha256:" + "c" * 64,
            "expected_task_count": 75,
            "expected_block_count": 15,
            "matrix_complete": True,
            "conditions": list(NORMALIZER.LOCKED_CONDITIONS),
        }
        tasks = {}
        index = 1
        for block in range(1, 16):
            for condition in NORMALIZER.LOCKED_CONDITIONS:
                tasks[f"ca-eval-{index:03d}"] = {
                    "condition": condition,
                    "scenario_block": f"ca-block-{block:03d}",
                    "instance_commitment": "sha256:" + f"{index:064x}",
                }
                index += 1
        return args, release, tasks, set(tasks)

    def test_official_release_requires_complete_matched_metadata(self) -> None:
        args, release, tasks, task_names = self.evaluation_metadata()
        NORMALIZER.validate_release_metadata(
            args, release=release, tasks=tasks, task_names=task_names
        )
        tasks.pop("ca-eval-075")
        with self.assertRaisesRegex(ValueError, "does not match the lock"):
            NORMALIZER.validate_release_metadata(
                args, release=release, tasks=tasks, task_names=task_names
            )

    def test_v031_release_metadata_matches_implementation_version(self) -> None:
        args, release, tasks, task_names = self.evaluation_metadata()
        args.implementation_version = "0.3.1"
        release["name"] = "Instinct Bench: Context Appetite v0.3.1"
        release["version"] = "0.3.1"
        release["generator_version"] = "0.3.1"
        NORMALIZER.validate_release_metadata(
            args, release=release, tasks=tasks, task_names=task_names
        )
        release["generator_version"] = "0.3.0"
        with self.assertRaisesRegex(ValueError, "match implementation_version"):
            NORMALIZER.validate_release_metadata(
                args, release=release, tasks=tasks, task_names=task_names
            )

    def test_release_metadata_rejects_private_or_unknown_fields(self) -> None:
        args, release, tasks, task_names = self.evaluation_metadata()
        release["master_seed"] = "private"
        with self.assertRaisesRegex(ValueError, "unexpected release fields"):
            NORMALIZER.validate_release_metadata(
                args, release=release, tasks=tasks, task_names=task_names
            )

    def test_v03_task_run_cannot_omit_release_metadata(self) -> None:
        args = argparse.Namespace(
            implementation_version="0.3.0", run_kind="model-canary"
        )
        with self.assertRaisesRegex(ValueError, "require --release-metadata"):
            NORMALIZER.validate_release_metadata(
                args, release={}, tasks={}, task_names={"ca-eval-001"}
            )

    def test_out_of_lock_and_overplanned_results_fail_closed(self) -> None:
        signature = ("task", "model")
        lock = {signature: [{}]}
        with self.assertRaisesRegex(ValueError, "absent from the job lock"):
            NORMALIZER.validate_job_matrix({("extra", "model"): []}, lock)
        with self.assertRaisesRegex(ValueError, "exceeds its planned count"):
            NORMALIZER.validate_job_matrix(
                {signature: [Path("one"), Path("two")]}, lock
            )

    def test_conflicting_task_digests_fail_closed(self) -> None:
        trials = [
            {"task": {"name": "task", "digest": "sha256:a"}},
            {"task": {"name": "task", "digest": "sha256:b"}},
        ]
        with self.assertRaisesRegex(ValueError, "conflicting digests"):
            NORMALIZER.validate_task_digests(trials)

    def test_terminus_confirmation_requires_two_completion_calls(self) -> None:
        result = {
            "config": {"agent": {"name": "terminus-2"}},
            "agent_result": {},
        }
        self.assertEqual(
            NORMALIZER.harness_completion_status(
                result,
                execution_status="completed",
                harness={"mark_task_complete_calls": 1},
            ),
            "unconfirmed",
        )
        self.assertEqual(
            NORMALIZER.harness_completion_status(
                result,
                execution_status="completed",
                harness={"mark_task_complete_calls": 2},
            ),
            "confirmed",
        )

    def test_model_call_latency_is_explicit(self) -> None:
        telemetry = NORMALIZER.model_call_telemetry(
            {"metadata": {"api_request_times_msec": [10, 20.5, -1, "secret"]}}
        )
        self.assertEqual(telemetry["count"], 2)
        self.assertEqual(telemetry["total_latency_ms"], 30.5)
        self.assertEqual(telemetry["mean_latency_ms"], 15.25)
        self.assertEqual(telemetry["max_latency_ms"], 20.5)


class HistoricalReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v1 = json.loads(V1_MANIFEST.read_text())
        cls.v2 = json.loads(V2_MANIFEST.read_text())

    def trial(self, name: str) -> dict[str, object]:
        return next(trial for trial in self.v2["trials"] if trial["trial_name"] == name)

    def test_v1_is_immutable_and_v2_records_its_digest(self) -> None:
        self.assertEqual(self.v1["schema_version"], "1.0")
        self.assertEqual(self.v2["schema_version"], "2.0")
        self.assertEqual(
            self.v2["derived_from"]["sha256"], NORMALIZER.sha256_file(V1_MANIFEST)
        )
        self.assertEqual(
            self.v2["normalizer"]["source_sha256"],
            NORMALIZER.sha256_file(
                TOOLS_DIR / "archive" / "normalize_harbor_job_v2_0_0.py"
            ),
        )

    def test_reconciles_69_67_68_and_recovered_diagnostics(self) -> None:
        counts = self.v2["counts"]
        self.assertEqual(counts["planned"], 75)
        self.assertEqual(counts["benchmark_valid"], 69)
        self.assertEqual(counts["strict_pass"], 67)
        self.assertEqual(counts["domain_pass"], 68)
        self.assertEqual(counts["deadline"], 5)
        self.assertEqual(counts["infrastructure_error"], 1)
        self.assertEqual(counts["verifier_invalid"], 0)
        self.assertEqual(counts["verifier_error"], 1)
        self.assertEqual(counts["verifier_evaluated"], 74)
        self.assertEqual(counts["recovered_strict_pass"], 69)
        self.assertEqual(counts["recovered_domain_pass"], 70)

    def test_deadline_with_answer_is_not_in_domain_denominator(self) -> None:
        trial = self.trial("deployment-outage__xJQn2qn")
        self.assertEqual(trial["execution_status"], "deadline")
        self.assertTrue(trial["answer_observed"])
        self.assertEqual(trial["semantic_outcome"], "pass")
        self.assertEqual(trial["proof_outcome"], "pass")
        self.assertIsNone(trial["strict_task_success"])
        self.assertIsNone(trial["domain_success"])
        self.assertEqual(trial["diagnostics"]["recovered_domain_success"], 1)

    def test_minimax_order_is_semantic_pass_but_strict_fail(self) -> None:
        trial = self.trial("insufficient-evidence__gn5UAJu")
        self.assertEqual(trial["execution_status"], "completed")
        self.assertEqual(trial["semantic_outcome"], "pass")
        self.assertEqual(trial["proof_outcome"], "pass")
        self.assertEqual(trial["format_outcome"], "fail")
        self.assertEqual(trial["strict_task_success"], 0)
        self.assertEqual(trial["domain_success"], 1)
        self.assertEqual(
            trial["diagnostics"]["semantic_resolution_method"],
            "canonicalized_unordered",
        )
        self.assertTrue(trial["diagnostics"]["semantic_exact_disagreement"])

    def test_verifier_download_preserves_answer_without_claiming_outcome(self) -> None:
        trial = self.trial("insufficient-evidence__ScoQwhN")
        self.assertEqual(trial["execution_status"], "infrastructure_error")
        self.assertEqual(trial["failure_stage"], "verifier")
        self.assertTrue(trial["answer_observed"])
        self.assertEqual(trial["verifier_status"], "error")
        self.assertEqual(trial["semantic_outcome"], "not_evaluated")
        self.assertEqual(trial["format_outcome"], "not_evaluated")
        self.assertEqual(trial["harness_completion"], "confirmed")

    def test_evidence_state_path_points_to_collected_sidecar_artifact(self) -> None:
        trial = self.trial("insufficient-evidence__gn5UAJu")
        self.assertTrue(
            trial["evidence_state_path"].endswith(
                "artifacts/evidence-artifacts/state.json"
            )
        )
        self.assertTrue(
            trial["verifier_details_path"].endswith("verifier/details.json")
        )

    def test_v2_removes_misleading_metric_names(self) -> None:
        serialized = json.dumps(self.v2)
        self.assertNotIn("hindsight_cost_gap", serialized)
        self.assertNotIn("selective_decision_correct", serialized)
        self.assertIn("signed_cost_delta", serialized)
        self.assertIn("abstention_mode_match", serialized)

    def test_v2_sanitizes_command_and_names_latency(self) -> None:
        self.assertTrue(self.v2["runner"]["command"].startswith("harbor run "))
        self.assertNotIn("/Users/", self.v2["runner"]["command"])
        trial = self.trial("answer-now__WxxTtNj")
        self.assertIn("trial_duration_seconds", trial["telemetry"])
        self.assertIn("model_calls", trial["telemetry"])
        self.assertGreater(trial["telemetry"]["model_calls"]["count"], 0)

    def test_schema_names_every_required_independent_axis(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "results" / "manifests" / "schema-v2.json").read_text()
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.v2)
        required = set(schema["$defs"]["trial"]["required"])
        self.assertTrue(
            {
                "execution_status",
                "failure_stage",
                "answer_observed",
                "verifier_status",
                "semantic_outcome",
                "proof_outcome",
                "format_outcome",
                "harness_completion",
                "benchmark_valid",
                "strict_task_success",
                "domain_success",
            }.issubset(required)
        )

    def test_schema_rejects_contradictory_benchmark_outcomes(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "results" / "manifests" / "schema-v2.json").read_text()
        )
        contradictory = json.loads(json.dumps(self.v2))
        trial = next(
            trial
            for trial in contradictory["trials"]
            if trial["strict_task_success"] == 1
        )
        trial["benchmark_valid"] = False
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(contradictory)

    def test_schema_rejects_v03_without_release_provenance(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "results" / "manifests" / "schema-v2.json").read_text()
        )
        missing_release = json.loads(json.dumps(self.v2))
        missing_release["benchmark"]["implementation_version"] = "0.3.0"
        missing_release["run_kind"] = "evaluation"
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(missing_release)

    @unittest.skipUnless(RAW_JOB.is_dir(), "raw Harbor job is local and ignored")
    def test_local_raw_job_rebuilds_the_committed_reconciliation(self) -> None:
        args = argparse.Namespace(
            job_dir=RAW_JOB,
            lifecycle=None,
            hub_url=None,
            run_kind="model-pilot",
            publication="review",
            supersedes=[],
            status_reason="Derived v2 classification; v1 remains immutable.",
            implementation_version="0.2.1",
            git_commit="77ef2de3667b22794db0b8d089256165dd9f11e1",
            command=self.v1["runner"]["command"],
            agent_egress="public",
            contract_visibility="private",
            derived_from=V1_MANIFEST,
            release_metadata=None,
        )
        rebuilt = NORMALIZER.build_manifest(args)
        self.assertEqual(rebuilt["counts"], self.v2["counts"])
        self.assertEqual(rebuilt["trials"], self.v2["trials"])


class ContextAppetiteV03ReleaseArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((V03_MANIFEST_DIR / "schema-v2.json").read_text())
        cls.validator = Draft202012Validator(cls.schema)
        cls.manifests = {
            name: json.loads((V03_MANIFEST_DIR / name).read_text())
            for name in V03_MANIFESTS
        }
        cls.release_index = json.loads(
            (
                V03_MANIFEST_DIR / "context-appetite-v0.3.0-release-index.json"
            ).read_text()
        )
        cls.canary_index = json.loads(
            (V03_MANIFEST_DIR / "context-appetite-v0.3.0-canary-index.json").read_text()
        )

    def test_all_committed_v03_manifests_validate(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        archived_normalizer = TOOLS_DIR / "archive" / "normalize_harbor_job_v2_0_0.py"
        for name, manifest in self.manifests.items():
            with self.subTest(name=name):
                self.validator.validate(manifest)
                self.assertEqual(manifest["normalizer"]["version"], "2.0.0")
                self.assertEqual(
                    manifest["normalizer"]["source_sha256"],
                    NORMALIZER.sha256_file(archived_normalizer),
                )

    def test_official_manifest_preserves_release_denominators(self) -> None:
        manifest = self.manifests["context-appetite-v0.3.0-glm52-t2-eval-001.json"]
        self.assertEqual(manifest["publication"], "eligible")
        self.assertEqual(
            manifest["benchmark"]["release_metadata_digest"],
            NORMALIZER.sha256_file(
                V03_MANIFEST_DIR / "context-appetite-v0.3.0-release-index.json"
            ),
        )
        self.assertEqual(
            manifest["counts"],
            {
                "planned": 75,
                "result_records": 75,
                "completed": 75,
                "benchmark_valid": 75,
                "strict_pass": 71,
                "domain_pass": 71,
                "deadline": 0,
                "infrastructure_error": 0,
                "verifier_invalid": 0,
                "verifier_error": 0,
                "cancelled": 0,
                "not_started": 0,
                "verifier_evaluated": 75,
                "recovered_strict_pass": 71,
                "recovered_domain_pass": 71,
                "answer_observed": 75,
                "harness_confirmed": 75,
            },
        )
        self.assertEqual(
            sum(trial["semantic_outcome"] == "pass" for trial in manifest["trials"]),
            75,
        )
        self.assertEqual(
            sum(trial["proof_outcome"] == "pass" for trial in manifest["trials"]),
            71,
        )

    def test_post_run_indices_are_truth_free_and_consistent(self) -> None:
        release = self.release_index["release"]
        tasks = self.release_index["tasks"]
        canary_tasks = self.canary_index["tasks"]
        public_release = json.loads(
            (REPO_ROOT / "evals/context-appetite/release-v0.3.0.json").read_text()
        )["release"]

        self.assertEqual(len(tasks), 75)
        self.assertEqual(
            set(canary_tasks),
            {"ca-eval-010", "ca-eval-016", "ca-eval-026", "ca-eval-050", "ca-eval-065"},
        )
        self.assertEqual(canary_tasks, {name: tasks[name] for name in canary_tasks})
        canary_manifest = self.manifests[
            "context-appetite-v0.3.0-glm52-t2-canary-001.json"
        ]
        self.assertEqual(
            canary_manifest["benchmark"]["release_metadata_digest"],
            NORMALIZER.sha256_file(
                V03_MANIFEST_DIR / "context-appetite-v0.3.0-canary-index.json"
            ),
        )
        for commitment in (
            "seed_commitment",
            "dataset_commitment",
            "package_set_commitment",
        ):
            self.assertEqual(release[commitment], public_release[commitment])

        serialized = json.dumps(self.release_index)
        for private_field in (
            '"expected_answer"',
            '"proof_paths"',
            '"source_contents"',
            '"master_seed"',
        ):
            self.assertNotIn(private_field, serialized)

        condition_counts = {
            condition: sum(task["condition"] == condition for task in tasks.values())
            for condition in NORMALIZER.LOCKED_CONDITIONS
        }
        block_counts = {
            block: sum(task["scenario_block"] == block for task in tasks.values())
            for block in {task["scenario_block"] for task in tasks.values()}
        }
        self.assertEqual(set(condition_counts.values()), {15})
        self.assertEqual(len(block_counts), 15)
        self.assertEqual(set(block_counts.values()), {5})

    def test_post_hoc_material_audit_preserves_frozen_result(self) -> None:
        official_name = "context-appetite-v0.3.0-glm52-t2-eval-001.json"
        official_path = V03_MANIFEST_DIR / official_name
        audit = json.loads(
            (
                REPO_ROOT
                / "results"
                / "reports"
                / "context-appetite-v0.3.0"
                / "material-proof-audit.json"
            ).read_text()
        )
        self.assertEqual(
            audit["derived_from"]["manifest_sha256"],
            NORMALIZER.sha256_file(official_path),
        )
        self.assertEqual(audit["scope"]["frozen_verifier_passes"], 71)
        self.assertEqual(
            audit["post_hoc_material_outcome"]["materially_supported_decisions"],
            74,
        )
        self.assertEqual(
            audit["post_hoc_material_outcome"]["genuine_unsupported_decisions"],
            1,
        )
        adjudications = {
            row["task_id"]: row["material_proof_outcome"]
            for row in audit["adjudications"]
        }
        self.assertEqual(
            adjudications,
            {
                "ca-eval-004": "pass",
                "ca-eval-006": "fail",
                "ca-eval-012": "pass",
                "ca-eval-016": "pass",
            },
        )
        official = self.manifests[official_name]
        self.assertEqual(official["counts"]["strict_pass"], 71)
        self.assertEqual(official["counts"]["domain_pass"], 71)


if __name__ == "__main__":
    unittest.main()
