#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from instinct_bench.context_appetite import generator  # noqa: E402
from instinct_bench.context_appetite.schemas import CONDITIONS, TaskSpec  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a generated Context Appetite release"
    )
    parser.add_argument("--split", choices=("dev", "eval"), required=True)
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--secret-file", type=Path)
    return parser.parse_args()


def release_secret(split: str, secret_file: Path | None) -> bytes:
    if split == "dev":
        if secret_file is not None:
            raise ValueError("the public dev release uses its committed seed")
        return generator.DEV_SECRET
    if secret_file is None:
        raise ValueError("--secret-file is required for the eval release")
    return generator.read_private_secret(secret_file)


def validate_permissions(dataset_dir: Path) -> None:
    for path in (dataset_dir, *dataset_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"private release must not contain symlinks: {path}")
        mode = path.stat().st_mode & 0o777
        if mode & 0o077:
            raise ValueError(f"private path is accessible by group or others: {path}")
        expected = 0o700 if path.is_dir() or mode & 0o111 else 0o600
        if mode != expected:
            raise ValueError(
                f"unexpected private mode for {path}: {mode:04o}, expected {expected:04o}"
            )


def validate_dataset(
    dataset_dir: Path,
    specs: list[TaskSpec],
    secret: bytes,
    *,
    private: bool,
) -> None:
    actual_metadata = json.loads((dataset_dir / "release-metadata.json").read_text())
    expected_metadata = generator.release_metadata(secret, specs, dataset_dir)
    if actual_metadata != expected_metadata:
        raise ValueError("release metadata does not match generator output")

    dataset = tomllib.loads((dataset_dir / "dataset.toml").read_text())
    task_rows = dataset["tasks"]
    if len(task_rows) != len(specs):
        raise ValueError("dataset task count does not match generated specs")
    digests = {row["name"].split("/", 1)[1]: row["digest"] for row in task_rows}
    if set(digests) != {spec.task_id for spec in specs}:
        raise ValueError("dataset task names do not match generated specs")

    for spec in specs:
        task_dir = dataset_dir / spec.task_id
        if digests[spec.task_id] != generator.task_digest(task_dir):
            raise ValueError(f"package digest mismatch: {spec.task_id}")
        task_data = json.loads(
            (
                task_dir / "environment" / "evidence-sidecar" / "task_data.json"
            ).read_text()
        )
        expected = json.loads((task_dir / "tests" / "expected.json").read_text())
        if task_data != generator.task_data(spec):
            raise ValueError(f"agent-visible task data drift: {spec.task_id}")
        if expected != generator.expected_data(spec):
            raise ValueError(f"hidden verifier data drift: {spec.task_id}")
        if (task_dir / "instruction.md").read_text() != generator.instruction(spec):
            raise ValueError(f"instruction drift: {spec.task_id}")

    if private:
        validate_permissions(dataset_dir)


def review_rows(specs: list[TaskSpec]) -> list[str]:
    by_block: dict[str, list[TaskSpec]] = defaultdict(list)
    for spec in specs:
        by_block[spec.scenario_block].append(spec)

    rows = []
    for block in sorted(by_block):
        block_specs = by_block[block]
        if Counter(spec.condition for spec in block_specs) != Counter(CONDITIONS):
            raise ValueError(f"incomplete condition matrix: {block}")
        if len({spec.title for spec in block_specs}) != 1:
            raise ValueError(f"scenario title drift inside matched block: {block}")
        mapping = {spec.condition: spec.task_id for spec in block_specs}
        assignments = "  ".join(
            f"{condition}={mapping[condition]}" for condition in CONDITIONS
        )
        rows.append(f"{block}  {block_specs[0].title}  {assignments}")
    return rows


def main() -> None:
    args = parse_args()
    dataset_dir = args.dataset_dir.resolve()
    secret = release_secret(args.split, args.secret_file)
    specs = generator.build_specs(secret, args.split)
    validate_dataset(dataset_dir, specs, secret, private=args.split == "eval")
    rows = review_rows(specs)
    for row in rows:
        print(row)
    print(
        f"Validated {len(specs)} Context Appetite v{generator.RELEASE_VERSION} "
        f"{args.split} tasks across {len(rows)} matched blocks."
    )


if __name__ == "__main__":
    main()
