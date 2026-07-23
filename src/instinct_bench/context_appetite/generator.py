from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import random
import shutil
import stat
import string
from dataclasses import dataclass
from itertools import permutations
from pathlib import Path
from typing import Any, Literal

from .blueprints import DEV_BLUEPRINTS, EVAL_BLUEPRINTS, Blueprint
from .schemas import CONDITIONS, SOURCE_COSTS, Condition, SourceSpec, TaskSpec


RELEASE_NAME = "Instinct Bench: Context Appetite v0.3.1"
RELEASE_VERSION = "0.3.1"
GENERATOR_VERSION = "0.3.1"
STATE_SCHEMA_VERSION = 5
DEV_SECRET = b"instinct-bench-context-appetite-v0.3.1-public-dev-seed"
TEMPLATE_ROOT = Path(__file__).with_name("templates")
GENERATED_MARKER = ".generated-context-appetite-v0.3.1"
LEGACY_DEV_MARKER = ".generated-context-appetite-v0.3.0"
TOKEN_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"
INDEX_PERMUTATIONS = tuple(permutations(range(4)))


@dataclass(frozen=True)
class RoleRecord:
    authority_class: str
    declared_reliability: float
    lineage_group: str
    content: str


def derived_bytes(secret: bytes, label: str) -> bytes:
    return hmac.new(secret, label.encode(), hashlib.sha256).digest()


def derived_rng(secret: bytes, label: str) -> random.Random:
    return random.Random(int.from_bytes(derived_bytes(secret, label), "big"))


def opaque_token(rng: random.Random, length: int = 8) -> str:
    return "".join(rng.choice(TOKEN_ALPHABET) for _ in range(length))


def source_filler(rng: random.Random) -> str:
    notes = (
        "The record also contains routine timestamps that do not change the attribution.",
        "Administrative fields were reconciled independently and add no attribution claim.",
        "The surrounding status checks remained within their ordinary operating range.",
        "A duplicate bookkeeping line was removed before this record was finalized.",
    )
    selected = rng.sample(notes, k=rng.randrange(0, 3))
    return " " + " ".join(selected) if selected else ""


