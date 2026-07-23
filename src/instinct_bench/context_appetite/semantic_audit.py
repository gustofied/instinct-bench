from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping


EVENT_PATTERN = re.compile(r"\bevt-[23456789abcdefghjkmnpqrstuvwxyz]+\b")
ENTITY_PATTERN = r"([a-z][a-z0-9-]*-[23456789abcdefghjkmnpqrstuvwxyz]+)"
LINK_PATTERN = r"(link-[23456789abcdefghjkmnpqrstuvwxyz]+)"


class SemanticAuditError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class SupportedDecision:
    decision: str
    entity_id: str | None = None


@dataclass(frozen=True)
class SemanticAuditResult:
    task_id: str
    minimal_support_sets: tuple[tuple[str, ...], ...]
    expected_decision: SupportedDecision


def _event_id(task_data: Mapping[str, Any]) -> str:
    question = task_data.get("question")
    if not isinstance(question, str):
        raise SemanticAuditError("question must be a string")
    matches = set(EVENT_PATTERN.findall(question))
    if len(matches) != 1:
        raise SemanticAuditError(
            f"question must contain exactly one event identifier, found {sorted(matches)}"
        )
    return matches.pop()


def _source_records(task_data: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sources = task_data.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise SemanticAuditError("sources must be a non-empty object")
    records: dict[str, Mapping[str, Any]] = {}
    for source_id, record in sources.items():
        if not isinstance(source_id, str) or not isinstance(record, dict):
            raise SemanticAuditError("source IDs and records must be objects")
        for field in (
            "content",
            "authority_class",
            "declared_reliability",
            "lineage_group",
        ):
            if field not in record:
                raise SemanticAuditError(f"{source_id} is missing {field}")
        records[source_id] = record
    return records


def _trusted(record: Mapping[str, Any], authorities: set[str], minimum: float) -> bool:
    reliability = record.get("declared_reliability")
    return (
        record.get("authority_class") in authorities
        and isinstance(reliability, int | float)
        and not isinstance(reliability, bool)
        and float(reliability) >= minimum
    )


def _direct_answers(event_id: str, text: str) -> set[str]:
    event = re.escape(event_id)
    patterns = (
        rf"The signed decision register for {event} establishes {ENTITY_PATTERN} "
        r"as the controlling",
        rf"The signed decision for {event} names {ENTITY_PATTERN} "
        r"as the controlling",
        rf"The independent audit for {event} identifies {ENTITY_PATTERN} "
        r"as the controlling",
        rf"The final control record independently confirms {ENTITY_PATTERN} "
        rf"for {event}\.",
    )
    answers: set[str] = set()
    for pattern in patterns:
        answers.update(re.findall(pattern, text))
    return answers


def infer_supported_decisions(
    task_data: Mapping[str, Any],
    opened_source_ids: Iterable[str],
) -> frozenset[SupportedDecision]:
    event_id = _event_id(task_data)
    sources = _source_records(task_data)
    opened = tuple(dict.fromkeys(opened_source_ids))
    unknown = set(opened).difference(sources)
    if unknown:
        raise SemanticAuditError(f"unknown opened sources: {sorted(unknown)}")

    decisions: set[SupportedDecision] = set()
    initial_context = task_data.get("initial_context")
    if not isinstance(initial_context, str):
        raise SemanticAuditError("initial_context must be a string")
    for entity_id in _direct_answers(event_id, initial_context):
        decisions.add(SupportedDecision("answer", entity_id))

    event_links: set[str] = set()
    link_entities: dict[str, set[str]] = {}
    ambiguity_sources: set[str] = set()
    completeness_sources: set[str] = set()

    for source_id in opened:
        record = sources[source_id]
        content = record.get("content")
        if not isinstance(content, str):
            raise SemanticAuditError(f"{source_id} content must be a string")

        if _trusted(
            record,
            {"primary-control-record", "independent-audit-record"},
            0.97,
        ):
            for entity_id in _direct_answers(event_id, content):
                decisions.add(SupportedDecision("answer", entity_id))

        if _trusted(
            record,
            {"primary-control-record", "independent-audit-record"},
            0.97,
        ):
            event_links.update(
                re.findall(
                    rf"(?:control record|audit) maps {re.escape(event_id)} to "
                    rf"(?:independent )?correlation key {LINK_PATTERN}",
                    content,
                )
            )
        if _trusted(record, {"immutable-control-ledger"}, 0.99):
            event_links.update(
                re.findall(
                    rf"immutable ledger maps {re.escape(event_id)} to payload hash "
                    rf"{LINK_PATTERN}",
                    content,
                )
            )
        if _trusted(record, {"signed-ingestion-receipt"}, 0.98):
            for link_id, entity_id in re.findall(
                rf"(?:signed receipt|second signed receipt) maps "
                rf"(?:correlation key|payload hash) {LINK_PATTERN} to {ENTITY_PATTERN}",
                content,
            ):
                link_entities.setdefault(link_id, set()).add(entity_id)

        if (
            _trusted(record, {"signed-operational-log"}, 0.98)
            and event_id in content
            and "cannot distinguish which" in content
            and "controlled the event" in content
        ):
            ambiguity_sources.add(source_id)
        if (
            _trusted(record, {"independent-audit-record"}, 0.97)
            and "records are complete for the window" in content
            and "no additional attribution evidence" in content
        ):
            completeness_sources.add(source_id)

    for link_id in event_links:
        for entity_id in link_entities.get(link_id, set()):
            decisions.add(SupportedDecision("answer", entity_id))

    if ambiguity_sources and completeness_sources:
        decisions.add(SupportedDecision("insufficient"))
    return frozenset(decisions)


def _expected_decision(expected: Mapping[str, Any]) -> SupportedDecision:
    decision = expected.get("expected_decision")
    entity_id = expected.get("expected_entity_id")
    if decision == "insufficient" and entity_id is None:
        return SupportedDecision("insufficient")
    if decision == "answer" and isinstance(entity_id, str) and entity_id:
        return SupportedDecision("answer", entity_id)
    raise SemanticAuditError("hidden expected decision is malformed")


def _minimal_support_sets(
    task_data: Mapping[str, Any], expected: SupportedDecision
) -> tuple[tuple[str, ...], ...]:
    sources = tuple(_source_records(task_data))
    supporting: list[frozenset[str]] = []
    for size in range(len(sources) + 1):
        for subset in combinations(sources, size):
            decisions = infer_supported_decisions(task_data, subset)
            unexpected = decisions.difference({expected})
            if unexpected:
                raise SemanticAuditError(
                    f"material supports unexpected decisions {sorted(unexpected)} "
                    f"from sources {sorted(subset)}"
                )
            if expected in decisions:
                supporting.append(frozenset(subset))

    minimal = [
        subset
        for subset in supporting
        if not any(other < subset for other in supporting)
    ]
    return tuple(
        tuple(source_id for source_id in sources if source_id in subset)
        for subset in sorted(minimal, key=lambda item: (len(item), sorted(item)))
    )


def audit_task_package(task_dir: Path) -> SemanticAuditResult:
    task_data_path = task_dir / "environment" / "evidence-sidecar" / "task_data.json"
    expected_path = task_dir / "tests" / "expected.json"
    task_data = json.loads(task_data_path.read_text())
    expected = json.loads(expected_path.read_text())
    if task_data.get("task_id") != expected.get("task_id"):
        raise SemanticAuditError("task and verifier IDs disagree")

    expected_decision = _expected_decision(expected)
    material_sets = _minimal_support_sets(task_data, expected_decision)
    verifier_sets = tuple(
        tuple(path) for path in expected.get("accepted_proof_sets", [])
    )
    material_normalized = {frozenset(path) for path in material_sets}
    verifier_normalized = {frozenset(path) for path in verifier_sets}
    if material_normalized != verifier_normalized:
        raise SemanticAuditError(
            f"{task_dir.name}: material minimal supports "
            f"{sorted(map(sorted, material_normalized))} do not match verifier paths "
            f"{sorted(map(sorted, verifier_normalized))}"
        )
    if len(material_normalized) != len(material_sets):
        raise SemanticAuditError(f"{task_dir.name}: duplicate material support sets")
    return SemanticAuditResult(
        task_id=task_dir.name,
        minimal_support_sets=material_sets,
        expected_decision=expected_decision,
    )


def audit_dataset(dataset_dir: Path) -> list[SemanticAuditResult]:
    dataset = tomllib.loads((dataset_dir / "dataset.toml").read_text())
    rows = dataset.get("tasks")
    if not isinstance(rows, list) or not rows:
        raise SemanticAuditError("dataset.toml must contain task rows")
    results = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise SemanticAuditError("dataset task row is malformed")
        task_id = row["name"].split("/", 1)[-1]
        results.append(audit_task_package(dataset_dir / task_id))
    if len({result.task_id for result in results}) != len(results):
        raise SemanticAuditError("dataset contains duplicate task IDs")
    return results
