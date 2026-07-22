#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATE_PATH = Path("/evidence-artifacts/state.json")
REWARD_PATH = Path("/logs/verifier/reward.json")
DETAILS_PATH = Path("/logs/verifier/details.json")
EXPECTED_PATH = Path(__file__).with_name("expected.json")
EXPECTED: dict[str, Any] = json.loads(EXPECTED_PATH.read_text())


def normalized(value: object) -> str:
    return str(value or "").strip().lower()


def _nonnegative_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def load_state_artifact(path: Path = STATE_PATH) -> tuple[dict[str, Any], list[str]]:
    if not path.is_file():
        return {}, ["evidence artifact is missing"]
    try:
        state = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {}, [f"evidence artifact is unreadable: {type(exc).__name__}"]
    if not isinstance(state, dict):
        return {}, ["evidence artifact is not a JSON object"]
    return state, []


def _opened_sources(
    state: dict[str, Any],
    source_costs: dict[str, int],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    opened: list[str] = []
    raw = state.get("opened")
    if not isinstance(raw, list):
        return [], ["opened is not a list"]
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, str):
            errors.append("opened contains a non-string source")
            continue
        if value not in source_costs:
            errors.append(f"opened contains unknown source {value!r}")
            continue
        if value in seen:
            errors.append(f"opened contains duplicate source {value!r}")
            continue
        opened.append(value)
        seen.add(value)
    return opened, errors


def _validate_payload(
    event: dict[str, Any],
    source_id: str,
    source_payload_bytes: dict[str, int],
    source_token_proxy: dict[str, int],
) -> tuple[list[str], int, int]:
    errors: list[str] = []
    payload_bytes = _nonnegative_int(event.get("payload_bytes"))
    payload_tokens = _nonnegative_int(event.get("payload_token_proxy"))
    if payload_bytes != source_payload_bytes[source_id]:
        errors.append(f"payload byte count mismatch for {source_id!r}")
    if payload_tokens != source_token_proxy[source_id]:
        errors.append(f"payload token proxy mismatch for {source_id!r}")
    return errors, payload_bytes or 0, payload_tokens or 0


