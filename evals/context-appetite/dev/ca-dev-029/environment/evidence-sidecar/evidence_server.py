#!/usr/bin/env python3
from __future__ import annotations

import hmac
import json
import os
import secrets
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


TASK_DATA_PATH = Path(__file__).with_name("task_data.json")
STATE_PATH = Path("/var/lib/evidence/state.json")
SNAPSHOT_PATH = Path("/evidence-artifacts/state.json")
SNAPSHOT_TOKEN_PATH = Path("/var/lib/evidence/snapshot-token")
STATE_SCHEMA_VERSION = 5
MAX_REQUEST_BYTES = 8192
MAX_AGENT_REQUESTS = 256
MAX_SUBMISSION_BYTES = 2048

TASK_DATA = json.loads(TASK_DATA_PATH.read_text())
SOURCES: dict[str, dict[str, Any]] = TASK_DATA["sources"]
SOURCE_ORDER: list[str] = TASK_DATA["source_order"]

if set(SOURCE_ORDER) != set(SOURCES) or len(SOURCE_ORDER) != len(SOURCES):
    raise RuntimeError("source_order must contain every source exactly once")

_state_lock = threading.Lock()


def token_proxy(byte_count: int) -> int:
    return (byte_count + 3) // 4


def content_metrics(content: str) -> tuple[int, int]:
    byte_count = len(content.encode("utf-8"))
    return byte_count, token_proxy(byte_count)


def source_costs() -> dict[str, int]:
    return {
        source_id: int(source["evidence_cost"]) for source_id, source in SOURCES.items()
    }


def initial_state() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "task_id": TASK_DATA["task_id"],
        "task_data_version": TASK_DATA["task_data_version"],
        "evidence_cost_table_version": TASK_DATA["evidence_cost_table_version"],
        "source_costs": source_costs(),
        "source_order": SOURCE_ORDER,
        "opened": [],
        "observed_evidence_cost": 0,
        "observed_evidence_payload_bytes": 0,
        "observed_evidence_token_proxy": 0,
        "submission": None,
        "events": [],
        "agent_request_count": 0,
        "finalized": False,
        "snapshot": None,
    }


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return initial_state()
    return json.loads(STATE_PATH.read_text())


def write_text_atomic(path: Path, value: str, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(value)
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(value, indent=2) + "\n")


def save_state(state: dict[str, Any]) -> None:
    write_json_atomic(STATE_PATH, state)


def public_sources() -> list[dict[str, Any]]:
    return [
        {
            "id": source_id,
            "evidence_cost": SOURCES[source_id]["evidence_cost"],
            "description": SOURCES[source_id]["description"],
            "authority_class": SOURCES[source_id]["authority_class"],
            "declared_reliability": SOURCES[source_id]["declared_reliability"],
            "lineage_group": SOURCES[source_id]["lineage_group"],
        }
        for source_id in SOURCE_ORDER
    ]


def _agent_request_allowed(state: dict[str, Any]) -> bool:
    state["agent_request_count"] = int(state["agent_request_count"]) + 1
    return int(state["agent_request_count"]) <= MAX_AGENT_REQUESTS


def _snapshot_authenticated(provided: object) -> bool:
    if not isinstance(provided, str):
        return False
    try:
        expected = SNAPSHOT_TOKEN_PATH.read_text().strip()
    except OSError:
        return False
    return bool(expected) and hmac.compare_digest(provided, expected)


