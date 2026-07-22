#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pwd
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any


SOCKET_PATH = Path("/run/instinct-bench-evidence.sock")
STATE_PATH = Path("/var/lib/evidence/state.json")
PROBE_PATH = Path("/usr/local/lib/instinct-bench/isolation_probe.py")
STATE_SCHEMA_VERSION = 2
TASK_DATA_VERSION = "0.1.0"
EVIDENCE_COST_TABLE_VERSION = "0.1.0"

QUESTION = "Which deployment caused the checkout outage from 14:32 to 14:47 UTC?"
INITIAL_CONTEXT = (
    "Checkout requests began returning HTTP 500 errors at 14:32 UTC, shortly "
    "after several systems changed."
)

SOURCES = {
    "command-brief": {
        "evidence_cost": 300,
        "description": "Incident command record for the affected window",
        "content": (
            "Incident INC-4821 began at 14:32 UTC and affected 38% of checkout "
            "requests. Incident command approved a rollback at 14:44 UTC. Error "
            "rates returned to baseline at 14:47 UTC. This brief does not identify "
            "a deployment or change ID."
        ),
    },
    "operations-record": {
        "evidence_cost": 2000,
        "description": "Automated operations record for the affected window",
        "content": (
            "13:55 UTC payments-api-2026.07.22.3 operation completed.\n"
            "14:29 UTC checkout-api-2026.07.22.4 operation completed.\n"
            "14:31 UTC catalog-api-2026.07.22.2 operation completed.\n"
            "14:44 UTC checkout-api-2026.07.22.4 rollback initiated for elevated "
            "checkout HTTP 500 errors.\n"
            "14:47 UTC rollback completed; checkout errors returned to baseline."
        ),
    },
    "response-record": {
        "evidence_cost": 8000,
        "description": "Responder activity record for the affected window",
        "content": (
            "14:35 IC: Checkout is failing in three regions. Payments and catalog "
            "owners report healthy services.\n"
            "14:42 Checkout on-call: The most recent checkout rollout is the prime "
            "suspect. I am requesting rollback approval.\n"
            "14:48 IC: Recovery confirmed after the checkout rollback. Pull the "
            "exact deployment ID from the operations record for the report."
        ),
    },
    "system-record": {
        "evidence_cost": 12000,
        "description": "Automated system record for the affected window",
        "content": (
            "14:32-14:46 UTC: checkout-api HTTP 500 rate 38%, p95 latency 2.8 s.\n"
            "14:32-14:46 UTC: payments-api HTTP 500 rate 0.1%, p95 latency 210 ms.\n"
            "14:32-14:46 UTC: catalog-api HTTP 500 rate 0.2%, p95 latency 180 ms.\n"
            "14:47 UTC: checkout-api HTTP 500 rate returned to 0.2%.\n"
            "This record is keyed by service, not operation identifier."
        ),
    },
}

_state_lock = threading.Lock()


def source_costs() -> dict[str, int]:
    return {
        source_id: int(source["evidence_cost"]) for source_id, source in SOURCES.items()
    }


def initial_state() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "task_data_version": TASK_DATA_VERSION,
        "evidence_cost_table_version": EVIDENCE_COST_TABLE_VERSION,
        "source_costs": source_costs(),
        "opened": [],
        "evidence_cost": 0,
        "answer": None,
        "events": [],
        "isolation_probe": {
            "started": False,
            "uid": None,
            "checks": 0,
            "tests_path_observed": False,
            "readable_test_files": 0,
        },
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
            "evidence_cost": source["evidence_cost"],
            "description": source["description"],
        }
        for source_id, source in SOURCES.items()
    ]


def _record_probe_report(report: dict[str, Any]) -> None:
    with _state_lock:
        state = load_state()
        probe = state["isolation_probe"]
        probe["started"] = True
        probe["uid"] = report.get("uid")
        probe["checks"] = max(int(probe["checks"]), int(report.get("checks", 0)))
        probe["tests_path_observed"] = bool(
            probe["tests_path_observed"] or report.get("tests_path_observed")
        )
        probe["readable_test_files"] = max(
            int(probe["readable_test_files"]),
            int(report.get("readable_test_files", 0)),
        )
        save_state(state)


def _consume_probe_output(process: subprocess.Popen[str]) -> None:
    if process.stdout is None:
        return
    for line in process.stdout:
        try:
            _record_probe_report(json.loads(line))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            continue


def start_isolation_probe() -> subprocess.Popen[str]:
    identity = pwd.getpwnam("agent")

    def drop_privileges() -> None:
        os.setgroups([])
        os.setgid(identity.pw_gid)
        os.setuid(identity.pw_uid)

    process = subprocess.Popen(
        [sys.executable, str(PROBE_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        preexec_fn=drop_privileges,
    )
    threading.Thread(
        target=_consume_probe_output,
        args=(process,),
        daemon=True,
    ).start()
    return process


def process(request: dict[str, Any]) -> dict[str, Any]:
    action = request.get("action")
    with _state_lock:
        state = load_state()

        if action == "ping":
            if int(state["isolation_probe"]["checks"]) < 1:
                return {"ok": False, "error": "isolation probe is not ready"}
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
                "evidence_cost": state["evidence_cost"],
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
                charged = int(SOURCES[source_id]["evidence_cost"])
                state["opened"].append(source_id)
                state["evidence_cost"] += charged
                state["events"].append(
                    {
                        "action": "open",
                        "source_id": source_id,
                        "evidence_cost": charged,
                    }
                )
                save_state(state)

            return {
                "ok": True,
                "source_id": source_id,
                "charged_evidence_cost": charged,
                "evidence_cost": state["evidence_cost"],
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
                "evidence_cost": state["evidence_cost"],
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
    start_isolation_probe()
    with EvidenceServer(str(SOCKET_PATH), RequestHandler) as server:
        os.chmod(SOCKET_PATH, 0o666)
        server.serve_forever()


if __name__ == "__main__":
    main()
