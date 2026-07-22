#!/bin/sh
set -eu

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.txt /logs/verifier/reward.json
python3 /tests/score.py
