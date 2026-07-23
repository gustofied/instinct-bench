from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Literal


Condition = Literal[
    "answer-now",
    "single-source",
    "complementary-evidence",
    "insufficient-evidence",
    "reliability-conflict",
]
Decision = Literal["answer", "insufficient"]
Split = Literal["dev", "eval"]

CONDITIONS: tuple[Condition, ...] = (
    "answer-now",
    "single-source",
    "complementary-evidence",
    "insufficient-evidence",
    "reliability-conflict",
)
SOURCE_COSTS = (1, 2, 4, 8)
TASK_ID_PATTERN = re.compile(r"^ca-(?:dev|eval)-\d{3}$")
COMMITMENT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    evidence_cost: int
    description: str
    authority_class: str
    declared_reliability: float
    lineage_group: str
    content: str

    def validate(self) -> None:
        if not self.source_id.startswith("src-") or len(self.source_id) < 8:
            raise ValueError(f"invalid source id: {self.source_id}")
        if self.evidence_cost not in SOURCE_COSTS:
            raise ValueError(f"invalid source cost: {self.evidence_cost}")
        if not 0 <= self.declared_reliability <= 1:
            raise ValueError("declared reliability must be between zero and one")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                self.description,
                self.authority_class,
                self.lineage_group,
                self.content,
            )
        ):
            raise ValueError("source text fields must be non-empty")


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    split: Split
    scenario_block: str
    condition: Condition
    title: str
    question: str
    entity_label: str
    initial_context: str
    initial_authority_class: str
    initial_declared_reliability: float
    initial_lineage_group: str
    latent_entity_id: str
    expected_decision: Decision
    expected_entity_id: str | None
    sources: tuple[SourceSpec, ...]
    source_order: tuple[str, ...]
    accepted_proof_sets: tuple[tuple[str, ...], ...]

    @property
    def package_name(self) -> str:
        return f"instinct-bench/{self.task_id}"

    @property
    def source_map(self) -> dict[str, SourceSpec]:
        return {source.source_id: source for source in self.sources}

    @property
    def hindsight_minimum_cost(self) -> int:
        costs = {source.source_id: source.evidence_cost for source in self.sources}
        return min(
            sum(costs[source_id] for source_id in path)
            for path in self.accepted_proof_sets
        )

    @property
    def expected_submission(self) -> dict[str, object]:
        if self.expected_decision == "insufficient":
            return {"decision": "insufficient", "answer": None, "confidence": 1.0}
        return {
            "decision": "answer",
            "answer": {"entity_id": self.expected_entity_id},
            "confidence": 1.0,
        }

    def validate(self) -> None:
        if not TASK_ID_PATTERN.fullmatch(self.task_id):
            raise ValueError(f"invalid task id: {self.task_id}")
        expected_prefix = f"ca-{self.split}-"
        if not self.task_id.startswith(expected_prefix):
            raise ValueError("task id does not match split")
        if self.condition not in CONDITIONS:
            raise ValueError(f"unknown condition: {self.condition}")
        text_fields = (
            self.scenario_block,
            self.title,
            self.question,
            self.entity_label,
            self.initial_context,
            self.initial_authority_class,
            self.initial_lineage_group,
        )
        if not all(isinstance(value, str) and value.strip() for value in text_fields):
            raise ValueError("task text fields must be non-empty")
        expected_block_prefix = "ca-dev-block-" if self.split == "dev" else "ca-block-"
        if not self.scenario_block.startswith(expected_block_prefix):
            raise ValueError("scenario block does not match split")
        if len(self.sources) != 4:
            raise ValueError("every task must contain exactly four sources")
        for source in self.sources:
            source.validate()
        source_ids = [source.source_id for source in self.sources]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source ids must be unique")
        if sorted(source.evidence_cost for source in self.sources) != list(
            SOURCE_COSTS
        ):
            raise ValueError("every task must use costs 1, 2, 4, and 8 exactly once")
        if set(self.source_order) != set(source_ids) or len(self.source_order) != 4:
            raise ValueError("source_order must contain each source exactly once")
        if not self.accepted_proof_sets:
            raise ValueError("at least one accepted proof set is required")
        for path in self.accepted_proof_sets:
            if len(path) != len(set(path)) or not set(path).issubset(source_ids):
                raise ValueError(
                    "accepted proof sets must contain unique known sources"
                )
        proof_sets = [set(path) for path in self.accepted_proof_sets]
        if len({frozenset(path) for path in proof_sets}) != len(proof_sets):
            raise ValueError("accepted proof sets must be unique")
        if any(
            left > right
            for left_index, left in enumerate(proof_sets)
            for right_index, right in enumerate(proof_sets)
            if left_index != right_index
        ):
            raise ValueError("accepted proof sets must be inclusion-minimal")
        if self.condition == "answer-now" and self.accepted_proof_sets != ((),):
            raise ValueError("answer-now must permit the empty proof set")
        if self.condition != "answer-now" and any(
            not path for path in self.accepted_proof_sets
        ):
            raise ValueError("non-answer-now tasks cannot permit empty proof")
        if self.expected_decision == "answer" and not self.expected_entity_id:
            raise ValueError("answer tasks require an expected entity id")
        if (
            self.expected_decision == "insufficient"
            and self.expected_entity_id is not None
        ):
            raise ValueError("insufficient tasks cannot expose an expected entity id")
        if (self.condition == "insufficient-evidence") != (
            self.expected_decision == "insufficient"
        ):
            raise ValueError("condition and terminal decision disagree")
        if not self.latent_entity_id:
            raise ValueError("every matched task requires a latent entity id")
        if not 0 <= self.initial_declared_reliability <= 1:
            raise ValueError("initial reliability must be between zero and one")
        if sum(source.evidence_cost for source in self.sources) > 15:
            raise ValueError("total evidence acquisition cost must not exceed 15")

    def canonical_payload(self) -> dict[str, object]:
        return asdict(self)

    def instance_commitment(self) -> str:
        encoded = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":")
        ).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_commitment(value: str) -> None:
    if not COMMITMENT_PATTERN.fullmatch(value):
        raise ValueError(f"invalid SHA-256 commitment: {value}")
