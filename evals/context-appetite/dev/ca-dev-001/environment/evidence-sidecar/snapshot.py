#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.request
from pathlib import Path


SNAPSHOT_TOKEN_PATH = Path("/var/lib/evidence/snapshot-token")


def main() -> None:
    token = SNAPSHOT_TOKEN_PATH.read_text().strip()
    if not token:
        raise SystemExit("snapshot token is missing")
    body = json.dumps(
        {"action": "snapshot", "snapshot_token": token},
        separators=(",", ":"),
    ).encode()
    request = urllib.request.Request(
        "http://localhost:8000/v1",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read(65_536))
    if not payload.get("ok"):
        raise SystemExit(payload.get("error", "snapshot failed"))
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
