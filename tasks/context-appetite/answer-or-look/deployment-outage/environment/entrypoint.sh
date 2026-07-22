#!/bin/sh
set -eu

umask 077
python3 /opt/evidence/evidence_server.py >/var/log/evidence-server.log 2>&1 &

attempt=0
while [ ! -S /run/instinct-bench-evidence.sock ]; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 100 ]; then
        echo "evidence service failed to start" >&2
        exit 1
    fi
    sleep 0.05
done

if [ "$#" -eq 0 ]; then
    exec sleep infinity
fi

exec "$@"
