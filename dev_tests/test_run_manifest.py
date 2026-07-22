from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_normalizer() -> ModuleType:
    path = REPO_ROOT / "tools" / "normalize_harbor_job.py"
    spec = importlib.util.spec_from_file_location("normalize_harbor_job", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NORMALIZER = load_normalizer()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def base_result() -> dict[str, Any]:
    return {
        "id": "trial-uuid",
        "task_name": "instinct-bench/answer-now",
        "trial_name": "answer-now__abc1234",
        "config": {
            "agent": {
                "name": "terminus-2",
                "model_name": "openrouter/example/model",
                "kwargs": {},
            }
        },
        "agent_info": {
            "name": "terminus-2",
            "version": "2.0.0",
            "model_info": {"name": "example/model", "provider": "openrouter"},
        },
        "agent_result": {
            "n_input_tokens": 100,
            "n_cache_tokens": 20,
            "n_output_tokens": 10,
            "cost_usd": 0.001,
        },
        "verifier_result": {
            "rewards": {
                "reward": 1,
                "task_success": 1,
                "verifier_integrity": 1,
                "observed_evidence_cost": 0,
                "evidence_payload_bytes": 0,
                "evidence_token_proxy": 0,
                "list_calls": 1,
                "status_calls": 0,
            }
        },
        "exception_info": None,
        "started_at": "2026-07-22T00:00:00Z",
        "finished_at": "2026-07-22T00:01:00Z",
        "environment_setup": {"started_at": "x", "finished_at": "y"},
        "agent_setup": {"started_at": "x", "finished_at": "y"},
        "agent_execution": {"started_at": "x", "finished_at": "y"},
        "verifier": {"started_at": "x", "finished_at": "y"},
    }


class ClassificationTests(unittest.TestCase):
    def test_valid_pass_and_task_failure_are_distinct(self) -> None:
        passed = base_result()
        failed = base_result()
        failed["verifier_result"]["rewards"]["task_success"] = 0
        failed["verifier_result"]["rewards"]["reward"] = 0
        self.assertEqual(
            NORMALIZER.classify_trial(passed),
            ("valid", "pass", "none", None),
        )
        self.assertEqual(
            NORMALIZER.classify_trial(failed),
            ("valid", "fail", "task", None),
        )

    def test_harness_provider_and_verifier_failures_are_infrastructure(self) -> None:
        harness = base_result()
        harness["agent_execution"] = None
        harness["verifier"] = None
        harness["exception_info"] = {
            "exception_type": "RuntimeError",
            "exception_message": "tmux not found",
        }
        provider = base_result()
        provider["verifier"] = None
        provider["exception_info"] = {
            "exception_type": "ProviderError",
            "exception_message": "OpenRouter connection failed",
        }
        verifier = base_result()
        verifier["exception_info"] = {
            "exception_type": "VerifierOutputParseError",
            "exception_message": "bad reward",
        }
        self.assertEqual(NORMALIZER.classify_trial(harness)[2], "harness-setup")
        self.assertEqual(NORMALIZER.classify_trial(provider)[2], "model-provider")
        self.assertEqual(NORMALIZER.classify_trial(verifier)[2], "verifier")

    def test_agent_timeout_is_a_valid_task_failure(self) -> None:
        timeout = base_result()
        timeout["exception_info"] = {
            "exception_type": "AgentTimeoutError",
            "exception_message": "agent exceeded the task deadline",
        }
        self.assertEqual(
            NORMALIZER.classify_trial(timeout)[:3],
            ("valid", "fail", "agent"),
        )


class ManifestBuildTests(unittest.TestCase):
    def test_builds_auditable_manifest_from_harbor_020_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            job_dir = Path(temporary_directory) / "canary"
            write_json(
                job_dir / "result.json",
                {
                    "id": "job-uuid",
                    "started_at": "2026-07-22T00:00:00Z",
                    "finished_at": "2026-07-22T00:01:00Z",
                },
            )
            write_json(
                job_dir / "lock.json",
                {
                    "harbor": {"version": "0.20.0"},
                    "n_concurrent_trials": 1,
                    "trials": [
                        {
                            "task": {
                                "name": "answer-now",
                                "digest": "sha256:task",
                            },
                            "agent": {
                                "name": "terminus-2",
                                "model_name": "openrouter/example/model",
                                "skills": [],
                                "kwargs": {},
                                "extra_allowed_hosts": [],
                            },
                            "environment": {
                                "type": "modal",
                                "kwargs": {},
                            },
                        }
                    ],
                },
            )
            trial_dir = job_dir / "answer-now__abc1234"
            write_json(trial_dir / "result.json", base_result())
            write_json(
                trial_dir / "verifier" / "details.json",
                {"source_sequence": []},
            )
            write_json(
                trial_dir / "agent" / "trajectory.json",
                {
                    "steps": [
                        {
                            "source": "user",
                            "message": "Harness prompt\n\nTask Description:\nTask text",
                        }
                    ]
                },
            )
            args = argparse.Namespace(
                job_dir=job_dir,
                lifecycle=None,
                hub_url=None,
                run_kind="model-canary",
                publication="scratch",
                supersedes=[],
                status_reason=None,
                implementation_version="0.2.1",
                git_commit="deadbeef",
                command="harbor run ...",
                agent_egress="public",
                contract_visibility="private",
            )
            manifest = NORMALIZER.build_manifest(args)

        self.assertEqual(manifest["counts"]["planned"], 1)
        self.assertEqual(manifest["counts"]["valid"], 1)
        self.assertEqual(manifest["counts"]["task_pass"], 1)
        self.assertEqual(manifest["costs_usd"]["model"], 0.001)
        self.assertEqual(manifest["runner"]["model"], "openrouter/example/model")
        self.assertTrue(manifest["runner"]["prompt_digest"].startswith("sha256:"))
        trial = manifest["trials"][0]
        self.assertEqual(trial["trial_name"], "answer-now__abc1234")
        self.assertEqual(trial["attempt"], 1)
        self.assertEqual(trial["telemetry"]["model_tokens"]["cached_input"], 20)
        self.assertTrue(trial["trajectory_path"].endswith("trajectory.json"))


if __name__ == "__main__":
    unittest.main()
