#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shlex
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import normalize_harbor_job as v1


SCHEMA_VERSION = "2.0"
NORMALIZER_VERSION = "2.0.0"
LOCKED_CONDITIONS = (
    "answer-now",
    "single-source",
    "complementary-evidence",
    "insufficient-evidence",
    "reliability-conflict",
)
V02_CONDITIONS = {
    "answer-now": "answer-now",
    "deployment-outage": "single-source",
    "complementary-evidence": "complementary-evidence",
    "insufficient-evidence": "insufficient-evidence",
    "unreliable-or-conflicting-evidence": "reliability-conflict",
}
PUBLIC_METRIC_NAMES = {
    "abstained": "abstained",
    "agent_requests": "agent_requests",
    "confidence": "confidence",
    "correctness": "correctness",
    "cost_score": "cost_score",
    "duplicate_open_attempts": "duplicate_open_attempts",
    "evidence_payload_bytes": "evidence_payload_bytes",
    "evidence_sufficient": "evidence_sufficient",
    "evidence_token_proxy": "evidence_token_proxy",
    "format_contract_met": "format_contract_met",
    "format_outcome": "format_outcome",
    "format_success": "format_success",
    "hindsight_minimum_cost": "hindsight_minimum_cost",
    "list_calls": "list_calls",
    "observed_evidence_cost": "observed_evidence_cost",
    "policy_utility": "policy_utility",
    "proof_outcome": "proof_outcome",
    "proof_sufficient": "proof_sufficient",
    "reward": "harbor_reward",
    "selective_decision_correct": "abstention_mode_match",
    "semantic_outcome": "semantic_outcome",
    "semantic_success": "semantic_success",
    "sources_opened": "sources_opened",
    "sources_outside_hindsight_minimum": "sources_outside_hindsight_minimum",
    "status_calls": "status_calls",
    "supported_abstention": "supported_abstention",
    "task_success": "verifier_task_success",
    "unjustified_abstention": "unjustified_abstention",
    "unknown_source_attempts": "unknown_source_attempts",
    "verifier_integrity": "verifier_integrity",
    "zero_cost_tool_calls": "zero_cost_tool_calls",
}
SENSITIVE_COMMAND_FRAGMENTS = ("api-key", "apikey", "password", "secret", "token")


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256_commitment(value: object) -> bool:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or len(value) != 71
    ):
        return False
    try:
        int(value.removeprefix("sha256:"), 16)
    except ValueError:
        return False
    return True


def metric_outcome(value: object) -> str | None:
    if value in (1, 1.0, True, "pass"):
        return "pass"
    if value in (0, 0.0, False, "fail"):
        return "fail"
    if value == "not_evaluated":
        return "not_evaluated"
    return None


def finite_number(value: object) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return value if math.isfinite(value) else None


def binary_metric(value: object) -> int | None:
    outcome = metric_outcome(value)
    if outcome == "pass":
        return 1
    if outcome == "fail":
        return 0
    return None


def canonical_answer(value: object) -> object:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("INSUFFICIENT:"):
            candidates = stripped.split(":", 1)[1]
            return (
                "INSUFFICIENT",
                tuple(sorted(part.strip() for part in candidates.split(","))),
            )
        return stripped
    if isinstance(value, dict):
        normalized: list[tuple[str, object]] = []
        for key, item in sorted(value.items()):
            canonical = canonical_answer(item)
            if key in {"candidate_ids", "candidates", "entity_ids"} and isinstance(
                canonical, tuple
            ):
                canonical = tuple(sorted(canonical))
            normalized.append((key, canonical))
        return tuple(normalized)
    if isinstance(value, list):
        return tuple(canonical_answer(item) for item in value)
    return value


def evidence_state(trial_dir: Path) -> tuple[dict[str, Any], Path | None]:
    details_path = trial_dir / "verifier" / "details.json"
    details = v1.optional_json(details_path)
    state_path = trial_dir / "artifacts" / "evidence-artifacts" / "state.json"
    artifact_state = v1.optional_json(state_path)
    if details or artifact_state:
        merged = dict(artifact_state)
        merged.update(details)
        return merged, state_path if state_path.is_file() else None
    return {}, None


def answer_from_state(state: dict[str, Any]) -> object:
    if "answer" in state:
        return state.get("answer")
    submission = state.get("submission")
    if isinstance(submission, dict):
        return submission
    snapshot = state.get("snapshot")
    if isinstance(snapshot, dict):
        return snapshot.get("answer") or snapshot.get("submission")
    return None


def answer_was_observed(state: dict[str, Any]) -> bool:
    answer = answer_from_state(state)
    return answer not in (None, "", {})


