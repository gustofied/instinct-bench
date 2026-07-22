#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_FRAGMENTS = ("api_key", "apikey", "password", "secret", "token")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def redact(value: Any, key: str = "") -> Any:
    if any(fragment in key.lower() for fragment in SENSITIVE_FRAGMENTS):
        return "[redacted]"
    if isinstance(value, dict):
        return {item_key: redact(item, item_key) for item_key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def short_task_name(value: str) -> str:
    return value.rsplit("/", 1)[-1]


def result_signature(result: dict[str, Any]) -> tuple[str, str | None]:
    agent = result.get("config", {}).get("agent", {})
    return short_task_name(result["task_name"]), agent.get("model_name")


def lock_signature(trial: dict[str, Any]) -> tuple[str, str | None]:
    return trial["task"]["name"], trial.get("agent", {}).get("model_name")


def classify_trial(
    result: dict[str, Any],
) -> tuple[str, str, str, str | None]:
    exception = result.get("exception_info")
    if exception:
        exception_type = str(exception.get("exception_type", "UnknownError"))
        message = str(exception.get("exception_message", ""))
        detail = f"{exception_type}: {message}".strip()
        lowered = f"{exception_type} {message}".lower()
        if "cancel" in lowered:
            return "cancelled", "not-evaluated", "user", detail
        if exception_type in {"AgentTimeoutError", "AgentSafetyRefusalError"}:
            return "valid", "fail", "agent", detail
        if result.get("verifier") is not None:
            return "infrastructure-error", "not-evaluated", "verifier", detail
        if result.get("agent_execution") is None:
            if result.get("agent_setup") is not None:
                return (
                    "infrastructure-error",
                    "not-evaluated",
                    "harness-setup",
                    detail,
                )
            if result.get("environment_setup") is not None:
                return "infrastructure-error", "not-evaluated", "sandbox", detail
            return "infrastructure-error", "not-evaluated", "orchestrator", detail
        if any(
            marker in lowered
            for marker in (
                "apiusagelimit",
                "authentication",
                "modelnotfound",
                "openrouter",
                "provider",
                "rate limit",
                "connection",
            )
        ):
            return "infrastructure-error", "not-evaluated", "model-provider", detail
        return "valid", "fail", "agent", detail

    verifier_result = result.get("verifier_result") or {}
    rewards = verifier_result.get("rewards")
    if not isinstance(rewards, dict):
        return (
            "infrastructure-error",
            "not-evaluated",
            "verifier",
            "Verifier returned no reward dictionary.",
        )
    if rewards.get("verifier_integrity") != 1:
        return (
            "infrastructure-error",
            "not-evaluated",
            "verifier",
            "Verifier integrity did not pass.",
        )
    if rewards.get("task_success") == 1:
        return "valid", "pass", "none", None
    return "valid", "fail", "task", None


def optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = read_json(path)
    return value if isinstance(value, dict) else {}


def known_cost(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def build_trial(
    result_path: Path,
    *,
    attempt: int,
) -> dict[str, Any]:
    trial_dir = result_path.parent
    result = read_json(result_path)
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    details = optional_json(trial_dir / "verifier" / "details.json")
    agent_result = result.get("agent_result") or {}
    agent_config = result.get("config", {}).get("agent", {})
    agent_info = result.get("agent_info") or {}
    model_info = agent_info.get("model_info") or {}
    execution_state, task_outcome, failure_origin, failure_detail = classify_trial(
        result
    )
    trajectory_path = trial_dir / "agent" / "trajectory.json"
    verifier_details_path = trial_dir / "verifier" / "details.json"
    model_cost = known_cost(agent_result.get("cost_usd"))
    return {
        "trial_id": result["id"],
        "trial_name": result["trial_name"],
        "task_name": short_task_name(result["task_name"]),
        "model": agent_config.get("model_name"),
        "attempt": attempt,
        "seed": agent_config.get("kwargs", {}).get("seed"),
        "execution_state": execution_state,
        "task_outcome": task_outcome,
        "failure_origin": failure_origin,
        "failure_detail": failure_detail,
        "trajectory_path": relative_path(trajectory_path)
        if trajectory_path.is_file()
        else None,
        "verifier_details_path": relative_path(verifier_details_path)
        if verifier_details_path.is_file()
        else None,
        "provider_route": redact(model_info),
        "metrics": rewards,
        "telemetry": {
            "model_tokens": {
                "input": agent_result.get("n_input_tokens"),
                "output": agent_result.get("n_output_tokens"),
                "cached_input": agent_result.get("n_cache_tokens"),
                "total": None,
            },
            "evidence": {
                "credits": rewards.get("observed_evidence_cost"),
                "payload_bytes": rewards.get("evidence_payload_bytes"),
                "token_proxy": rewards.get("evidence_token_proxy"),
                "source_sequence": details.get("source_sequence", []),
                "list_calls": rewards.get("list_calls"),
                "status_calls": rewards.get("status_calls"),
            },
        },
        "costs_usd": {
            "model": model_cost,
            "harness": None,
            "sandbox": None,
            "total": None,
        },
    }


def build_not_started(
    lock_trial: dict[str, Any],
    *,
    attempt: int,
) -> dict[str, Any]:
    task_name, model = lock_signature(lock_trial)
    label = f"not-started:{task_name}:{model or 'none'}:{attempt}"
    return {
        "trial_id": label,
        "trial_name": label,
        "task_name": task_name,
        "model": model,
        "attempt": attempt,
        "seed": lock_trial.get("agent", {}).get("kwargs", {}).get("seed"),
        "execution_state": "not-started",
        "task_outcome": "not-evaluated",
        "failure_origin": "orchestrator",
        "failure_detail": "No TrialResult was written.",
        "trajectory_path": None,
        "verifier_details_path": None,
        "provider_route": {},
        "metrics": {},
        "telemetry": {
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
        },
        "costs_usd": {
            "model": None,
            "harness": None,
            "sandbox": None,
            "total": None,
        },
    }


def unique(values: list[Any]) -> list[Any]:
    output = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def prompt_digest(result_paths: list[Path]) -> str | None:
    digests: list[str] = []
    for result_path in result_paths:
        trajectory_path = result_path.parent / "agent" / "trajectory.json"
        if not trajectory_path.is_file():
            continue
        trajectory = read_json(trajectory_path)
        steps = trajectory.get("steps", []) if isinstance(trajectory, dict) else []
        first_user_message = next(
            (
                step.get("message")
                for step in steps
                if isinstance(step, dict)
                and step.get("source") == "user"
                and isinstance(step.get("message"), str)
            ),
            None,
        )
        if first_user_message is None:
            continue
        harness_prompt = first_user_message.split("\n\nTask Description:\n", 1)[0]
        digest = "sha256:" + hashlib.sha256(harness_prompt.encode()).hexdigest()
        if digest not in digests:
            digests.append(digest)
    if len(digests) > 1:
        raise ValueError(f"Harness prompt drift detected within one job: {digests}")
    return digests[0] if digests else None


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    job_dir = args.job_dir.resolve()
    job_result = read_json(job_dir / "result.json")
    job_lock = read_json(job_dir / "lock.json")
    lock_trials = job_lock["trials"]

    result_paths = sorted(
        (path for path in job_dir.glob("*/result.json") if path.parent != job_dir),
        key=lambda path: (
            read_json(path).get("started_at") or "",
            read_json(path).get("trial_name") or "",
        ),
    )
    grouped_results: dict[tuple[str, str | None], list[Path]] = defaultdict(list)
    for path in result_paths:
        grouped_results[result_signature(read_json(path))].append(path)

    grouped_locks: dict[tuple[str, str | None], list[dict[str, Any]]] = defaultdict(
        list
    )
    for trial in lock_trials:
        grouped_locks[lock_signature(trial)].append(trial)

    trials: list[dict[str, Any]] = []
    for signature, planned in grouped_locks.items():
        actual = grouped_results.get(signature, [])
        for attempt, result_path in enumerate(actual, start=1):
            trials.append(build_trial(result_path, attempt=attempt))
        for attempt in range(len(actual) + 1, len(planned) + 1):
            trials.append(build_not_started(planned[attempt - 1], attempt=attempt))
    trials.sort(
        key=lambda trial: (
            trial["model"] or "",
            trial["task_name"],
            trial["attempt"],
            trial["trial_name"],
        )
    )

    first_lock = lock_trials[0]
    agent_names = unique([trial["agent"]["name"] for trial in lock_trials])
    if len(agent_names) != 1:
        raise ValueError(f"Expected one harness per job, found {agent_names}")
    models = unique([trial.get("agent", {}).get("model_name") for trial in lock_trials])
    models = [model for model in models if model is not None]
    model_field: str | list[str] | None
    if not models:
        model_field = None
    elif len(models) == 1:
        model_field = models[0]
    else:
        model_field = models

    agent_versions = unique(
        [
            (read_json(path).get("agent_info") or {}).get("version")
            for path in result_paths
        ]
    )
    agent_versions = [version for version in agent_versions if version is not None]
    harness_version = agent_versions[0] if len(agent_versions) == 1 else None
    providers = unique(
        [
            ((read_json(path).get("agent_info") or {}).get("model_info") or {}).get(
                "provider"
            )
            for path in result_paths
        ]
    )
    providers = [provider for provider in providers if provider is not None]
    provider = providers[0] if len(providers) == 1 else None

    agent_kwargs = first_lock.get("agent", {}).get("kwargs", {})
    expected_per_signature = Counter(lock_signature(trial) for trial in lock_trials)
    n_attempts = max(expected_per_signature.values(), default=1)
    counts = {
        "planned": len(lock_trials),
        "completed": len(result_paths),
        "valid": sum(trial["execution_state"] == "valid" for trial in trials),
        "task_pass": sum(trial["task_outcome"] == "pass" for trial in trials),
        "task_fail": sum(trial["task_outcome"] == "fail" for trial in trials),
        "infrastructure_error": sum(
            trial["execution_state"] == "infrastructure-error" for trial in trials
        ),
        "cancelled": sum(trial["execution_state"] == "cancelled" for trial in trials),
        "not_started": sum(
            trial["execution_state"] == "not-started" for trial in trials
        ),
    }
    if counts["valid"] != counts["task_pass"] + counts["task_fail"]:
        raise ValueError("Valid trial count does not match task outcomes")
    if counts["planned"] != (
        counts["valid"]
        + counts["infrastructure_error"]
        + counts["cancelled"]
        + counts["not_started"]
    ):
        raise ValueError("Execution-state counts do not cover the planned matrix")

    lifecycle = args.lifecycle
    if lifecycle is None:
        if job_result.get("finished_at") and counts["completed"] == counts["planned"]:
            lifecycle = "completed"
        elif job_result.get("finished_at"):
            lifecycle = "partial"
        else:
            lifecycle = "aborted"

    known_model_costs = [
        trial["costs_usd"]["model"]
        for trial in trials
        if trial["costs_usd"]["model"] is not None
    ]
    model_cost = sum(known_model_costs) if known_model_costs else None
    task_checksums = {
        trial["task"]["name"]: trial["task"]["digest"] for trial in lock_trials
    }
    provider_routing = {
        "agent_kwargs": redact(agent_kwargs),
        "extra_allowed_hosts": redact(
            first_lock.get("agent", {}).get("extra_allowed_hosts", [])
        ),
    }
    effort = agent_kwargs.get("reasoning_effort", agent_kwargs.get("effort"))
    temperature = agent_kwargs.get("temperature")
    if not isinstance(temperature, int | float) or isinstance(temperature, bool):
        temperature = None

    return {
        "schema_version": "1.0",
        "run_id": job_dir.name,
        "harbor_job_uuid": job_result.get("id"),
        "raw_job_path": relative_path(job_dir),
        "hub_url": args.hub_url,
        "run_kind": args.run_kind,
        "lifecycle": lifecycle,
        "publication": args.publication,
        "supersedes": args.supersedes,
        "status_reason": args.status_reason,
        "started_at": job_result.get("started_at"),
        "finished_at": job_result.get("finished_at"),
        "benchmark": {
            "name": "instinct-bench",
            "domain": "context-appetite",
            "implementation_version": args.implementation_version,
            "git_commit": args.git_commit,
            "task_checksums": task_checksums,
        },
        "runner": {
            "harbor_version": job_lock["harbor"]["version"],
            "agent": agent_names[0],
            "harness_version": harness_version,
            "skills": first_lock.get("agent", {}).get("skills", []),
            "prompt_digest": prompt_digest(result_paths),
            "environment": first_lock["environment"]["type"],
            "sandbox_config": redact(first_lock["environment"]),
            "provider": provider,
            "provider_routing": provider_routing,
            "model": model_field,
            "effort": effort,
            "temperature": temperature,
            "n_attempts": n_attempts,
            "n_concurrent": job_lock["n_concurrent_trials"],
            "command": args.command,
        },
        "agent_egress": args.agent_egress,
        "contract_visibility": args.contract_visibility,
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
        description="Normalize a Harbor 0.20 job into an Instinct Bench manifest."
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
    parser.add_argument("--implementation-version", default="0.2.1")
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--hub-url")
    parser.add_argument("--status-reason")
    parser.add_argument("--supersedes", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")
    print(
        f"Wrote {args.output}: {manifest['counts']['completed']}/"
        f"{manifest['counts']['planned']} completed, "
        f"{manifest['counts']['task_pass']} task passes, "
        f"{manifest['counts']['infrastructure_error']} infrastructure errors"
    )


if __name__ == "__main__":
    main()