def role_records(
    *,
    condition: Condition,
    blueprint: Blueprint,
    event_id: str,
    target: str,
    alternate: str,
    link_a: str,
    link_b: str,
    block_number: int,
    rng: random.Random,
) -> tuple[dict[str, RoleRecord], tuple[tuple[str, ...], ...], str]:
    lineage = {
        name: f"lin-{opaque_token(rng, 6)}" for name in string.ascii_lowercase[:8]
    }

    def record(
        authority: str,
        reliability: float,
        lineage_key: str,
        content: str,
    ) -> RoleRecord:
        return RoleRecord(
            authority,
            reliability,
            lineage[lineage_key],
            content + source_filler(rng),
        )

    if condition == "answer-now":
        roles = {
            "redundant": record(
                "primary-control-record",
                0.99,
                "a",
                f"The final control record independently confirms {target} for {event_id}.",
            ),
            "unrelated": record(
                "primary-control-record",
                0.99,
                "b",
                f"A prior unrelated event was controlled by {alternate}; it is not {event_id}.",
            ),
            "timeline": record(
                "signed-operational-log",
                0.98,
                "c",
                f"The timeline confirms when {event_id} closed but contains no {blueprint.entity_label} identifier.",
            ),
            "summary": record(
                "derived-summary",
                0.74,
                "d",
                f"A desk summary refers to the {blueprint.entity_label} already named in the signed decision record.",
            ),
        }
        return roles, ((),), "redundant"

    if condition == "single-source":
        alternative_path = block_number % 2 == 0
        roles = {
            "proof-a": record(
                "primary-control-record",
                0.99,
                "a",
                f"The signed decision for {event_id} names {target} as the controlling {blueprint.entity_label}.",
            ),
            "proof-b": record(
                "independent-audit-record",
                0.97,
                "b",
                (
                    f"The independent audit for {event_id} identifies {target} as the controlling {blueprint.entity_label}."
                    if alternative_path
                    else f"The audit confirms that {event_id} was reviewed, but its extract omits the {blueprint.entity_label} identifier."
                ),
            ),
            "unrelated": record(
                "primary-control-record",
                0.99,
                "c",
                f"The similarly timed but unrelated event used {alternate}; its event identifier is different from {event_id}.",
            ),
            "timeline": record(
                "signed-operational-log",
                0.98,
                "d",
                f"The operational timeline confirms {event_id} but records no controlling entity.",
            ),
        }
        proof_sets = (
            (("proof-a",), ("proof-b",)) if alternative_path else (("proof-a",),)
        )
        return roles, proof_sets, "proof-a"

    if condition == "complementary-evidence":
        alternative_path = block_number % 3 == 0
        roles = {
            "proof-a": record(
                "primary-control-record",
                0.99,
                "a",
                f"The control record maps {event_id} to correlation key {link_a}; it contains no entity identifier.",
            ),
            "proof-b": record(
                "signed-ingestion-receipt",
                0.98,
                "b",
                f"The signed receipt maps correlation key {link_a} to {target}; it contains no event identifier.",
            ),
            "proof-c": record(
                "independent-audit-record",
                0.97,
                "c",
                (
                    f"The audit maps {event_id} to independent correlation key {link_b}; it contains no entity identifier."
                    if alternative_path
                    else f"The audit concerns a separate event linked to {alternate}, not {event_id}."
                ),
            ),
            "proof-d": record(
                "signed-ingestion-receipt",
                0.98,
                "d",
                (
                    f"A second signed receipt maps correlation key {link_b} to {target}; it contains no event identifier."
                    if alternative_path
                    else f"This receipt confirms routine processing but contains neither {event_id} nor an entity identifier."
                ),
            ),
        }
        proof_sets = (
            (("proof-a", "proof-b"), ("proof-c", "proof-d"))
            if alternative_path
            else (("proof-a", "proof-b"),)
        )
        return roles, proof_sets, "proof-a"

    if condition == "insufficient-evidence":
        roles = {
            "ambiguity": record(
                "signed-operational-log",
                0.98,
                "c",
                f"Telemetry for {event_id} combines both control actions and cannot distinguish which {blueprint.entity_label} controlled the event.",
            ),
            "completeness": record(
                "independent-audit-record",
                0.97,
                "d",
                "The audit confirms the records are complete for the window and contains no additional attribution evidence.",
            ),
            "candidate-a": record(
                "primary-control-record",
                0.99,
                "a",
                f"The event window contains a valid control action by {target}, but the record does not bind that action uniquely to {event_id}.",
            ),
            "candidate-b": record(
                "primary-control-record",
                0.99,
                "b",
                f"The same event window contains a valid control action by {alternate}, also not uniquely bound to {event_id}.",
            ),
        }
        return (
            roles,
            (("ambiguity", "completeness"),),
            "ambiguity",
        )

    shared_lineage = lineage["c"]
    roles = {
        "ledger": record(
            "immutable-control-ledger",
            0.995,
            "a",
            f"The immutable ledger maps {event_id} to payload hash {link_a}; it contains no entity identifier.",
        ),
        "receipt": record(
            "signed-ingestion-receipt",
            0.985,
            "b",
            f"The signed receipt maps payload hash {link_a} to {target}; it contains no event identifier.",
        ),
        "informal": RoleRecord(
            "unsigned-operator-note",
            0.52,
            shared_lineage,
            f"An unsigned note claims {alternate} controlled {event_id}."
            + source_filler(rng),
        ),
        "derived": RoleRecord(
            "derived-summary",
            0.68,
            shared_lineage,
            f"A generated summary repeats the same claim that {alternate} controlled {event_id}."
            + source_filler(rng),
        ),
    }
    return roles, (("ledger", "receipt"),), "ledger"


