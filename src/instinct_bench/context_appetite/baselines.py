from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Literal

from .schemas import TaskSpec
from .semantic_audit import infer_supported_decisions


TerminalMode = Literal["answer", "insufficient", "oracle"]
AcquisitionPolicy = Callable[[TaskSpec], tuple[str, ...]]


@dataclass(frozen=True)
class Policy:
    acquire: AcquisitionPolicy
    terminal_mode: TerminalMode


@dataclass(frozen=True)
class PolicyResult:
    policy: str
    task_id: str
    opened: tuple[str, ...]
    proof_coverage: int
    terminal_mode_match: int
    optimistic_success: int
    evidence_cost: int
    optimistic_policy_utility: int


def open_none(_spec: TaskSpec) -> tuple[str, ...]:
    return ()


def first_listed(spec: TaskSpec) -> tuple[str, ...]:
    return spec.source_order[:1]


def cheapest_first(spec: TaskSpec) -> tuple[str, ...]:
    source = min(spec.sources, key=lambda item: item.evidence_cost)
    return (source.source_id,)


def highest_reliability_first(spec: TaskSpec) -> tuple[str, ...]:
    source = max(
        spec.sources,
        key=lambda item: (item.declared_reliability, -item.evidence_cost),
    )
    return (source.source_id,)


def random_one(spec: TaskSpec) -> tuple[str, ...]:
    rng = random.Random(spec.task_id)
    return (rng.choice(spec.source_order),)


def open_all(spec: TaskSpec) -> tuple[str, ...]:
    return spec.source_order


AUTHORITY_PRIORITY = {
    "immutable-control-ledger": 7,
    "primary-control-record": 6,
    "signed-ingestion-receipt": 5,
    "signed-operational-log": 4,
    "independent-audit-record": 3,
    "derived-summary": 1,
    "unsigned-operator-note": 0,
}


def authority_aware_sequential(spec: TaskSpec) -> tuple[str, ...]:
    visible_task = {
        "question": spec.question,
        "initial_context": spec.initial_context,
        "sources": {
            source.source_id: {
                "content": source.content,
                "authority_class": source.authority_class,
                "declared_reliability": source.declared_reliability,
                "lineage_group": source.lineage_group,
            }
            for source in spec.sources
        },
    }
    if infer_supported_decisions(visible_task, ()):
        return ()
    list_position = {
        source_id: position for position, source_id in enumerate(spec.source_order)
    }
    ordered = sorted(
        spec.sources,
        key=lambda source: (
            -AUTHORITY_PRIORITY.get(source.authority_class, -1),
            -source.declared_reliability,
            list_position[source.source_id],
            source.evidence_cost,
        ),
    )
    opened: list[str] = []
    for source in ordered:
        opened.append(source.source_id)
        if infer_supported_decisions(visible_task, opened):
            break
    return tuple(opened)


def proof_aware_oracle(spec: TaskSpec) -> tuple[str, ...]:
    costs = spec.source_map
    return min(
        spec.accepted_proof_sets,
        key=lambda path: sum(costs[source_id].evidence_cost for source_id in path),
    )


# Acquisition-only policies use an oracle terminal mode after opening evidence. This
# deliberately isolates source-selection coverage; it is not a model-performance
# baseline and does not claim the policy could infer the hidden answer.
POLICIES: dict[str, Policy] = {
    "answer-immediately": Policy(open_none, "answer"),
    "abstain-immediately": Policy(open_none, "insufficient"),
    "first-listed": Policy(first_listed, "oracle"),
    "cheapest-first": Policy(cheapest_first, "oracle"),
    "highest-reliability-first": Policy(highest_reliability_first, "oracle"),
    "random-one": Policy(random_one, "oracle"),
    "authority-aware-sequential": Policy(authority_aware_sequential, "oracle"),
    "open-all": Policy(open_all, "oracle"),
    "proof-aware-oracle": Policy(proof_aware_oracle, "oracle"),
}


def evaluate_policy(name: str, policy: Policy, spec: TaskSpec) -> PolicyResult:
    opened = tuple(dict.fromkeys(policy.acquire(spec)))
    opened_set = set(opened)
    proof_coverage = int(
        any(set(path).issubset(opened_set) for path in spec.accepted_proof_sets)
    )
    terminal_mode_match = int(
        policy.terminal_mode == "oracle"
        or policy.terminal_mode == spec.expected_decision
    )
    optimistic_success = proof_coverage * terminal_mode_match
    evidence_cost = sum(
        spec.source_map[source_id].evidence_cost for source_id in opened
    )
    if optimistic_success:
        utility = 100 - evidence_cost
    elif policy.terminal_mode == "insufficient" and spec.expected_decision == "answer":
        utility = -50 - evidence_cost
    else:
        utility = -200 - evidence_cost
    return PolicyResult(
        policy=name,
        task_id=spec.task_id,
        opened=opened,
        proof_coverage=proof_coverage,
        terminal_mode_match=terminal_mode_match,
        optimistic_success=optimistic_success,
        evidence_cost=evidence_cost,
        optimistic_policy_utility=utility,
    )


def evaluate_all(specs: list[TaskSpec]) -> list[PolicyResult]:
    return [
        evaluate_policy(name, policy, spec)
        for name, policy in POLICIES.items()
        for spec in specs
    ]


def summarize(results: list[PolicyResult]) -> dict[str, dict[str, float | int]]:
    policies = sorted({result.policy for result in results})
    summary: dict[str, dict[str, float | int]] = {}
    for policy in policies:
        rows = [result for result in results if result.policy == policy]
        summary[policy] = {
            "tasks": len(rows),
            "proof_coverage": sum(row.proof_coverage for row in rows),
            "optimistic_successes": sum(row.optimistic_success for row in rows),
            "mean_evidence_cost": sum(row.evidence_cost for row in rows) / len(rows),
            "mean_optimistic_policy_utility": sum(
                row.optimistic_policy_utility for row in rows
            )
            / len(rows),
        }
    return summary