def semantic_outcome(rewards: dict[str, Any], state: dict[str, Any]) -> tuple[str, str]:
    if not answer_was_observed(state):
        return ("fail", "no_submission") if rewards else ("not_evaluated", "none")
    for key in ("semantic_outcome", "semantic_success"):
        outcome = metric_outcome(rewards.get(key))
        if outcome is not None:
            return outcome, "verifier_explicit"

    answer = answer_from_state(state)
    expected = state.get("expected_answer")
    if answer not in (None, "", {}) and expected not in (None, "", {}):
        if answer == expected:
            return "pass", "exact_match"
        if canonical_answer(answer) == canonical_answer(expected):
            return "pass", "canonicalized_unordered"

    correctness = metric_outcome(rewards.get("correctness"))
    if correctness is not None:
        return correctness, "verifier_correctness"
    return "not_evaluated", "none"


def proof_outcome(rewards: dict[str, Any]) -> str:
    for key in ("proof_outcome", "proof_sufficient", "evidence_sufficient"):
        outcome = metric_outcome(rewards.get(key))
        if outcome is not None:
            return outcome
    return "not_evaluated"


def format_outcome(
    rewards: dict[str, Any],
    state: dict[str, Any],
    semantic: str,
    proof: str,
) -> str:
    if not rewards:
        return "not_evaluated"
    for key in ("format_outcome", "format_contract_met", "format_success"):
        outcome = metric_outcome(rewards.get(key))
        if outcome is not None:
            return outcome

    if not answer_was_observed(state):
        return "not_evaluated"
    if metric_outcome(rewards.get("correctness")) == "pass":
        return "pass"
    if semantic == "pass" and proof == "pass":
        # Historical v0.2.1 used exact string order as an all-pass requirement.
        return "fail"
    return "pass"


def verifier_status(result: dict[str, Any]) -> str:
    rewards = (result.get("verifier_result") or {}).get("rewards")
    if isinstance(rewards, dict):
        integrity = metric_outcome(rewards.get("verifier_integrity"))
        if integrity == "fail":
            return "fail"
        if integrity != "pass" or binary_metric(rewards.get("task_success")) is None:
            return "error"
        return "pass"
    exception = result.get("exception_info") or {}
    exception_type = str(exception.get("exception_type", ""))
    if "Verifier" in exception_type or exception_type in {
        "DownloadVerifierDirError",
        "VerifierOutputParseError",
    }:
        return "error"
    return "not_run"


def timeout_stage(exception: dict[str, Any]) -> str:
    trace = " ".join(
        str(exception.get(key, ""))
        for key in ("exception_type", "exception_message", "exception_traceback")
    ).lower()
    if any(
        marker in trace
        for marker in ("_query_llm", "litellm", "openrouter", "aiohttp", "httpx")
    ):
        return "provider_wait"
    if any(
        marker in trace
        for marker in ("tmux", "terminal", "capture_pane", "mark_task_complete")
    ):
        return "terminal_io"
    return "agent_execution"


def infrastructure_stage(exception: dict[str, Any]) -> str:
    text = " ".join(
        str(exception.get(key, ""))
        for key in ("exception_type", "exception_message", "exception_traceback")
    ).lower()
    if "verifier" in text:
        return "verifier"
    if any(marker in text for marker in ("artifact", "collect", "snapshot")):
        return "collection"
    if any(
        marker in text
        for marker in (
            "openrouter",
            "provider",
            "rate limit",
            "authentication",
            "modelnotfound",
            "apiusagelimit",
        )
    ):
        return "provider_wait"
    if any(marker in text for marker in ("tmux", "terminal", "capture_pane")):
        return "terminal_io"
    return "sandbox"


def execution_classification(
    result: dict[str, Any],
) -> tuple[str, str | None, str | None]:
    exception = result.get("exception_info")
    if not exception:
        if result.get("config", {}).get("install_only") is True:
            setup = result.get("agent_setup") or {}
            if not (setup.get("started_at") and setup.get("finished_at")):
                return (
                    "infrastructure_error",
                    "sandbox",
                    "Install-only setup did not finish.",
                )
        if result.get("config", {}).get("install_only") is not True:
            rewards = (result.get("verifier_result") or {}).get("rewards")
            if not isinstance(rewards, dict):
                return (
                    "infrastructure_error",
                    "verifier",
                    "Verifier returned no reward dictionary.",
                )
        return "completed", None, None

    exception_type = str(exception.get("exception_type", "UnknownError"))
    message = str(exception.get("exception_message", ""))
    lowered = f"{exception_type} {message}".lower()
    if "cancel" in lowered:
        return "cancelled", None, "cancelled"
    if exception_type == "AgentTimeoutError":
        return "deadline", timeout_stage(exception), exception_type
    return "infrastructure_error", infrastructure_stage(exception), exception_type