def assign_costs_and_order(
    roles: tuple[str, ...],
    *,
    block_number: int,
) -> tuple[dict[str, int], tuple[str, ...]]:
    block_index = block_number - 1
    cost_permutation = INDEX_PERMUTATIONS[(3 * block_index + 3) % 24]
    order_permutation = INDEX_PERMUTATIONS[(5 * block_index + 5) % 24]
    costs = {
        role: SOURCE_COSTS[cost_permutation[index]] for index, role in enumerate(roles)
    }
    order = tuple(roles[index] for index in order_permutation)
    return costs, order


def build_task(
    *,
    secret: bytes,
    split: Literal["dev", "eval"],
    task_number: int,
    block_number: int,
    condition: Condition,
    blueprint: Blueprint,
    event_id: str,
    target: str,
    alternate: str,
    link_a: str,
    link_b: str,
) -> TaskSpec:
    rng = derived_rng(secret, f"{split}:{block_number}:{condition}")
    roles, proof_role_sets, _primary_role = role_records(
        condition=condition,
        blueprint=blueprint,
        event_id=event_id,
        target=target,
        alternate=alternate,
        link_a=link_a,
        link_b=link_b,
        block_number=block_number,
        rng=rng,
    )
    role_names = tuple(roles)
    costs, role_order = assign_costs_and_order(
        role_names,
        block_number=block_number,
    )
    source_ids = {role: f"src-{opaque_token(rng, 7)}" for role in role_names}
    sources = tuple(
        SourceSpec(
            source_id=source_ids[role],
            evidence_cost=costs[role],
            description=f"{blueprint.title} record {opaque_token(rng, 5)}",
            authority_class=record.authority_class,
            declared_reliability=record.declared_reliability,
            lineage_group=record.lineage_group,
            content=record.content,
        )
        for role, record in roles.items()
    )
    source_order = tuple(source_ids[role] for role in role_order)
    accepted_proof_sets = tuple(
        tuple(source_ids[role] for role in path) for path in proof_role_sets
    )
    if condition == "answer-now":
        initial_context = (
            f"The signed decision register for {event_id} establishes {target} as the controlling "
            f"{blueprint.entity_label}."
        )
        initial_authority = "signed-decision-register"
        initial_reliability = 0.995
    else:
        initial_context = (
            f"The signed intake record establishes {event_id} and the decision question, "
            f"but does not identify the controlling {blueprint.entity_label}."
        )
        initial_authority = "signed-intake-record"
        initial_reliability = 0.99
    expected_decision = (
        "insufficient" if condition == "insufficient-evidence" else "answer"
    )
    task_id = f"ca-{split}-{task_number:03d}"
    scenario_block = (
        f"ca-block-{block_number:03d}"
        if split == "eval"
        else f"ca-dev-block-{block_number:03d}"
    )
    spec = TaskSpec(
        task_id=task_id,
        split=split,
        scenario_block=scenario_block,
        condition=condition,
        title=blueprint.title,
        question=blueprint.question(event_id),
        entity_label=blueprint.entity_label,
        initial_context=initial_context,
        initial_authority_class=initial_authority,
        initial_declared_reliability=initial_reliability,
        initial_lineage_group=f"initial-{opaque_token(rng, 6)}",
        latent_entity_id=target,
        expected_decision=expected_decision,
        expected_entity_id=target if expected_decision == "answer" else None,
        sources=sources,
        source_order=source_order,
        accepted_proof_sets=accepted_proof_sets,
    )
    spec.validate()
    return spec


