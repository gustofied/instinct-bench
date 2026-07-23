#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = REPO_ROOT / "evals" / "context-appetite" / "official-run-v0.3.1.json"
CONDITIONS = {
    "answer-now",
    "single-source",
    "complementary-evidence",
    "insufficient-evidence",
    "reliability-conflict",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the locked Context Appetite v0.3.1 protocol"
    )
    parser.add_argument("--phase", choices=("canary", "evaluation"), required=True)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--print-config", action="store_true")
    parser.add_argument("--install-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected an object in {path}")
    return value


def validate_lock(lock: dict[str, Any], phase: str) -> dict[str, Any]:
    if lock.get("schema_version") != "1.1":
        raise ValueError("unsupported run-lock schema")
    benchmark = lock.get("benchmark")
    agent = lock.get("agent")
    sandbox = lock.get("sandbox")
    execution = lock.get("execution")
    if not all(
        isinstance(value, dict) for value in (benchmark, agent, sandbox, execution)
    ):
        raise ValueError("run lock is missing required sections")

    commitment_path = REPO_ROOT / benchmark["release_commitment_file"]
    metadata_path = REPO_ROOT / benchmark["release_metadata_file"]
    commitment = load_json(commitment_path)["release"]
    metadata = load_json(metadata_path)
    release = metadata["release"]
    for field in (
        "seed_commitment",
        "dataset_commitment",
        "package_set_commitment",
    ):
        locked = benchmark[field]
        if commitment[field] != locked or release[field] != locked:
            raise ValueError(f"run lock does not match release {field}")
    if release["expected_task_count"] != execution["evaluation"]["expected_trials"]:
        raise ValueError("locked trial count does not match release metadata")

    canary_ids = execution["canary"]["task_ids"]
    if len(canary_ids) != 5 or len(set(canary_ids)) != 5:
        raise ValueError("canary must contain five unique task IDs")
    task_rows = metadata.get("tasks", {})
    if not set(canary_ids).issubset(task_rows):
        raise ValueError("canary names unknown tasks")
    if {task_rows[task_id]["condition"] for task_id in canary_ids} != CONDITIONS:
        raise ValueError("canary must contain exactly one task per condition")
    if len({task_rows[task_id]["scenario_block"] for task_id in canary_ids}) != 5:
        raise ValueError("canary tasks must come from five distinct matched blocks")

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    if status.stdout.strip():
        raise ValueError("official protocol requires a clean Git worktree")
    release_commit = benchmark["task_release_commit"]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", release_commit, "HEAD"],
        cwd=REPO_ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("task release commit is not an ancestor of HEAD")

    phase_config = execution.get(phase)
    if not isinstance(phase_config, dict):
        raise ValueError(f"missing {phase} execution lock")
    return phase_config


def build_command(
    lock: dict[str, Any],
    *,
    phase: str,
    harbor_executable: str,
    print_config: bool = False,
    install_only: bool = False,
) -> list[str]:
    benchmark = lock["benchmark"]
    agent = lock["agent"]
    sandbox = lock["sandbox"]
    execution = lock["execution"]
    phase_config = execution[phase]
    provider = agent["provider_request"]
    provider_payload = json.dumps(
        {
            "extra_body": {
                "provider": {
                    "order": [provider["endpoint_tag"]],
                    "allow_fallbacks": provider["allow_fallbacks"],
                    "require_parameters": provider["require_parameters"],
                }
            }
        },
        separators=(",", ":"),
    )

    command = [
        harbor_executable,
        "run",
        "-p",
        benchmark["dataset_path"],
    ]
    if phase == "canary":
        for task_id in phase_config["task_ids"]:
            command.extend(("-i", task_id))
    command.extend(
        (
            "-a",
            agent["harness"],
            "-m",
            agent["model"],
            "-e",
            sandbox["environment"],
            "-o",
            phase_config["jobs_dir"],
            "--job-name",
            phase_config["job_name"],
            "-k",
            str(execution["attempts_per_task"]),
            "-n",
            str(execution["concurrency"]),
            "--n-concurrent-agents",
            str(execution["agent_concurrency"]),
            "--max-retries",
            str(execution["max_retries"]),
            "--ek",
            f"modal_vm_runtime={str(sandbox['modal_vm_runtime']).lower()}",
            "--ak",
            f"temperature={agent['sampling']['temperature']}",
            "--ak",
            f"llm_call_kwargs={provider_payload}",
            "--env-file",
            execution["env_file"],
            "-y",
        )
    )
    if print_config:
        command.append("--print-config")
    if install_only:
        command.append("--install-only")
    return command


def main() -> None:
    args = parse_args()
    lock_path = args.lock.resolve()
    lock = load_json(lock_path)
    phase_config = validate_lock(lock, args.phase)
    harbor_executable = shutil.which("harbor")
    if harbor_executable is None:
        raise SystemExit("harbor executable not found")
    command = build_command(
        lock,
        phase=args.phase,
        harbor_executable=harbor_executable,
        print_config=args.print_config,
        install_only=args.install_only,
    )
    if args.dry_run:
        print(shlex.join(command))
        return

    os.umask(0o077)
    output_root = REPO_ROOT / phase_config["jobs_dir"]
    output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_root.chmod(0o700)
    job_path = output_root / phase_config["job_name"]
    if job_path.exists():
        raise SystemExit(f"refusing to overwrite locked job: {job_path}")
    subprocess.run(command, cwd=REPO_ROOT, check=True)


if __name__ == "__main__":
    main()