def sanitize_command(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        return "[invalid command]"
    if not parts:
        return ""
    parts[0] = Path(parts[0]).name
    sanitized: list[str] = []
    redact_next = False
    for part in parts:
        if redact_next:
            sanitized.append("[redacted]")
            redact_next = False
            continue
        if Path(part).name == "harbor":
            part = "harbor"
        lowered = part.lower().lstrip("-")
        if "=" in part:
            key, _value = part.split("=", 1)
            if any(fragment in key.lower() for fragment in SENSITIVE_COMMAND_FRAGMENTS):
                sanitized.append(f"{key}=[redacted]")
                continue
        if part.startswith("-") and any(
            fragment in lowered for fragment in SENSITIVE_COMMAND_FRAGMENTS
        ):
            sanitized.append(part)
            redact_next = True
            continue
        if "=" in part:
            key, _value = part.split("=", 1)
            if any(fragment in key.lower() for fragment in SENSITIVE_COMMAND_FRAGMENTS):
                sanitized.append(f"{key}=[redacted]")
                continue
        sanitized.append(part)
    return shlex.join(sanitized)


def duration_seconds(result: dict[str, Any]) -> float | None:
    started = result.get("started_at")
    finished = result.get("finished_at")
    if not isinstance(started, str) or not isinstance(finished, str):
        return None
    try:
        return (
            datetime.fromisoformat(finished) - datetime.fromisoformat(started)
        ).total_seconds()
    except ValueError:
        return None


def normalized_metrics(
    rewards: dict[str, Any],
    *,
    semantic: str,
    proof: str,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for source_name, public_name in PUBLIC_METRIC_NAMES.items():
        value = rewards.get(source_name)
        public_value = finite_number(value)
        if source_name in rewards and (value is None or public_value is not None):
            metrics[public_name] = public_value

    observed = rewards.get("observed_evidence_cost")
    minimum = rewards.get("hindsight_minimum_cost")
    signed_delta: int | float | None = None
    observed_number = finite_number(observed)
    minimum_number = finite_number(minimum)
    if observed_number is not None and minimum_number is not None:
        signed_delta = observed_number - minimum_number
    metrics["signed_cost_delta"] = signed_delta
    metrics["successful_excess_cost"] = (
        signed_delta if semantic == "pass" and proof == "pass" else None
    )
    return metrics


def model_call_telemetry(agent_result: dict[str, Any]) -> dict[str, Any]:
    metadata = agent_result.get("metadata") or {}
    raw_times = metadata.get("api_request_times_msec")
    times = (
        [
            float(value)
            for value in raw_times
            if finite_number(value) is not None and value >= 0
        ]
        if isinstance(raw_times, list)
        else []
    )
    return {
        "count": len(times),
        "total_latency_ms": sum(times) if times else None,
        "mean_latency_ms": sum(times) / len(times) if times else None,
        "max_latency_ms": max(times) if times else None,
    }


def harness_completion_status(
    result: dict[str, Any],
    *,
    execution_status: str,
    harness: dict[str, Any],
) -> str:
    if execution_status in {"deadline", "cancelled"}:
        return "unconfirmed"
    if result.get("agent_result") is None:
        return "not_evaluated"
    agent_name = result.get("config", {}).get("agent", {}).get("name")
    if agent_name == "terminus-2":
        return (
            "confirmed"
            if harness.get("mark_task_complete_calls", 0) >= 2
            else "unconfirmed"
        )
    return "not_evaluated"


def evidence_telemetry(
    rewards: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    snapshot = state.get("snapshot") if isinstance(state.get("snapshot"), dict) else {}
    events = state.get("events") if isinstance(state.get("events"), list) else []
    source_sequence = state.get("source_sequence")
    if not isinstance(source_sequence, list):
        source_sequence = state.get("opened")
    if not isinstance(source_sequence, list):
        source_sequence = [
            event.get("source_id")
            for event in events
            if isinstance(event, dict)
            and event.get("action") == "open"
            and isinstance(event.get("source_id"), str)
        ]

    def reward_or_snapshot(reward_key: str, snapshot_key: str) -> object:
        value = rewards.get(reward_key)
        return value if value is not None else snapshot.get(snapshot_key)

    return {
        "credits": reward_or_snapshot(
            "observed_evidence_cost", "observed_evidence_cost"
        ),
        "payload_bytes": reward_or_snapshot(
            "evidence_payload_bytes", "observed_evidence_payload_bytes"
        ),
        "token_proxy": reward_or_snapshot(
            "evidence_token_proxy", "observed_evidence_token_proxy"
        ),
        "source_sequence": source_sequence,
        "list_calls": rewards.get("list_calls")
        if rewards.get("list_calls") is not None
        else sum(
            isinstance(event, dict) and event.get("action") == "list"
            for event in events
        ),
        "status_calls": rewards.get("status_calls")
        if rewards.get("status_calls") is not None
        else sum(
            isinstance(event, dict) and event.get("action") == "status"
            for event in events
        ),
    }


def load_release_metadata(
    path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    if path is None:
        return {}, {}, None
    value = v1.read_json(path)
    if not isinstance(value, dict):
        raise ValueError("Release metadata must be a JSON object")
    release = value.get("release")
    tasks = value.get("tasks")
    if not isinstance(release, dict):
        raise ValueError("Release metadata must contain a release object")
    if not isinstance(tasks, dict):
        raise ValueError("Release metadata tasks must be an object")
    return release, tasks, sha256_file(path)


def validate_release_metadata(
    args: argparse.Namespace,
    *,
    release: dict[str, Any],
    tasks: dict[str, Any],
    task_names: set[str],
) -> None:
    requires_metadata = (
        str(args.implementation_version).startswith("0.3")
        and args.run_kind != "preflight"
    )
    if not release and not tasks:
        if requires_metadata:
            raise ValueError("v0.3 task runs require --release-metadata")
        return

    required_release_fields = {
        "name",
        "version",
        "split",
        "generator_version",
        "seed_commitment",
        "expected_task_count",
        "expected_block_count",
        "matrix_complete",
        "conditions",
    }
    missing_release = required_release_fields - release.keys()
    if missing_release:
        raise ValueError(
            f"Release metadata is missing fields: {sorted(missing_release)}"
        )
    if set(release) != required_release_fields:
        raise ValueError("Release metadata contains unexpected release fields")
    if release["conditions"] != list(LOCKED_CONDITIONS):
        raise ValueError("Release conditions do not match the locked condition order")
    if not is_sha256_commitment(release["seed_commitment"]):
        raise ValueError("Release seed_commitment must be a SHA-256 commitment")
    if release["expected_task_count"] != len(task_names):
        raise ValueError("Release expected_task_count does not match the job lock")
    if set(tasks) != task_names:
        missing = sorted(task_names - set(tasks))
        extra = sorted(set(tasks) - task_names)
        raise ValueError(
            f"Release task metadata does not match the lock; missing={missing}, extra={extra}"
        )
    for task_name, metadata in tasks.items():
        if not isinstance(metadata, dict):
            raise ValueError(f"Release metadata for {task_name} must be an object")
        if set(metadata) != {"condition", "scenario_block", "instance_commitment"}:
            raise ValueError(f"Release metadata for {task_name} has unexpected fields")
        if metadata["condition"] not in LOCKED_CONDITIONS:
            raise ValueError(
                f"Unknown condition for {task_name}: {metadata['condition']}"
            )
        if (
            not isinstance(metadata["scenario_block"], str)
            or not metadata["scenario_block"]
        ):
            raise ValueError(f"Missing scenario block for {task_name}")
        commitment = metadata["instance_commitment"]
        if not is_sha256_commitment(commitment):
            raise ValueError(f"Invalid instance commitment for {task_name}")

    blocks: dict[str, list[str]] = defaultdict(list)
    for metadata in tasks.values():
        blocks[metadata["scenario_block"]].append(metadata["condition"])
    if release["expected_block_count"] != len(blocks):
        raise ValueError("Release expected_block_count does not match scenario blocks")

    if args.run_kind == "evaluation" and str(args.implementation_version).startswith(
        "0.3"
    ):
        expected_names = {f"ca-eval-{index:03d}" for index in range(1, 76)}
        if task_names != expected_names:
            raise ValueError("The official v0.3 evaluation requires ca-eval-001..075")
        if (
            release["name"] != "Instinct Bench: Context Appetite v0.3.0"
            or release["version"] != "0.3.0"
            or release["generator_version"] != "0.3.0"
            or release["split"] != "eval"
        ):
            raise ValueError("The official evaluation requires the v0.3.0 eval split")
        if release["matrix_complete"] is not True:
            raise ValueError("The official evaluation matrix must be complete")
        if len(blocks) != 15:
            raise ValueError("The official evaluation requires 15 scenario blocks")
        for block, conditions in blocks.items():
            if Counter(conditions) != Counter(LOCKED_CONDITIONS):
                raise ValueError(
                    f"Scenario block {block} is not a complete matched block"
                )


def build_trial(
    result_path: Path,
    *,
    attempt: int,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    trial_dir = result_path.parent
    result = v1.read_json(result_path)
    task_name = v1.short_task_name(result["task_name"])
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    state, state_path = evidence_state(trial_dir)
    semantic, semantic_method = semantic_outcome(rewards, state)
    proof = proof_outcome(rewards)
    formatting = format_outcome(rewards, state, semantic, proof)
    integrity = binary_metric(rewards.get("verifier_integrity"))
    v_status = verifier_status(result)
    execution_status, failure_stage, failure_detail = execution_classification(result)
    if execution_status == "completed" and v_status in {"fail", "error"}:
        execution_status = "infrastructure_error"
        failure_stage = "verifier"
        failure_detail = (
            "Verifier integrity did not pass."
            if v_status == "fail"
            else "Verifier output was missing or invalid."
        )
    agent_result = result.get("agent_result") or {}
    agent_config = result.get("config", {}).get("agent", {})
    agent_info = result.get("agent_info") or {}
    model_info = agent_info.get("model_info") or {}
    if v_status != "pass":
        semantic = proof = formatting = "not_evaluated"
        semantic_method = "none"
    recovered_strict = (
        binary_metric(rewards.get("task_success")) if v_status == "pass" else None
    )
    recovered_domain = (
        int(semantic == "pass" and proof == "pass" and integrity == 1)
        if v_status == "pass"
        else None
    )
    benchmark_valid = (
        execution_status == "completed" and v_status == "pass" and integrity == 1
    )
    strict_success = recovered_strict if benchmark_valid else None
    domain_success = recovered_domain if benchmark_valid else None
    model_cost = v1.known_cost(agent_result.get("cost_usd"))
    trajectory_path = trial_dir / "agent" / "trajectory.json"
    details_path = trial_dir / "verifier" / "details.json"
    trial_metadata = metadata.get(task_name, {})
    if not isinstance(trial_metadata, dict):
        trial_metadata = {}
    harness = v1.harness_telemetry(trial_dir, agent_result)
    trial = {
        "trial_id": result["id"],
        "trial_name": result["trial_name"],
        "task_name": task_name,
        "condition": trial_metadata.get("condition", V02_CONDITIONS.get(task_name)),
        "scenario_block": trial_metadata.get("scenario_block"),
        "instance_commitment": trial_metadata.get("instance_commitment"),
        "model": agent_config.get("model_name"),
        "attempt": attempt,
        "sampling_seed": agent_config.get("kwargs", {}).get("seed"),
        "execution_status": execution_status,
        "failure_stage": failure_stage,
        "failure_detail": failure_detail,
        "answer_observed": answer_was_observed(state),
        "verifier_status": v_status,
        "semantic_outcome": semantic,
        "proof_outcome": proof,
        "format_outcome": formatting,
        "verifier_integrity": integrity,
        "harness_completion": harness_completion_status(
            result, execution_status=execution_status, harness=harness
        ),
        "benchmark_valid": benchmark_valid,
        "strict_task_success": strict_success,
        "domain_success": domain_success,
        "diagnostics": {
            "recovered_strict_task_success": recovered_strict,
            "recovered_domain_success": recovered_domain,
            "semantic_resolution_method": semantic_method,
            "semantic_exact_disagreement": semantic_method == "canonicalized_unordered",
            "agent_phase_returned": result.get("agent_result") is not None,
        },
        "trajectory_path": v1.relative_path(trajectory_path)
        if trajectory_path.is_file()
        else None,
        "verifier_details_path": v1.relative_path(details_path)
        if details_path.is_file()
        else None,
        "evidence_state_path": v1.relative_path(state_path) if state_path else None,
        "provider_route": v1.redact(model_info),
        "metrics": normalized_metrics(rewards, semantic=semantic, proof=proof),
        "telemetry": {
            "trial_duration_seconds": duration_seconds(result),
            "model_calls": model_call_telemetry(agent_result),
            "model_tokens": {
                "input": agent_result.get("n_input_tokens"),
                "output": agent_result.get("n_output_tokens"),
                "cached_input": agent_result.get("n_cache_tokens"),
                "total": (
                    agent_result.get("n_input_tokens", 0)
                    + agent_result.get("n_output_tokens", 0)
                )
                if isinstance(agent_result.get("n_input_tokens"), int)
                and isinstance(agent_result.get("n_output_tokens"), int)
                else None,
            },
            "evidence": evidence_telemetry(rewards, state),
            "harness": harness,
        },
        "costs_usd": {
            "model": model_cost,
            "harness": None,
            "sandbox": None,
            "total": None,
        },
    }
    validate_trial(trial)
    return trial


def build_not_started(
    lock_trial: dict[str, Any],
    *,
    attempt: int,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    task_name, model = v1.lock_signature(lock_trial)
    label = f"not-started:{task_name}:{model or 'none'}:{attempt}"
    trial_metadata = metadata.get(task_name, {})
    if not isinstance(trial_metadata, dict):
        trial_metadata = {}
    trial = {
        "trial_id": label,
        "trial_name": label,
        "task_name": task_name,
        "condition": trial_metadata.get("condition", V02_CONDITIONS.get(task_name)),
        "scenario_block": trial_metadata.get("scenario_block"),
        "instance_commitment": trial_metadata.get("instance_commitment"),
        "model": model,
        "attempt": attempt,
        "sampling_seed": lock_trial.get("agent", {}).get("kwargs", {}).get("seed"),
        "execution_status": "not_started",
        "failure_stage": None,
        "failure_detail": "not_started",
        "answer_observed": False,
        "verifier_status": "not_run",
        "semantic_outcome": "not_evaluated",
        "proof_outcome": "not_evaluated",
        "format_outcome": "not_evaluated",
        "verifier_integrity": None,
        "harness_completion": "not_evaluated",
        "benchmark_valid": False,
        "strict_task_success": None,
        "domain_success": None,
        "diagnostics": {
            "recovered_strict_task_success": None,
            "recovered_domain_success": None,
            "semantic_resolution_method": "none",
            "semantic_exact_disagreement": False,
            "agent_phase_returned": False,
        },
        "trajectory_path": None,
        "verifier_details_path": None,
        "evidence_state_path": None,
        "provider_route": {},
        "metrics": {},
        "telemetry": {
            "trial_duration_seconds": None,
            "model_calls": {
                "count": 0,
                "total_latency_ms": None,
                "mean_latency_ms": None,
                "max_latency_ms": None,
            },
            "model_tokens": {
                "input": None,
                "output": None,
                "cached_input": None,
                "total": None,
            },
            "evidence": {
                "credits": None,
                "payload_bytes": None,
                "token_proxy": None,
                "source_sequence": [],
                "list_calls": None,
                "status_calls": None,
            },
            "harness": {},
        },
        "costs_usd": {"model": None, "harness": None, "sandbox": None, "total": None},
    }
    validate_trial(trial)
    return trial


def validate_trial(trial: dict[str, Any]) -> None:
    valid = (
        trial["execution_status"] == "completed"
        and trial["verifier_status"] == "pass"
        and trial["verifier_integrity"] == 1
    )
    if trial["benchmark_valid"] is not valid:
        raise ValueError(f"Inconsistent benchmark validity for {trial['trial_name']}")
    if valid and (
        trial["strict_task_success"] not in {0, 1}
        or trial["domain_success"] not in {0, 1}
    ):
        raise ValueError(f"Valid trial is missing task outcomes: {trial['trial_name']}")
    expected_integrity = {
        "pass": 1,
        "fail": 0,
        "error": None,
        "not_run": None,
    }[trial["verifier_status"]]
    if trial["verifier_integrity"] != expected_integrity:
        raise ValueError(f"Inconsistent verifier integrity for {trial['trial_name']}")
    if not valid and (
        trial["strict_task_success"] is not None or trial["domain_success"] is not None
    ):
        raise ValueError(f"Invalid trial has benchmark outcomes: {trial['trial_name']}")
    if trial["verifier_status"] != "pass" and any(
        trial[field] != "not_evaluated"
        for field in ("semantic_outcome", "proof_outcome", "format_outcome")
    ):
        raise ValueError(f"Invalid verifier has task outcomes: {trial['trial_name']}")
    if not trial["answer_observed"] and trial["semantic_outcome"] == "pass":
        raise ValueError(
            f"Missing answer marked semantically correct: {trial['trial_name']}"
        )
    if trial["strict_task_success"] == 1 and any(
        trial[field] != "pass"
        for field in ("semantic_outcome", "proof_outcome", "format_outcome")
    ):
        raise ValueError(f"Strict pass has a failed axis: {trial['trial_name']}")
    if trial["domain_success"] == 1 and any(
        trial[field] != "pass" for field in ("semantic_outcome", "proof_outcome")
    ):
        raise ValueError(f"Domain pass has a failed axis: {trial['trial_name']}")
    if trial["verifier_status"] != "pass" and any(
        trial["diagnostics"][field] is not None
        for field in ("recovered_strict_task_success", "recovered_domain_success")
    ):
        raise ValueError(
            f"Invalid verifier has recovered task outcomes: {trial['trial_name']}"
        )
    if any(
        value is not None
        and (isinstance(value, bool) or not isinstance(value, int | float))
        for value in trial["metrics"].values()
    ):
        raise ValueError(
            f"Public metrics must be numeric or null: {trial['trial_name']}"
        )


def derived_from(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    manifest = v1.read_json(path)
    return {
        "manifest_path": v1.relative_path(path),
        "schema_version": manifest.get("schema_version"),
        "sha256": sha256_file(path),
    }


def build_counts(trials: list[dict[str, Any]], planned: int) -> dict[str, int]:
    counts = {
        "planned": planned,
        "result_records": sum(
            trial["execution_status"] != "not_started" for trial in trials
        ),
        "completed": sum(trial["execution_status"] == "completed" for trial in trials),
        "benchmark_valid": sum(trial["benchmark_valid"] for trial in trials),
        "strict_pass": sum(trial["strict_task_success"] == 1 for trial in trials),
        "domain_pass": sum(trial["domain_success"] == 1 for trial in trials),
        "deadline": sum(trial["execution_status"] == "deadline" for trial in trials),
        "infrastructure_error": sum(
            trial["execution_status"] == "infrastructure_error" for trial in trials
        ),
        "verifier_invalid": sum(trial["verifier_status"] == "fail" for trial in trials),
        "verifier_error": sum(trial["verifier_status"] == "error" for trial in trials),
        "cancelled": sum(trial["execution_status"] == "cancelled" for trial in trials),
        "not_started": sum(
            trial["execution_status"] == "not_started" for trial in trials
        ),
        "verifier_evaluated": sum(
            trial["verifier_status"] == "pass" for trial in trials
        ),
        "recovered_strict_pass": sum(
            trial["diagnostics"]["recovered_strict_task_success"] == 1
            for trial in trials
        ),
        "recovered_domain_pass": sum(
            trial["diagnostics"]["recovered_domain_success"] == 1 for trial in trials
        ),
        "answer_observed": sum(trial["answer_observed"] for trial in trials),
        "harness_confirmed": sum(
            trial["harness_completion"] == "confirmed" for trial in trials
        ),
    }
    terminal = (
        counts["completed"]
        + counts["deadline"]
        + counts["infrastructure_error"]
        + counts["cancelled"]
        + counts["not_started"]
    )
    if terminal != planned:
        raise ValueError(f"Execution counts cover {terminal} of {planned} trials")
    if counts["strict_pass"] > counts["benchmark_valid"]:
        raise ValueError("Strict passes exceed benchmark-valid trials")
    if counts["domain_pass"] > counts["benchmark_valid"]:
        raise ValueError("Domain passes exceed benchmark-valid trials")
    return counts


def validate_job_matrix(
    grouped_results: dict[tuple[str, str | None], list[Path]],
    grouped_locks: dict[tuple[str, str | None], list[dict[str, Any]]],
) -> None:
    unknown_results = set(grouped_results) - set(grouped_locks)
    if unknown_results:
        raise ValueError(
            f"Result signatures are absent from the job lock: {unknown_results}"
        )
    for signature, actual in grouped_results.items():
        if len(actual) > len(grouped_locks[signature]):
            raise ValueError(f"Result signature exceeds its planned count: {signature}")


def validate_task_digests(lock_trials: list[dict[str, Any]]) -> None:
    task_digests: dict[str, set[str]] = defaultdict(set)
    for lock_trial in lock_trials:
        task = lock_trial["task"]
        task_digests[task["name"]].add(task["digest"])
    conflicting = {
        name: sorted(digests)
        for name, digests in task_digests.items()
        if len(digests) > 1
    }
    if conflicting:
        raise ValueError(f"Task names have conflicting digests: {conflicting}")


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    job_dir = args.job_dir.resolve()
    job_lock = v1.read_json(job_dir / "lock.json")
    lock_trials = job_lock["trials"]
    result_paths = sorted(
        (path for path in job_dir.glob("*/result.json") if path.parent != job_dir),
        key=lambda path: (
            v1.read_json(path).get("started_at") or "",
            v1.read_json(path).get("trial_name") or "",
        ),
    )
    grouped_results: dict[tuple[str, str | None], list[Path]] = defaultdict(list)
    for path in result_paths:
        grouped_results[v1.result_signature(v1.read_json(path))].append(path)
    grouped_locks: dict[tuple[str, str | None], list[dict[str, Any]]] = defaultdict(
        list
    )
    for lock_trial in lock_trials:
        grouped_locks[v1.lock_signature(lock_trial)].append(lock_trial)

    validate_job_matrix(grouped_results, grouped_locks)
    validate_task_digests(lock_trials)

    release, release_metadata, metadata_digest = load_release_metadata(
        getattr(args, "release_metadata", None)
    )
    task_names = {v1.lock_signature(trial)[0] for trial in lock_trials}
    validate_release_metadata(
        args, release=release, tasks=release_metadata, task_names=task_names
    )
    base = v1.build_manifest(args)

    trials: list[dict[str, Any]] = []
    for signature, planned in grouped_locks.items():
        actual = grouped_results.get(signature, [])
        for attempt, path in enumerate(actual, start=1):
            trials.append(build_trial(path, attempt=attempt, metadata=release_metadata))
        for attempt in range(len(actual) + 1, len(planned) + 1):
            trials.append(
                build_not_started(
                    planned[attempt - 1], attempt=attempt, metadata=release_metadata
                )
            )
    trials.sort(
        key=lambda trial: (
            trial["model"] or "",
            trial["task_name"],
            trial["attempt"],
            trial["trial_name"],
        )
    )

    counts = build_counts(trials, len(lock_trials))
    known_model_costs = [
        trial["costs_usd"]["model"]
        for trial in trials
        if trial["costs_usd"]["model"] is not None
    ]
    model_cost = sum(known_model_costs) if known_model_costs else None
    base["benchmark"].update(
        {
            "release_metadata_digest": metadata_digest,
            "release_name": release.get("name"),
            "release_version": release.get("version"),
            "split": release.get("split"),
            "generator_version": release.get("generator_version"),
            "seed_commitment": release.get("seed_commitment"),
        }
    )
    base["runner"]["command"] = sanitize_command(base["runner"]["command"])
    return {
        "schema_version": SCHEMA_VERSION,
        "normalizer": {
            "name": "normalize_harbor_job_v2",
            "version": NORMALIZER_VERSION,
            "source_sha256": sha256_file(Path(__file__).resolve()),
        },
        "derived_from": derived_from(args.derived_from),
        "run_id": base["run_id"],
        "harbor_job_uuid": base["harbor_job_uuid"],
        "raw_job_path": base["raw_job_path"],
        "hub_url": base["hub_url"],
        "run_kind": base["run_kind"],
        "lifecycle": base["lifecycle"],
        "publication": base["publication"],
        "supersedes": base["supersedes"],
        "status_reason": base["status_reason"],
        "started_at": base["started_at"],
        "finished_at": base["finished_at"],
        "benchmark": base["benchmark"],
        "runner": base["runner"],
        "agent_egress": base["agent_egress"],
        "contract_visibility": base["contract_visibility"],
        "counts": counts,
        "costs_usd": {
            "model": model_cost,
            "harness": None,
            "sandbox": None,
            "total": None,
        },
        "trials": trials,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize a Harbor 0.20 job into an Instinct Bench v2 manifest."
    )
    parser.add_argument("job_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--run-kind",
        choices=(
            "preflight",
            "oracle-smoke",
            "model-canary",
            "model-pilot",
            "evaluation",
        ),
        required=True,
    )
    parser.add_argument(
        "--publication",
        choices=(
            "scratch",
            "review",
            "eligible",
            "published",
            "superseded",
            "excluded",
        ),
        required=True,
    )
    parser.add_argument(
        "--lifecycle",
        choices=("planned", "running", "completed", "partial", "aborted", "cancelled"),
    )
    parser.add_argument(
        "--agent-egress",
        choices=("public", "allowlist", "no-network"),
        default="public",
    )
    parser.add_argument(
        "--contract-visibility",
        choices=("public", "private", "runtime-generated"),
        required=True,
    )
    parser.add_argument("--implementation-version", default="0.3.0")
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--hub-url")
    parser.add_argument("--status-reason")
    parser.add_argument("--supersedes", action="append", default=[])
    parser.add_argument("--derived-from", type=Path)
    parser.add_argument("--release-metadata", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    counts = manifest["counts"]
    print(
        f"Wrote {args.output}: {counts['benchmark_valid']}/{counts['planned']} "
        f"benchmark-valid, {counts['strict_pass']} strict, "
        f"{counts['domain_pass']} domain, {counts['deadline']} deadlines, "
        f"{counts['infrastructure_error']} infrastructure errors"
    )


if __name__ == "__main__":
    main()