def build_specs(secret: bytes, split: Literal["dev", "eval"]) -> list[TaskSpec]:
    blueprints = DEV_BLUEPRINTS if split == "dev" else EVAL_BLUEPRINTS
    specs: list[TaskSpec] = []
    task_numbers = list(range(1, len(blueprints) * len(CONDITIONS) + 1))
    if split == "eval":
        derived_rng(secret, "eval:task-id-permutation").shuffle(task_numbers)
    number_index = 0
    for block_number, blueprint in enumerate(blueprints, start=1):
        block_rng = derived_rng(secret, f"{split}:block:{block_number}")
        event_id = f"evt-{opaque_token(block_rng, 8)}"
        target = f"{blueprint.entity_prefix}-{opaque_token(block_rng, 8)}"
        alternate = f"{blueprint.entity_prefix}-{opaque_token(block_rng, 8)}"
        link_a = f"link-{opaque_token(block_rng, 7)}"
        link_b = f"link-{opaque_token(block_rng, 7)}"
        for condition in CONDITIONS:
            specs.append(
                build_task(
                    secret=secret,
                    split=split,
                    task_number=task_numbers[number_index],
                    block_number=block_number,
                    condition=condition,
                    blueprint=blueprint,
                    event_id=event_id,
                    target=target,
                    alternate=alternate,
                    link_a=link_a,
                    link_b=link_b,
                )
            )
            number_index += 1
    if split == "eval":
        derived_rng(secret, "eval:dataset-order-permutation").shuffle(specs)
    return specs


def task_data(spec: TaskSpec) -> dict[str, Any]:
    return {
        "task_id": spec.package_name,
        "task_data_version": RELEASE_VERSION,
        "evidence_cost_table_version": RELEASE_VERSION,
        "question": spec.question,
        "initial_context": spec.initial_context,
        "initial_context_metadata": {
            "authority_class": spec.initial_authority_class,
            "declared_reliability": spec.initial_declared_reliability,
            "lineage_group": spec.initial_lineage_group,
        },
        "source_order": list(spec.source_order),
        "sources": {
            source.source_id: {
                "evidence_cost": source.evidence_cost,
                "description": source.description,
                "authority_class": source.authority_class,
                "declared_reliability": source.declared_reliability,
                "lineage_group": source.lineage_group,
                "content": source.content,
            }
            for source in spec.sources
        },
    }


def expected_data(spec: TaskSpec) -> dict[str, Any]:
    source_map = spec.source_map
    payload_bytes = {
        source_id: len(source.content.encode())
        for source_id, source in source_map.items()
    }
    return {
        "task_id": spec.package_name,
        "state_schema_version": STATE_SCHEMA_VERSION,
        "task_data_version": RELEASE_VERSION,
        "evidence_cost_table_version": RELEASE_VERSION,
        "scorer_version": RELEASE_VERSION,
        "evaluation_protocol_version": RELEASE_VERSION,
        "expected_decision": spec.expected_decision,
        "expected_entity_id": spec.expected_entity_id,
        "accepted_proof_sets": [list(path) for path in spec.accepted_proof_sets],
        "hindsight_minimum_cost": spec.hindsight_minimum_cost,
        "source_order": list(spec.source_order),
        "source_costs": {
            source_id: source.evidence_cost for source_id, source in source_map.items()
        },
        "source_payload_bytes": payload_bytes,
        "source_token_proxy": {
            source_id: (byte_count + 3) // 4
            for source_id, byte_count in payload_bytes.items()
        },
    }


def instruction(spec: TaskSpec) -> str:
    return f"""# Decision Record

{spec.question}

Initial context: {spec.initial_context}

Initial-context provenance:
- authority class: `{spec.initial_authority_class}`
- declared reliability: `{spec.initial_declared_reliability:.3f}`
- lineage group: `{spec.initial_lineage_group}`

The evidence catalog is optional. Inspect it with `evidence list`, open one
source with `evidence open SOURCE_ID`, and inspect spend with `evidence status`.

Submit exactly one final decision:

```text
evidence submit answer ENTITY_ID --confidence PROBABILITY
evidence submit insufficient --confidence PROBABILITY
```

Replace `PROBABILITY` with your confidence from `0` to `1`.
Your submission is final. Evidence cannot be opened afterward.

Payoff used as a diagnostic:

```text
supported correct answer       +100
supported INSUFFICIENT         +100
wrong or unsupported answer    -200
unjustified abstention           -50
opened evidence                -sum(source credits)
```

Task success comes first. Evidence use, payload, model tokens, and policy
utility are reported separately.
"""


