#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


STATE_PATH = Path("/evidence-artifacts/state.json")
REWARD_PATH = Path("/logs/verifier/reward.json")
DETAILS_PATH = Path("/logs/verifier/details.json")
EXPECTED_PATH = Path(__file__).with_name("expected.json")
EXPECTED: dict[str, Any] = json.loads(EXPECTED_PATH.read_text())


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


def canonical_answer(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return tuple(canonical_answer(item) for item in value)
    if isinstance(value, dict):
        items: list[tuple[str, object]] = []
        for key, item in sorted(value.items()):
            canonical = canonical_answer(item)
            if key in {"candidate_ids", "entity_ids"} and isinstance(canonical, tuple):
                canonical = tuple(sorted(canonical))
            items.append((key, canonical))
        return tuple(items)
    return value


def submission_contract(
    submission: object,
) -> tuple[int, str | None, object, float | None, list[str]]:
    errors: list[str] = []
    if not isinstance(submission, dict):
        return 0, None, None, None, ["submission is not an object"]
    if set(submission) != {"decision", "answer", "confidence"}:
        errors.append("submission fields do not match the typed contract")
    decision = submission.get("decision")
    answer = submission.get("answer")
    confidence = submission.get("confidence")
    if decision not in {"answer", "insufficient"}:
        errors.append("decision is not answer or insufficient")
        decision = None
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, int | float)
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
    ):
        errors.append("confidence is not a finite number between zero and one")
        confidence = None
    else:
        confidence = float(confidence)
    if decision == "answer":
        if (
            not isinstance(answer, dict)
            or set(answer) != {"entity_id"}
            or not isinstance(answer.get("entity_id"), str)
            or not answer["entity_id"].strip()
        ):
            errors.append("answer decision requires exactly one non-empty entity_id")
    elif decision == "insufficient" and answer is not None:
        errors.append("insufficient decision requires answer=null")
    return int(not errors), decision, answer, confidence, errors


def _opened_sources(
    state: dict[str, Any], source_costs: dict[str, int]
) -> tuple[list[str], list[str]]:
    raw = state.get("opened")
    if not isinstance(raw, list):
        return [], ["opened is not a list"]
    opened: list[str] = []
    errors: list[str] = []
    for value in raw:
        if not isinstance(value, str) or value not in source_costs:
            errors.append(f"opened contains unknown source {value!r}")
        elif value in opened:
            errors.append(f"opened contains duplicate source {value!r}")
        else:
            opened.append(value)
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
    submission_from_events: object = None
    submission_seen = False
    events = state.get("events")
    if not isinstance(events, list):
        return ["events is not a list"], counters

    for event in events:
        if not isinstance(event, dict):
            errors.append("events contains a non-object entry")
            continue
        action = event.get("action")
        if (
            action in {"open", "open_duplicate", "open_unknown", "submit"}
            and submission_seen
        ):
            errors.append(f"{action!r} event appears after the final submission")
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
                event, source_id, source_payload_bytes, source_token_proxy
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
                event, source_id, source_payload_bytes, source_token_proxy
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
        elif action == "submit":
            if submission_seen:
                errors.append("more than one submission event was recorded")
            submission_seen = True
            submission_from_events = event.get("submission")
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
    if submission_from_events != state.get("submission"):
        errors.append("submission does not match the final submission event")
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
    accepted_proof_sets = [set(path) for path in EXPECTED["accepted_proof_sets"]]
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
        "snapshot_credential_absent": "snapshot_token" not in state,
        "agent_integrity_claim_absent": "verifier_integrity" not in state,
        "verifier_checks": verifier_checks_passed,
    }
    integrity_errors.extend(name for name, passed in checks.items() if not passed)
    opened, opened_errors = _opened_sources(state, source_costs)
    integrity_errors.extend(opened_errors)
    observed_cost = sum(source_costs[source_id] for source_id in opened)
    if state.get("observed_evidence_cost") != observed_cost:
        integrity_errors.append("observed_evidence_cost does not match opened sources")
    event_errors, counters = _validate_events(
        state, source_costs, source_payload_bytes, source_token_proxy
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

    format_contract_met, decision, answer, confidence, format_errors = (
        submission_contract(state.get("submission"))
    )
    expected_decision = EXPECTED["expected_decision"]
    if expected_decision == "insufficient":
        semantic_success = int(decision == "insufficient")
    else:
        expected_answer = {"entity_id": EXPECTED["expected_entity_id"]}
        semantic_success = int(
            decision == "answer"
            and canonical_answer(answer) == canonical_answer(expected_answer)
        )
    opened_set = set(opened)
    proof_sufficient = int(
        any(path.issubset(opened_set) for path in accepted_proof_sets)
    )
    verifier_integrity = int(not integrity_errors)
    task_success = (
        semantic_success * proof_sufficient * format_contract_met * verifier_integrity
    )
    abstained = int(decision == "insufficient")
    expected_abstention = int(expected_decision == "insufficient")
    abstention_mode_match = int(
        decision in {"answer", "insufficient"} and abstained == expected_abstention
    )
    supported_abstention = int(
        abstained and expected_abstention and semantic_success and proof_sufficient
    )
    unjustified_abstention = int(abstained and not expected_abstention)
    if semantic_success and proof_sufficient:
        policy_utility = 100 - observed_cost
    elif unjustified_abstention:
        policy_utility = -50 - observed_cost
    else:
        policy_utility = -200 - observed_cost

    metrics = {
        "reward": task_success,
        "task_success": task_success,
        "semantic_success": semantic_success,
        "proof_sufficient": proof_sufficient,
        "format_contract_met": format_contract_met,
        "correctness": semantic_success,
        "evidence_sufficient": proof_sufficient,
        "observed_evidence_cost": observed_cost,
        "evidence_payload_bytes": counters["payload_bytes"],
        "evidence_token_proxy": counters["token_proxy"],
        "sources_opened": len(opened),
        "agent_requests": request_count,
        "list_calls": counters["list_calls"],
        "status_calls": counters["status_calls"],
        "zero_cost_tool_calls": counters["list_calls"] + counters["status_calls"],
        "hindsight_minimum_cost": int(EXPECTED["hindsight_minimum_cost"]),
        "abstained": abstained,
        "abstention_mode_match": abstention_mode_match,
        "supported_abstention": supported_abstention,
        "unjustified_abstention": unjustified_abstention,
        "duplicate_open_attempts": counters["duplicate_open_attempts"],
        "unknown_source_attempts": counters["unknown_source_attempts"],
        "policy_utility": policy_utility,
        "confidence": confidence if confidence is not None else -1.0,
        "verifier_integrity": verifier_integrity,
    }
    details = {
        "submission": state.get("submission"),
        "expected_decision": expected_decision,
        "expected_answer": EXPECTED["expected_entity_id"],
        "source_sequence": opened,
        "accepted_proof_sets": EXPECTED["accepted_proof_sets"],
        "source_costs": source_costs,
        "task_data_version": state.get("task_data_version"),
        "evidence_cost_table_version": state.get("evidence_cost_table_version"),
        "scorer_version": EXPECTED["scorer_version"],
        "evaluation_protocol_version": EXPECTED["evaluation_protocol_version"],
        "events": state.get("events", []),
        "snapshot": snapshot,
        "format_errors": format_errors,
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
