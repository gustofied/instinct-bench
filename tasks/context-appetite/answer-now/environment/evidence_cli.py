#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


BASE_URL = os.environ.get("EVIDENCE_URL", "http://evidence:8000").rstrip("/")
MAX_RESPONSE_BYTES = 131_072


def request(payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, separators=(",", ":")).encode()
    http_request = urllib.request.Request(
        f"{BASE_URL}/v1",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(http_request, timeout=5) as response:
            encoded = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        encoded = exc.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise SystemExit(f"evidence service unavailable: {exc}") from exc

    if len(encoded) > MAX_RESPONSE_BYTES:
        raise SystemExit("evidence response exceeded the size limit")
    response = json.loads(encoded)
    if not response.get("ok"):
        raise SystemExit(response.get("error", "evidence request failed"))
    return response


def print_list(response: dict[str, Any]) -> None:
    print(f"Question: {response['question']}")
    print(f"Initial context: {response['initial_context']}")
    print("\nAvailable evidence:")
    for source in response["sources"]:
        print(
            f"  {source['id']:<20} {source['evidence_cost']:>6} credits  "
            f"{source['description']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List evidence sources and their prices")
    open_parser = subparsers.add_parser("open", help="Open one evidence source")
    open_parser.add_argument("source_id")
    subparsers.add_parser("status", help="Show evidence spend and submission status")
    answer_parser = subparsers.add_parser("answer", help="Submit the final answer")
    answer_parser.add_argument("answer")
    subparsers.add_parser("ping", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.command == "list":
        print_list(request({"action": "list"}))
    elif args.command == "open":
        response = request({"action": "open", "source_id": args.source_id})
        print(f"Source: {response['source_id']}")
        print(f"Charged: {response['charged_evidence_cost']} credits")
        print(f"Total evidence cost: {response['observed_evidence_cost']} credits")
        print(f"Payload: {response['payload_bytes']} UTF-8 bytes")
        print(
            f"Token proxy: {response['payload_token_proxy']} (ceil UTF-8 bytes / 4)\n"
        )
        print(response["content"])
    elif args.command == "status":
        response = request({"action": "status"})
        visible = {key: value for key, value in response.items() if key != "ok"}
        print(json.dumps(visible, indent=2))
    elif args.command == "answer":
        response = request({"action": "answer", "answer": args.answer})
        print(f"Submitted: {response['submitted']}")
        print(f"Evidence cost: {response['observed_evidence_cost']} credits")
    elif args.command == "ping":
        request({"action": "ping"})
        print("ready")
    else:
        parser.error(f"unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
