#!/bin/sh
set -u

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.txt /logs/verifier/reward.json

checks_passed=0
if python3 /tests/runtime_checks.py > /logs/verifier/runtime-checks.txt 2>&1; then
    checks_passed=1
fi

python3 /tests/score.py --verifier-checks-passed "$checks_passed"
