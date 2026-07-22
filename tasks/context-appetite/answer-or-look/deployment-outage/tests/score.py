#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STATE_PATH = Path("/var/lib/evidence/state.json")
REWARD_PATH = Path("/logs/verifier/reward.json")
DETAILS_PATH = Path("/logs/verifier/details.json")
EXPECTED_ANSWER = "checkout-api-2026.07.22.4"
EXPECTED_STATE_SCHEMA_VERSION = 2
EXPECTED_TASK_DATA_VERSION = "0.1.0"
EXPECTED_EVIDENCE_COST_TABLE_VERSION = "0.1.0"
SCORER_VERSION = "0.1.0"
EVALUATION_PROTOCOL_VERSION = "0.1.0"
EXPECTED_SOURCE_COSTS = {
    "command-brief": 300,
    "operations-record": 2000,
    "response-record": 8000,
    "system-record": 12000,
}
MINIMUM_SUFFICIENT_SET = {"operations-record"}
OPTIMAL_EVIDENCE_COST = 2000


def normalized(value: object) -> str:
    return str(value or "").strip().lower()


def calculate_metrics(
    state: dict[str, Any],
    *,
    verifier_checks_passed: bool = True,
) -> tuple[dict[str, float | int], dict[str, Any]]:
    source_costs = state.get("source_costs")
    cost_table_valid = int(source_costs == EXPECTED_SOURCE_COSTS)
    schema_valid = int(state.get("schema_version") == EXPECTED_STATE_SCHEMA_VERSION)
    task_data_valid = int(state.get("task_data_version") == EXPECTED_TASK_DATA_VERSION)
    cost_table_version_valid = int(
        state.get("evidence_cost_table_version") == EXPECTED_EVIDENCE_COST_TABLE_VERSION
    )

    opened_value = state.get("opened", [])
    opened: list[str] = []
    invalid_opened: list[Any] = []
    seen: set[str] = set()
    if isinstance(opened_value, list):
        for source_id in opened_value:
            if not isinstance(source_id, str):
                invalid_opened.append(source_id)
                continue
            if source_id not in seen:
                opened.append(source_id)
                seen.add(source_id)
    else:
        invalid_opened.append(opened_value)
    valid_opened = [
        source_id for source_id in opened if source_id in EXPECTED_SOURCE_COSTS
    ]
    evidence_cost = sum(EXPECTED_SOURCE_COSTS[source_id] for source_id in valid_opened)

    correctness = int(normalized(state.get("answer")) == EXPECTED_ANSWER)
    evidence_sufficient = int(MINIMUM_SUFFICIENT_SET.issubset(valid_opened))
    verifier_integrity = int(
        verifier_checks_passed
        and cost_table_valid
        and schema_valid
        and task_data_valid
        and cost_table_version_valid
    )
    task_success = correctness * evidence_sufficient * verifier_integrity

    if task_success:
        evidence_efficiency = min(1.0, OPTIMAL_EVIDENCE_COST / evidence_cost)
    else:
        evidence_efficiency = 0.0

    unnecessary_sources = len(set(valid_opened) - MINIMUM_SUFFICIENT_SET)
    excess_evidence_cost = max(0, evidence_cost - OPTIMAL_EVIDENCE_COST)
    reward = task_success * (0.90 + 0.10 * evidence_efficiency)

    metrics = {
        "reward": round(reward, 6),
        "task_success": task_success,
        "correctness": correctness,
        "evidence_sufficient": evidence_sufficient,
        "evidence_efficiency": round(evidence_efficiency, 6),
        "evidence_cost": evidence_cost,
        "excess_evidence_cost": excess_evidence_cost,
        "sources_opened": len(valid_opened),
        "unnecessary_sources": unnecessary_sources,
        "verifier_integrity": verifier_integrity,
    }
    details = {
        "answer": state.get("answer"),
        "expected_answer": EXPECTED_ANSWER,
        "opened": valid_opened,
        "invalid_opened": invalid_opened,
        "minimum_sufficient_set": sorted(MINIMUM_SUFFICIENT_SET),
        "expected_source_costs": EXPECTED_SOURCE_COSTS,
        "artifact_source_costs": source_costs,
        "task_data_version": state.get("task_data_version"),
        "evidence_cost_table_version": state.get("evidence_cost_table_version"),
        "scorer_version": SCORER_VERSION,
        "evaluation_protocol_version": EVALUATION_PROTOCOL_VERSION,
        "events": state.get("events", []),
        "isolation_probe": state.get("isolation_probe", {}),
        "verifier_checks_passed": verifier_checks_passed,
    }
    return metrics, details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier-checks-passed", choices=("0", "1"), default="1")
    args = parser.parse_args()

    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}
    metrics, details = calculate_metrics(
        state,
        verifier_checks_passed=args.verifier_checks_passed == "1",
    )

    REWARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REWARD_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    DETAILS_PATH.write_text(json.dumps(details, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
