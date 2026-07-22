#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


STATE_PATH = Path("/var/lib/evidence/state.json")
REWARD_PATH = Path("/logs/verifier/reward.json")
DETAILS_PATH = Path("/logs/verifier/details.json")
EXPECTED_ANSWER = "checkout-api-2026.07.22.4"
SOURCE_COSTS = {
    "incident-summary": 300,
    "deployment-log": 2000,
    "team-conversation": 8000,
    "metrics-export": 12000,
}
MINIMUM_SUFFICIENT_SET = {"deployment-log"}
OPTIMAL_CONTEXT_TOKENS = 2000


def normalized(value: object) -> str:
    return str(value or "").strip().lower()


def calculate_metrics(state: dict[str, object]) -> tuple[dict[str, float | int], dict[str, object]]:
    opened = list(dict.fromkeys(state.get("opened", [])))
    valid_opened = [source_id for source_id in opened if source_id in SOURCE_COSTS]
    context_tokens = sum(SOURCE_COSTS[source_id] for source_id in valid_opened)

    correctness = int(normalized(state.get("answer")) == EXPECTED_ANSWER)
    evidence_sufficient = int(MINIMUM_SUFFICIENT_SET.issubset(valid_opened))
    unnecessary_sources = len(set(valid_opened) - MINIMUM_SUFFICIENT_SET)
    context_regret_tokens = max(0, context_tokens - OPTIMAL_CONTEXT_TOKENS)

    if evidence_sufficient:
        context_efficiency = min(1.0, OPTIMAL_CONTEXT_TOKENS / context_tokens)
    else:
        context_efficiency = 0.0

    stopped_correctly = int(
        correctness
        and valid_opened == ["deployment-log"]
        and state.get("events", [])
        and state["events"][-1].get("action") == "answer"
    )

    reward = correctness * (
        0.80 + 0.15 * context_efficiency + 0.05 * stopped_correctly
    )

    metrics = {
        "reward": round(reward, 6),
        "correctness": correctness,
        "context_efficiency": round(context_efficiency, 6),
        "stopped_correctly": stopped_correctly,
        "evidence_sufficient": evidence_sufficient,
        "context_tokens": context_tokens,
        "context_regret_tokens": context_regret_tokens,
        "sources_opened": len(valid_opened),
        "unnecessary_sources": unnecessary_sources,
    }
    details = {
        "answer": state.get("answer"),
        "expected_answer": EXPECTED_ANSWER,
        "opened": valid_opened,
        "minimum_sufficient_set": sorted(MINIMUM_SUFFICIENT_SET),
        "events": state.get("events", []),
    }
    return metrics, details


def main() -> None:
    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}
    metrics, details = calculate_metrics(state)

    REWARD_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    DETAILS_PATH.write_text(json.dumps(details, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