def _validate_events(
    state: dict[str, Any],
    source_costs: dict[str, int],
    source_payload_bytes: dict[str, int],
    source_token_proxy: dict[str, int],
) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counters = {
        "duplicate_open_attempts": 0,
        "unknown_source_attempts": 0,
        "list_calls": 0,
        "status_calls": 0,
        "payload_bytes": 0,
        "token_proxy": 0,
    }
    opened_from_events: list[str] = []
    event_cost = 0
    answer_from_events: str | None = None
    answer_seen = False
    events = state.get("events")
    if not isinstance(events, list):
        return ["events is not a list"], counters

    for event in events:
        if not isinstance(event, dict):
            errors.append("events contains a non-object entry")
            continue
        action = event.get("action")
        if (
            action in {"open", "open_duplicate", "open_unknown", "answer"}
            and answer_seen
        ):
            errors.append(f"{action!r} event appears after the final answer")

        if action == "list":
            counters["list_calls"] += 1
            if event.get("evidence_cost") != 0:
                errors.append("list event has non-zero evidence cost")
        elif action == "status":
            counters["status_calls"] += 1
            if event.get("evidence_cost") != 0:
                errors.append("status event has non-zero evidence cost")
        elif action == "open":
            source_id = event.get("source_id")
            if not isinstance(source_id, str) or source_id not in source_costs:
                errors.append(f"open event has unknown source {source_id!r}")
                continue
            if source_id in opened_from_events:
                errors.append(f"source {source_id!r} has two charged open events")
                continue
            expected_cost = source_costs[source_id]
            if event.get("evidence_cost") != expected_cost:
                errors.append(f"open event cost mismatch for {source_id!r}")
            payload_errors, payload_bytes, payload_tokens = _validate_payload(
                event,
                source_id,
                source_payload_bytes,
                source_token_proxy,
            )
            errors.extend(payload_errors)
            counters["payload_bytes"] += payload_bytes
            counters["token_proxy"] += payload_tokens
            opened_from_events.append(source_id)
            event_cost += expected_cost
        elif action == "open_duplicate":
            counters["duplicate_open_attempts"] += 1
            source_id = event.get("source_id")
            if (
                not isinstance(source_id, str)
                or source_id not in opened_from_events
                or event.get("evidence_cost") != 0
            ):
                errors.append("invalid duplicate-open event")
                continue
            payload_errors, payload_bytes, payload_tokens = _validate_payload(
                event,
                source_id,
                source_payload_bytes,
                source_token_proxy,
            )
            errors.extend(payload_errors)
            counters["payload_bytes"] += payload_bytes
            counters["token_proxy"] += payload_tokens
        elif action == "open_unknown":
            counters["unknown_source_attempts"] += 1
            if event.get("source_id") in source_costs:
                errors.append("unknown-open event names a known source")
            if event.get("evidence_cost") != 0:
                errors.append("unknown-open event has non-zero evidence cost")
        elif action == "answer":
            if answer_seen:
                errors.append("more than one answer event was recorded")
            answer_seen = True
            answer_from_events = event.get("answer")
            if not isinstance(answer_from_events, str) or not answer_from_events:
                errors.append("answer event is empty or not a string")
        else:
            errors.append(f"unknown event action {action!r}")

    opened, _ = _opened_sources(state, source_costs)
    if opened_from_events != opened:
        errors.append("opened sources do not match the charged event sequence")
    if event_cost != state.get("observed_evidence_cost"):
        errors.append("event cost does not match observed_evidence_cost")
    if counters["payload_bytes"] != state.get("observed_evidence_payload_bytes"):
        errors.append("event bytes do not match observed_evidence_payload_bytes")
    if counters["token_proxy"] != state.get("observed_evidence_token_proxy"):
        errors.append("event token proxy does not match observed_evidence_token_proxy")
    if answer_from_events != state.get("answer"):
        errors.append("answer does not match the final answer event")
    return errors, counters


