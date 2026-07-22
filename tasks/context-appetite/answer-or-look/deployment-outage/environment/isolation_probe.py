#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


TESTS_PATH = Path(os.environ.get("INSTINCT_BENCH_TESTS_PATH", "/tests"))


def inspect_tests(path: Path) -> dict[str, int | bool]:
    path_observed = path.exists()
    readable_files = 0
    if path_observed:
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            if not candidate.is_file():
                continue
            try:
                with candidate.open("rb") as handle:
                    handle.read(1)
                readable_files += 1
            except OSError:
                continue
    return {
        "tests_path_observed": path_observed,
        "readable_test_files": readable_files,
    }


def main() -> None:
    checks = 0
    ever_observed = False
    max_readable_files = 0
    previous: dict[str, Any] | None = None

    while True:
        checks += 1
        observation = inspect_tests(TESTS_PATH)
        ever_observed = bool(ever_observed or observation["tests_path_observed"])
        max_readable_files = max(
            max_readable_files,
            int(observation["readable_test_files"]),
        )
        report = {
            "uid": os.getuid(),
            "checks": checks,
            "tests_path_observed": ever_observed,
            "readable_test_files": max_readable_files,
        }
        if previous != report and (checks == 1 or checks % 20 == 0 or ever_observed):
            print(json.dumps(report), flush=True)
            previous = report
        time.sleep(0.05)


if __name__ == "__main__":
    main()
