# instinct-bench/deployment-outage

This is one look-required `answer-or-look` instance and a learning task for
Harbor task construction. The agent identifies the deployment responsible for
a checkout outage while choosing among records with visible evidence-credit
prices. The agent-facing request is in [instruction.md](instruction.md).

The implementation targets Harbor `0.20.0`.

This instance alone does not validate context appetite. A meaningful task
population must also contain answer-now, one-source, multi-source, and
insufficient-evidence cases so that the correct policy cannot be inferred from
the task template.

## Environment

The agent image is pinned to `python:3.13.7-slim-bookworm` at a fixed OCI digest.
It runs with one CPU, 1 GB RAM, no network, and a 120-second timeout. A
root-owned Unix-socket service exposes four records through the `evidence` CLI
and records openings in `/var/lib/evidence/state.json`. The agent runs as the
unprivileged `agent` user and cannot read unopened evidence or modify the state
file directly. Pinned Debian packages provide `tmux` and `asciinema` for
Terminus 2 without runtime package installation or network access.

A background process running as the same unprivileged user continuously checks
whether `/tests` becomes visible. Its observations are written by the
root-owned service into the protected state artifact.

The Harbor implementation is versioned `0.1.1`. Task data, the evidence-cost
table, scorer, and evaluation protocol remain independently versioned `0.1.0`;
the repository commit freezes their exact contents.

## Verifier

Harbor stops the agent environment, transfers only the declared state artifact,
and builds a separate verifier from `tests/Dockerfile`. Expected answers and
scoring code therefore never enter the agent container.

Task success requires both an exact answer and the minimum sufficient evidence
for this instance. Efficiency only adjusts successful rewards:

```text
reward = task_success * (0.90 + 0.10 * evidence_efficiency)
```

| Metric | Meaning |
| --- | --- |
| `reward` | Primary score in the successful band `[0.90, 1.00]`; failures are `0` |
| `task_success` | Exact answer and sufficient evidence both passed |
| `correctness` | Exact deployment ID match |
| `evidence_sufficient` | Minimum sufficient record was opened |
| `evidence_efficiency` | Optimal evidence cost divided by actual successful cost |
| `evidence_cost` | Synthetic evidence credits consumed, not model tokens |
| `excess_evidence_cost` | Credits above the minimum successful cost |
| `unnecessary_sources` | Opened records outside the minimum sufficient set |
| `verifier_integrity` | Artifact schema, cost parity, and isolation checks passed |

Actual prompt and completion token usage remains available in Harbor's agent
trajectory and is not represented by `evidence_cost`.

## Layout

```text
deployment-outage/
|-- environment/
|   |-- Dockerfile           # Pinned agent image
|   |-- evidence_server.py   # Root-owned evidence and state service
|   |-- evidence_cli.py      # Agent-facing client
|   `-- isolation_probe.py   # Unprivileged background leak probe
|-- solution/solve.sh        # Minimum-cost Oracle path
|-- tests/
|   |-- Dockerfile           # Pinned separate-verifier image
|   |-- runtime_checks.py    # Artifact, parity, and anti-leak checks
|   |-- score.py             # Deterministic multi-metric scorer
|   `-- test.sh              # Harbor verifier entrypoint
|-- instruction.md           # Short agent-facing request
`-- task.toml                # Artifact, isolation, and resource configuration
```

Repository-level regression tests live in
`dev_tests/test_deployment_outage.py` and cover scoring and service behavior.

## Running

Run the deterministic local tests:

```bash
python3 -m unittest discover -s dev_tests -v
```

Run the Oracle on Modal:

```bash
uvx --from 'harbor[modal]==0.20.0' harbor run \
  -p tasks/context-appetite/answer-or-look/deployment-outage \
  -a oracle \
  -e modal \
  -n 1
```

To run a model through Terminus 2, replace `oracle` with `terminus-2` and add
the model flag required by the configured provider.