def task_toml(spec: TaskSpec) -> str:
    return f'''schema_version = "1.3"
artifacts = [
    {{ source = "/evidence-artifacts/state.json", service = "evidence" }},
]

[task]
name = "{spec.package_name}"
description = "Make a supported decision under priced optional evidence."
authors = [{{ name = "Adam Sioud" }}]
keywords = ["context-appetite", "evidence", "tool-use", "metareasoning"]

[metadata]
implementation_version = "{RELEASE_VERSION}"
difficulty = "medium"
category = "reasoning"
tags = ["instinct-bench", "context-appetite", "evidence-cost"]
difficulty_explanation = "The agent must decide whether available context is sufficient, acquire evidence when useful, and stop."
solution_explanation = "The reference policy opens one hindsight-minimal accepted proof path, then submits the supported terminal decision."
verification_explanation = "A protected sidecar records evidence acquisition. A separate deterministic verifier checks typed semantics, accepted proof paths, format, and ledger integrity."

[verifier]
timeout_sec = 30.0
user = "root"
environment_mode = "separate"

[[verifier.collect]]
service = "evidence"
command = "python3 /opt/evidence/snapshot.py"
timeout_sec = 30.0

[verifier.environment]
network_mode = "no-network"
build_timeout_sec = 600.0
os = "linux"
cpus = 1
memory_mb = 512
storage_mb = 1024
workdir = "/"

[agent]
timeout_sec = 300.0
user = "agent"

[environment]
network_mode = "public"
build_timeout_sec = 600.0
os = "linux"
cpus = 1
memory_mb = 1024
storage_mb = 2048
mcp_servers = []
workdir = "/workspace"

[environment.healthcheck]
command = "evidence ping"
interval_sec = 1.0
timeout_sec = 2.0
start_period_sec = 2.0
start_interval_sec = 0.5
retries = 10
'''


def solution(spec: TaskSpec) -> str:
    opens = "\n".join(
        f"evidence open {source_id}" for source_id in spec.accepted_proof_sets[0]
    )
    if spec.expected_decision == "insufficient":
        submit = "evidence submit insufficient --confidence 1.0"
    else:
        submit = f"evidence submit answer {spec.expected_entity_id} --confidence 1.0"
    body = "\n".join(part for part in (opens, submit) if part)
    return f"#!/bin/sh\nset -eu\n\n{body}\n"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")


def write_task(output_dir: Path, spec: TaskSpec) -> None:
    task_dir = output_dir / spec.task_id
    shutil.copytree(TEMPLATE_ROOT, task_dir)
    (task_dir / "task.toml").write_text(task_toml(spec))
    (task_dir / "instruction.md").write_text(instruction(spec))
    (task_dir / "README.md").write_text(
        f"# {spec.task_id}\n\n"
        f"Generated Context Appetite v{RELEASE_VERSION} {spec.split} task. "
        "Do not edit this "
        "bundle directly; regenerate it from the versioned generator.\n"
    )
    (task_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    write_json(
        task_dir / "environment" / "evidence-sidecar" / "task_data.json",
        task_data(spec),
    )
    write_json(task_dir / "tests" / "expected.json", expected_data(spec))
    solve_path = task_dir / "solution" / "solve.sh"
    solve_path.parent.mkdir(parents=True, exist_ok=True)
    solve_path.write_text(solution(spec))
    solve_path.chmod(0o755)


def task_digest(task_dir: Path) -> str:
    paths: set[Path] = set()
    for name in ("task.toml", "instruction.md", "README.md"):
        path = task_dir / name
        if path.is_file():
            paths.add(path)
    for name in ("environment", "tests", "solution", "steps"):
        directory = task_dir / name
        if directory.is_dir():
            paths.add(directory)
            paths.update(
                path
                for path in directory.rglob("*")
                if "__pycache__" not in path.parts and path.suffix != ".pyc"
            )
    outer = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(task_dir).as_posix()):
        relative = path.relative_to(task_dir).as_posix()
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            outer.update(f"directory\0{relative}\0{mode:04o}\n".encode())
        elif path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            outer.update(f"file\0{relative}\0{mode:04o}\0{digest}\n".encode())
    return "sha256:" + outer.hexdigest()