def process(request: dict[str, Any]) -> dict[str, Any]:
    action = request.get("action")
    with _state_lock:
        state = load_state()

        if action == "ping":
            return {"ok": True, "status": "ready"}

        if action == "snapshot":
            if not _snapshot_authenticated(request.get("snapshot_token")):
                return {"ok": False, "error": "Snapshot authentication failed."}
            if state.get("finalized") or SNAPSHOT_PATH.exists():
                return {"ok": False, "error": "Evidence state is already finalized."}
            state["finalized"] = True
            state["snapshot"] = {
                "complete": True,
                "authentication": "sidecar-file-token-v1",
                "task_id": state["task_id"],
                "event_count": len(state["events"]),
                "opened_count": len(state["opened"]),
                "agent_request_count": state["agent_request_count"],
                "observed_evidence_cost": state["observed_evidence_cost"],
                "observed_evidence_payload_bytes": state[
                    "observed_evidence_payload_bytes"
                ],
                "observed_evidence_token_proxy": state["observed_evidence_token_proxy"],
            }
            save_state(state)
            write_json_atomic(SNAPSHOT_PATH, state)
            return {"ok": True, "snapshot": str(SNAPSHOT_PATH)}

        if state.get("finalized"):
            return {"ok": False, "error": "Evidence state is finalized."}
        if action not in {"list", "status", "open", "submit"}:
            return {"ok": False, "error": f"Unknown action: {action}"}
        if not _agent_request_allowed(state):
            save_state(state)
            return {"ok": False, "error": "Evidence request limit exceeded."}

        if action == "list":
            state["events"].append({"action": "list", "evidence_cost": 0})
            save_state(state)
            return {
                "ok": True,
                "question": TASK_DATA["question"],
                "initial_context": TASK_DATA["initial_context"],
                "initial_context_metadata": TASK_DATA["initial_context_metadata"],
                "sources": public_sources(),
            }

        if action == "status":
            state["events"].append({"action": "status", "evidence_cost": 0})
            save_state(state)
            return {
                "ok": True,
                "opened": state["opened"],
                "observed_evidence_cost": state["observed_evidence_cost"],
                "observed_evidence_payload_bytes": state[
                    "observed_evidence_payload_bytes"
                ],
                "observed_evidence_token_proxy": state["observed_evidence_token_proxy"],
                "submitted": state["submission"] is not None,
                "submission": state["submission"],
            }

        if action == "open":
            if state["submission"] is not None:
                save_state(state)
                return {"ok": False, "error": "The submitted decision is final."}
            source_id = request.get("source_id")
            if not isinstance(source_id, str) or source_id not in SOURCES:
                state["events"].append(
                    {
                        "action": "open_unknown",
                        "source_id": str(source_id)[:100],
                        "evidence_cost": 0,
                    }
                )
                save_state(state)
                return {"ok": False, "error": f"Unknown source: {source_id}"}

            content = str(SOURCES[source_id]["content"])
            payload_bytes, payload_token_proxy = content_metrics(content)
            state["observed_evidence_payload_bytes"] += payload_bytes
            state["observed_evidence_token_proxy"] += payload_token_proxy
            charged = 0
            if source_id in state["opened"]:
                state["events"].append(
                    {
                        "action": "open_duplicate",
                        "source_id": source_id,
                        "evidence_cost": 0,
                        "payload_bytes": payload_bytes,
                        "payload_token_proxy": payload_token_proxy,
                    }
                )
            else:
                charged = int(SOURCES[source_id]["evidence_cost"])
                state["opened"].append(source_id)
                state["observed_evidence_cost"] += charged
                state["events"].append(
                    {
                        "action": "open",
                        "source_id": source_id,
                        "evidence_cost": charged,
                        "payload_bytes": payload_bytes,
                        "payload_token_proxy": payload_token_proxy,
                    }
                )
            save_state(state)
            return {
                "ok": True,
                "source_id": source_id,
                "charged_evidence_cost": charged,
                "observed_evidence_cost": state["observed_evidence_cost"],
                "payload_bytes": payload_bytes,
                "payload_token_proxy": payload_token_proxy,
                "observed_evidence_payload_bytes": state[
                    "observed_evidence_payload_bytes"
                ],
                "observed_evidence_token_proxy": state["observed_evidence_token_proxy"],
                "content": content,
            }

        if state["submission"] is not None:
            save_state(state)
            return {"ok": False, "error": "The submitted decision is final."}
        submission = request.get("submission")
        encoded_submission = json.dumps(submission, separators=(",", ":")).encode()
        if submission is None or len(encoded_submission) > MAX_SUBMISSION_BYTES:
            save_state(state)
            return {"ok": False, "error": "Submission is empty or too large."}
        state["submission"] = submission
        state["events"].append({"action": "submit", "submission": submission})
        save_state(state)
        return {
            "ok": True,
            "submission": submission,
            "observed_evidence_cost": state["observed_evidence_cost"],
        }


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "instinct-bench-evidence/0.3.1"

    def _write(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write(200, {"ok": True})
        else:
            self._write(404, {"ok": False, "error": "Not found."})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1":
            self._write(404, {"ok": False, "error": "Not found."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 1 or length > MAX_REQUEST_BYTES:
            self._write(413, {"ok": False, "error": "Invalid request size."})
            return
        try:
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise TypeError("request must be a JSON object")
            response = process(request)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            self._write(400, {"ok": False, "error": f"Invalid request: {exc}"})
            return
        self._write(200 if response.get("ok") else 400, response)

    def log_message(self, format: str, *args: object) -> None:
        return


def initialize_runtime() -> None:
    for path in (STATE_PATH, SNAPSHOT_PATH, SNAPSHOT_TOKEN_PATH):
        path.unlink(missing_ok=True)
    write_text_atomic(SNAPSHOT_TOKEN_PATH, secrets.token_urlsafe(48) + "\n")
    save_state(initial_state())


def main() -> None:
    initialize_runtime()
    server = ThreadingHTTPServer(("0.0.0.0", 8000), RequestHandler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