def calculate_metrics(
    state: dict[str, Any],
    *,
    verifier_checks_passed: bool = True,
    external_integrity_errors: tuple[str, ...] | list[str] = (),
) -> tuple[dict[str, float | int], dict[str, Any]]:
    source_costs = {
        source_id: int(cost) for source_id, cost in EXPECTED["source_costs"].items()
    }
    source_payload_bytes = {
        source_id: int(value)
        for source_id, value in EXPECTED["source_payload_bytes"].items()
    }
    source_token_proxy = {
        source_id: int(value)
        for source_id, value in EXPECTED["source_token_proxy"].items()
    }
    required_sources = set(EXPECTED["required_sources"])
    integrity_errors = list(external_integrity_errors)

    checks = {
        "schema_version": state.get("schema_version")
        == EXPECTED["state_schema_version"],
        "task_id": state.get("task_id") == EXPECTED["task_id"],
        "task_data_version": state.get("task_data_version")
        == EXPECTED["task_data_version"],
        "cost_table_version": state.get("evidence_cost_table_version")
        == EXPECTED["evidence_cost_table_version"],
        "source_costs": state.get("source_costs") == source_costs,
        "source_order": state.get("source_order") == EXPECTED["source_order"],
        "finalized": state.get("finalized") is True,
        "agent_probe_telemetry_absent": "isolation_probe" not in state,
        "snapshot_credential_absent": "snapshot_token" not in state,
        "verifier_checks": verifier_checks_passed,
    }
    integrity_errors.extend(name for name, passed in checks.items() if not passed)

    opened, opened_errors = _opened_sources(state, source_costs)
    integrity_errors.extend(opened_errors)
    observed_cost = sum(source_costs[source_id] for source_id in opened)
    if state.get("observed_evidence_cost") != observed_cost:
        integrity_errors.append("observed_evidence_cost does not match opened sources")

    event_errors, counters = _validate_events(
        state,
        source_costs,
        source_payload_bytes,
        source_token_proxy,
    )
    integrity_errors.extend(event_errors)

    request_count = _nonnegative_int(state.get("agent_request_count"))
    event_count = (
        len(state.get("events", [])) if isinstance(state.get("events"), list) else -1
    )
    if request_count is None:
        integrity_errors.append("agent_request_count is not a non-negative integer")
        request_count = 0
    elif request_count < event_count:
        integrity_errors.append("agent_request_count is smaller than the event count")

    snapshot = state.get("snapshot")
    expected_snapshot = {
        "complete": True,
        "authentication": "sidecar-file-token-v1",
        "task_id": EXPECTED["task_id"],
        "event_count": event_count,
        "opened_count": len(opened),
        "agent_request_count": request_count,
        "observed_evidence_cost": observed_cost,
        "observed_evidence_payload_bytes": counters["payload_bytes"],
        "observed_evidence_token_proxy": counters["token_proxy"],
    }
    if snapshot != expected_snapshot:
        integrity_errors.append("snapshot metadata mismatch")

    verifier_integrity = int(not integrity_errors)
    answer = normalized(state.get("answer"))
    expected_answer = normalized(EXPECTED["expected_answer"])
    correctness = int(answer == expected_answer)
    evidence_sufficient = int(required_sources.issubset(opened))
    task_success = correctness * evidence_sufficient * verifier_integrity

    task_cost_cap = int(EXPECTED["task_cost_cap"])
    cost_score = max(0.0, 1.0 - observed_cost / task_cost_cap)
    hindsight_minimum_cost = int(EXPECTED["hindsight_minimum_cost"])
    hindsight_cost_gap = max(0, observed_cost - hindsight_minimum_cost)
    outside_hindsight = len(set(opened) - required_sources)
    abstained = int(answer.startswith("insufficient"))
    expected_abstention = int(expected_answer.startswith("insufficient"))
    selective_decision_correct = int(bool(answer) and abstained == expected_abstention)

    metrics = {
        "reward": task_success,
        "task_success": task_success,
        "correctness": correctness,
        "evidence_sufficient": evidence_sufficient,
        "cost_score": round(cost_score, 6),
        "observed_evidence_cost": observed_cost,
        "evidence_payload_bytes": counters["payload_bytes"],
        "evidence_token_proxy": counters["token_proxy"],
        "sources_opened": len(opened),
        "agent_requests": request_count,
        "list_calls": counters["list_calls"],
        "status_calls": counters["status_calls"],
        "zero_cost_tool_calls": counters["list_calls"] + counters["status_calls"],
        "hindsight_minimum_cost": hindsight_minimum_cost,
        "hindsight_cost_gap": hindsight_cost_gap,
        "sources_outside_hindsight_minimum": outside_hindsight,
        "abstained": abstained,
        "selective_decision_correct": selective_decision_correct,
        "duplicate_open_attempts": counters["duplicate_open_attempts"],
        "unknown_source_attempts": counters["unknown_source_attempts"],
        "verifier_integrity": verifier_integrity,
    }
    details = {
        "answer": state.get("answer"),
        "expected_answer": EXPECTED["expected_answer"],
        "source_sequence": opened,
        "required_sources": sorted(required_sources),
        "expected_source_costs": source_costs,
        "artifact_source_costs": state.get("source_costs"),
        "expected_source_payload_bytes": source_payload_bytes,
        "expected_source_token_proxy": source_token_proxy,
        "task_data_version": state.get("task_data_version"),
        "evidence_cost_table_version": state.get("evidence_cost_table_version"),
        "scorer_version": EXPECTED["scorer_version"],
        "evaluation_protocol_version": EXPECTED["evaluation_protocol_version"],
        "events": state.get("events", []),
        "snapshot": snapshot,
        "integrity_errors": integrity_errors,
    }
    return metrics, details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier-checks-passed", choices=("0", "1"), default="1")
    args = parser.parse_args()

    state, artifact_errors = load_state_artifact()
    metrics, details = calculate_metrics(
        state,
        verifier_checks_passed=args.verifier_checks_passed == "1",
        external_integrity_errors=artifact_errors,
    )
    REWARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REWARD_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    DETAILS_PATH.write_text(json.dumps(details, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