def dataset_toml(output_dir: Path, specs: list[TaskSpec]) -> str:
    parts = [
        'schema_version = "1.0"',
        "",
        "[dataset]",
        'name = "instinct-bench/context-appetite-dev"'
        if specs[0].split == "dev"
        else 'name = "instinct-bench/context-appetite"',
        f'description = "{RELEASE_NAME}"',
        'authors = [{ name = "Adam Sioud" }]',
        'keywords = ["instinct-bench", "context-appetite", "agent-evaluation"]',
    ]
    for spec in specs:
        parts.extend(
            (
                "",
                "[[tasks]]",
                f'name = "{spec.package_name}"',
                f'digest = "{task_digest(output_dir / spec.task_id)}"',
            )
        )
    return "\n".join(parts) + "\n"


def seed_commitment(secret: bytes) -> str:
    return "sha256:" + hashlib.sha256(secret).hexdigest()


def dataset_commitment(specs: list[TaskSpec]) -> str:
    payload = [
        {
            "task_id": spec.task_id,
            "instance_commitment": spec.instance_commitment(),
        }
        for spec in sorted(specs, key=lambda item: item.task_id)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def package_set_commitment(output_dir: Path, specs: list[TaskSpec]) -> str:
    payload = [
        {
            "task_id": spec.task_id,
            "package_digest": task_digest(output_dir / spec.task_id),
        }
        for spec in sorted(specs, key=lambda item: item.task_id)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def release_metadata(
    secret: bytes, specs: list[TaskSpec], output_dir: Path
) -> dict[str, Any]:
    split = specs[0].split
    blocks = sorted({spec.scenario_block for spec in specs})
    return {
        "schema_version": "1.0",
        "release": {
            "name": RELEASE_NAME,
            "version": RELEASE_VERSION,
            "split": split,
            "generator_version": GENERATOR_VERSION,
            "seed_commitment": seed_commitment(secret),
            "dataset_commitment": dataset_commitment(specs),
            "package_set_commitment": package_set_commitment(output_dir, specs),
            "expected_task_count": len(specs),
            "expected_block_count": len(blocks),
            "matrix_complete": True,
            "conditions": list(CONDITIONS),
        },
        "tasks": {
            spec.task_id: {
                "condition": spec.condition,
                "scenario_block": spec.scenario_block,
                "instance_commitment": spec.instance_commitment(),
            }
            for spec in specs
        },
    }


def public_release_commitment(
    secret: bytes, specs: list[TaskSpec], output_dir: Path
) -> dict[str, Any]:
    split = specs[0].split
    return {
        "schema_version": "1.0",
        "release": {
            "name": RELEASE_NAME,
            "version": RELEASE_VERSION,
            "split": split,
            "generator_version": GENERATOR_VERSION,
            "seed_commitment": seed_commitment(secret),
            "dataset_commitment": dataset_commitment(specs),
            "package_set_commitment": package_set_commitment(output_dir, specs),
            "expected_task_count": len(specs),
            "expected_block_count": len({spec.scenario_block for spec in specs}),
        },
    }


def prepare_output(
    output_dir: Path,
    replace: bool,
    *,
    private: bool,
    allow_legacy_dev_marker: bool,
) -> None:
    if output_dir.exists():
        if not replace:
            raise ValueError(f"output already exists: {output_dir}; pass --replace")
        accepted_markers = [output_dir / GENERATED_MARKER]
        if allow_legacy_dev_marker:
            accepted_markers.append(output_dir / LEGACY_DEV_MARKER)
        if not any(marker.is_file() for marker in accepted_markers):
            raise ValueError(f"refusing to replace unmarked directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, mode=0o700 if private else 0o755)
    if private:
        output_dir.chmod(0o700)
    (output_dir / GENERATED_MARKER).write_text(GENERATOR_VERSION + "\n")


def secure_private_tree(output_dir: Path) -> None:
    output_dir.chmod(0o700)
    for path in output_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"private output must not contain symlinks: {path}")
        if path.is_dir():
            path.chmod(0o755 if path.name == "solution" else 0o700)
        elif path.is_file():
            executable = bool(stat.S_IMODE(path.stat().st_mode) & 0o111)
            # Harbor executes the Oracle solution as the configured non-root agent.
            # The private root remains 0700, while the transported solution path
            # must be traversable and executable after Harbor places it at /solution.
            path.chmod(0o755 if executable else 0o600)


def normalize_public_tree(output_dir: Path) -> None:
    output_dir.chmod(0o755)
    for path in output_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"public output must not contain symlinks: {path}")
        if path.is_dir():
            path.chmod(0o755)
        elif path.is_file():
            executable = bool(stat.S_IMODE(path.stat().st_mode) & 0o111)
            path.chmod(0o755 if executable else 0o644)


def generate(
    *,
    split: Literal["dev", "eval"],
    secret: bytes,
    output_dir: Path,
    replace: bool,
) -> list[TaskSpec]:
    if len(secret) < 32:
        raise ValueError("generation secret must contain at least 32 bytes")
    specs = build_specs(secret, split)
    private = split == "eval"
    prepare_output(
        output_dir,
        replace,
        private=private,
        allow_legacy_dev_marker=split == "dev",
    )
    for spec in specs:
        write_task(output_dir, spec)
    if private:
        secure_private_tree(output_dir)
    else:
        normalize_public_tree(output_dir)
    write_json(
        output_dir / "release-metadata.json",
        release_metadata(secret, specs, output_dir),
    )
    (output_dir / "dataset.toml").write_text(dataset_toml(output_dir, specs))
    (output_dir / "README.md").write_text(
        f"# {RELEASE_NAME}\n\n"
        f"{len(specs)} generated {split} tasks across {len(specs) // 5} matched "
        "blocks. See the domain runbook one directory above.\n"
    )
    if private:
        secure_private_tree(output_dir)
    else:
        normalize_public_tree(output_dir)
    return specs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Generate Context Appetite v{RELEASE_VERSION} tasks"
    )
    parser.add_argument("--split", choices=("dev", "eval"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--secret-file", type=Path)
    parser.add_argument(
        "--commitment-output",
        type=Path,
        help="Write a public commitment without task metadata (eval split only)",
    )
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def read_private_secret(path: Path) -> bytes:
    resolved = path.expanduser()
    if resolved.is_symlink():
        raise ValueError("release secret must not be a symbolic link")
    metadata = resolved.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("release secret must be a regular file")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError("release secret must not be accessible by group or others")
    secret = resolved.read_bytes()
    if len(secret) < 32:
        raise ValueError("generation secret must contain at least 32 bytes")
    return secret


def main() -> None:
    args = parse_args()
    if args.split == "eval":
        if args.secret_file is None:
            raise SystemExit("--secret-file is required for the private eval split")
        try:
            secret = read_private_secret(args.secret_file)
        except (OSError, ValueError) as exc:
            raise SystemExit(f"invalid private release secret: {exc}") from exc
    else:
        if args.secret_file is not None:
            raise SystemExit("the public dev split uses its fixed committed seed")
        if args.commitment_output is not None:
            raise SystemExit("--commitment-output is reserved for the eval split")
        secret = DEV_SECRET
    specs = generate(
        split=args.split,
        secret=secret,
        output_dir=args.output.resolve(),
        replace=args.replace,
    )
    if args.commitment_output is not None:
        write_json(
            args.commitment_output.resolve(),
            public_release_commitment(secret, specs, args.output.resolve()),
        )
    print(
        f"Generated {len(specs)} {args.split} tasks at {args.output}; "
        f"seed commitment {seed_commitment(secret)}; "
        f"dataset commitment {dataset_commitment(specs)}; "
        f"package-set commitment {package_set_commitment(args.output.resolve(), specs)}"
    )


if __name__ == "__main__":
    main()
