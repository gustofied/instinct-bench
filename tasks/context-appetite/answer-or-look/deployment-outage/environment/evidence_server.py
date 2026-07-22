#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socketserver
import tempfile
import threading
from pathlib import Path
from typing import Any


SOCKET_PATH = Path("/run/instinct-bench-evidence.sock")
STATE_PATH = Path("/var/lib/evidence/state.json")

QUESTION = (
    "Which deployment caused the checkout outage from 14:32 to 14:47 UTC?"
)
INITIAL_CONTEXT = (
    "Checkout requests began returning HTTP 500 errors at 14:32 UTC. "
    "Several services had deployments near that time."
)

SOURCES = {
    "incident-summary": {
        "cost": 300,
        "description": "High-level incident timeline and impact",
        "content": (
            "Incident INC-4821 began at 14:32 UTC and affected 38% of checkout "
            "requests. The incident commander initiated a rollback at 14:44 UTC. "
            "Error rates returned to baseline at 14:47 UTC. The summary names no "
            "deployment or change ID."
        ),
    },
    "deployment-log": {
        "cost": 2000,
        "description": "Deployment and rollback records with change IDs",
        "content": (
            "13:55 UTC deploy payments-api-2026.07.22.3 completed; no rollback.\n"
            "14:29 UTC deploy checkout-api-2026.07.22.4 completed.\n"
            "14:31 UTC deploy catalog-api-2026.07.22.2 completed; no rollback.\n"
            "14:44 UTC rollback checkout-api-2026.07.22.4 initiated for elevated "
            "checkout HTTP 500 errors.\n"
            "14:47 UTC rollback completed; checkout errors returned to baseline."
        ),
    },
    "team-conversation": {
        "cost": 8000,
        "description": "Messages from the incident response channel",
        "content": (
            "14:35 IC: Checkout is failing in three regions. Payments and catalog "
            "owners report healthy services.\n"
            "14:42 Checkout on-call: The most recent checkout rollout is the prime "
            "suspect. I am requesting rollback approval.\n"
            "14:48 IC: Recovery confirmed after the checkout rollback. Please pull "
            "the exact deployment ID from the deployment log for the report."
        ),
    },
    "metrics-export": {
        "cost": 12000,
        "description": "Service-level error and latency observations",
        "content": (
            "14:32-14:46 UTC: checkout-api HTTP 500 rate 38%, p95 latency 2.8 s.\n"
            "14:32-14:46 UTC: payments-api HTTP 500 rate 0.1%, p95 latency 210 ms.\n"
            "14:32-14:46 UTC: catalog-api HTTP 500 rate 0.2%, p95 latency 180 ms.\n"
            "14:47 UTC: checkout-api HTTP 500 rate returned to 0.2%.\n"
            "Metrics are keyed by service, not deployment ID."
        ),
    },
}

_state_lock = threading.Lock()


def initial_state() -> dict[str, Any]:
    return {
        "opened": [],
        "context_tokens": 0,
        "answer": None,
        "events": [],
    }


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return initial_state()
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(dir=STATE_PATH.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, STATE_PATH)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def public_sources() -> list[dict[str, Any]]:
    return [
        {
            "id": source_id,
            "cost": source["cost"],
            "description": source["description"],
        }
        for source_id, source in SOURCES.items()
    ]


def process(request: dict[str, Any]) -> dict[str, Any]:
    action = request.get("action")
    with _state_lock:
        state = load_state()

        if action == "ping":
            return {"ok": True, "status": "ready"}

        if action == "list":
            return {
                "ok": True,
                "question": QUESTION,
                "initial_context": INITIAL_CONTEXT,
                "sources": public_sources(),
            }

        if action == "status":
            return {
                "ok": True,
                "opened": state["opened"],
                "context_tokens": state["context_tokens"],
                "submitted": state["answer"] is not None,
                "answer": state["answer"],
            }

        if action == "open":
            if state["answer"] is not None:
                return {"ok": False, "error": "The submitted answer is final."}
            source_id = request.get("source_id")
            if source_id not in SOURCES:
                return {"ok": False, "error": f"Unknown source: {source_id}"}

            charged = 0
            if source_id not in state["opened"]:
                charged = SOURCES[source_id]["cost"]
                state["opened"].append(source_id)
                state["context_tokens"] += charged
                state["events"].append(
                    {"action": "open", "source_id": source_id, "cost": charged}
                )
                save_state(state)

            return {
                "ok": True,
                "source_id": source_id,
                "charged_tokens": charged,
                "context_tokens": state["context_tokens"],
                "content": SOURCES[source_id]["content"],
            }

        if action == "answer":
            if state["answer"] is not None:
                return {"ok": False, "error": "The submitted answer is final."}
            answer = str(request.get("answer", "")).strip()
            if not answer or len(answer) > 200:
                return {
                    "ok": False,
                    "error": "Submit a non-empty answer under 200 characters.",
                }
            state["answer"] = answer
            state["events"].append({"action": "answer", "answer": answer})
            save_state(state)
            return {
                "ok": True,
                "submitted": answer,
                "context_tokens": state["context_tokens"],
            }

        return {"ok": False, "error": f"Unknown action: {action}"}


class RequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            request = json.loads(self.rfile.readline())
            response = process(request)
        except Exception as exc:
            response = {"ok": False, "error": f"Invalid request: {exc}"}
        self.wfile.write((json.dumps(response) + "\n").encode())


class EvidenceServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def main() -> None:
    SOCKET_PATH.unlink(missing_ok=True)
    save_state(initial_state())
    with EvidenceServer(str(SOCKET_PATH), RequestHandler) as server:
        os.chmod(SOCKET_PATH, 0o666)
        server.serve_forever()


if __name__ == "__main__":
    main()
