# instinct-bench/deployment-outage

The agent identifies the deployment responsible for a checkout outage while
deciding which priced evidence to open. The complete task prompt is in
[instruction.md](instruction.md).

## Environment

The task uses `python:3.13-slim`, one CPU, 1 GB RAM, and no network. A root-owned
Unix-socket service exposes four evidence sources through the `evidence` CLI and
records source openings without exposing unopened contents. The agent runs as
the unprivileged `agent` user and has 120 seconds.

## Verifier

The deterministic verifier reads the service's root-owned state and writes a
multi-metric Harbor reward. The primary reward is gated by correctness:

| Metric | Type | Meaning |
| --- | --- | --- |
| `reward` | Programmatic | `correctness * (0.80 + 0.15 * efficiency + 0.05 * stopping)` |
| `correctness` | Programmatic | Exact deployment ID match |
| `context_efficiency` | Programmatic | Optimal evidence cost divided by actual sufficient cost |
| `stopped_correctly` | Programmatic | Answered after only the minimum sufficient source |
| `context_tokens` | Programmatic | Total listed cost of opened sources |
| `context_regret_tokens` | Programmatic | Spend above the 2,000-token minimum |
| `unnecessary_sources` | Programmatic | Opened sources outside the minimum sufficient set |

## Layout

```text
deployment-outage/
|-- environment/       # Metered evidence service and command-line client
|-- solution/solve.sh  # Minimum-context Oracle path
|-- tests/score.py     # Deterministic multi-metric verifier
|-- tests/test.sh      # Harbor verifier entrypoint
|-- instruction.md     # Agent-facing task
`-- task.toml          # Runtime and resource configuration
```

## Running

From the repository root:

```bash
harbor run \
  -p tasks/context-appetite/answer-or-look/deployment-outage \
  -a oracle \
  -e docker
```

To run a model through Terminus 2, replace `oracle` with `terminus-2` and add
the model provider and model flags required by your Harbor setup.
