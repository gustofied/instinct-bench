# instinct-bench

A benchmark suite for agent instinct: when to act from internal capability,
when to seek external context, and when to stop.

Instinct here is not guessing. It is the model's adaptive toolbox: priors,
taste, analogy, style, visual sense, language sense, craft, and learned ways of
working. The benchmark asks whether agents can balance that internal context
against external evidence, tools, references, feedback, and time.

Early domains:

- `context-appetite`: choose how much context is enough before answering.
- `tool-restraint`: know when to use tools and when to act directly.
- `drawing`: make, inspect, repair, and continue from partial shape.
- `writing`: draft, revise, preserve voice, and stop before overworking.

## First Harbor Pilot

The first `context-appetite` domain contains five hand-authored learning tasks:

- [`deployment-outage`](tasks/context-appetite/deployment-outage)
- [`answer-now`](tasks/context-appetite/answer-now)
- [`complementary-evidence`](tasks/context-appetite/complementary-evidence)
- [`insufficient-evidence`](tasks/context-appetite/insufficient-evidence)
- [`unreliable-or-conflicting-evidence`](tasks/context-appetite/unreliable-or-conflicting-evidence)

Together they test whether an agent should answer, look, combine evidence, or
stop. This is a verifier and task-design pilot, not yet a leaderboard.

Run its reference solution with:

```bash
uvx --from 'harbor[modal]==0.20.0' harbor run \
  -p tasks/context-appetite \
  -a oracle \
  -e modal \
  -o jobs-scratch \
  --job-name context-appetite-v0.2.1-oracle-smoke-001 \
  --ek modal_vm_runtime=true
```

See the [domain design and runbook](tasks/context-appetite/README.md) for the
measurement contract, security boundary, and real-agent canary.

The complete build and pilot review lives in
[`results/reports/our-first-harbor`](results/reports/our-first-harbor). It
separates task decisions, evidence acquisition, harness completion, and
infrastructure before proposing the next experiment.

## Context Appetite v0.3.0

The next release is preregistered as 30 public development tasks and 75 private
held-out tasks across five matched evidence-necessity conditions. It fixes one
model-harness configuration so the experiment measures answer, look, abstain,
and stop behavior without turning the result into a model leaderboard.

Read the full [v0.3.0 protocol](docs/context-appetite-v0.3.0-plan.md).
