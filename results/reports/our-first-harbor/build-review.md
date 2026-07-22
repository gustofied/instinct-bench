# Build Review

## System Map

**Target agent.** Terminus 2 `2.0.0` wraps one OpenRouter model at a time. It
turns model JSON into terminal keystrokes, records ATIF `v1.7`, and requires two
consecutive completion declarations before returning.

**Task capability.** The agent must choose among answering, opening one or more
priced records, combining evidence, abstaining, and stopping. The current
domain contains five hand-authored tasks under `tasks/context-appetite/`.

**Agent-visible surface.** The prompt supplies initial context and the
`evidence` CLI. The free `evidence list` call exposes record IDs,
descriptions, order, and symbolic prices. `evidence open` returns one payload
and logs its cost. `evidence answer` is final.

**State and effects.** A non-root sidecar owns the source corpus and an
append-only event ledger. A random token stored only in the sidecar authorizes
the final snapshot. Harbor stops the main service, runs the sidecar collect
hook, collects the protected artifact, and rehydrates it into an offline
separate verifier.

**Verifier.** A deterministic Python verifier checks the exact answer,
required source set, versions, prices, source order, event arithmetic,
snapshot metadata, and artifact integrity. `task_success` and Harbor reward are
binary. Cost and acquisition metrics are diagnostics.

**Run evidence.** The retained model pilot contains 75 ATIF trajectories, 75
protected sidecar snapshots, 75 artifact manifests, 74 verifier outputs, and
one explicit verifier infrastructure failure.

## What We Learned Building It

1. Harbor is the runner and record format, not the scientific claim. A job can
   preserve a verifier result even when an outer agent deadline fires, so a
   downstream manifest must not collapse exception, decision, verifier, and
   harness-finality state into one label.
2. Harbor 0.20 must be installed with the needed extra directly. In this
   workspace, `harbor[modal]==0.20.0` is the supported pin; `harbor[cloud]`
   caused dependency backtracking to 0.14.
3. Terminus 2 runtime dependencies belong in the image. Baking `tmux` and
   `asciinema` converted the first five setup errors into a clean model run.
4. Modal Compose network behavior matters. The working path uses
   `modal_vm_runtime=true`, a public main-service baseline, and a separate
   no-network verifier. That is operationally sound but not a closed-egress
   public benchmark.
5. Harbor's sidecar collect hook is the right primitive for protected action
   evidence. Collection itself is best effort, so the verifier must fail closed
   when the artifact or manifest is absent or malformed. This implementation
   does.
6. Oracle success proves solvability and plumbing. It says nothing about model
   performance and must stay out of leaderboard denominators.
7. `harbor view` is a filesystem browser. It does not know that one red job was
   superseded by a corrected rerun. Active jobs, scratch runs, archived setup
   history, and normalized publication records therefore need separate roots.

## What Is Sound

- The main and evidence services run as non-root users.
- Expected answers and scorer code are absent from the main image.
- The sidecar snapshot credential is not exposed to the agent.
- The main service is stopped before sidecar collection in separate-verifier
  mode.
- The verifier is offline, isolated, deterministic, and fails closed.
- Reward is binary; a cheap wrong answer cannot outrank a correct one.
- Exact source and event telemetry survives the agent and verifier lifecycle.
- Images and runtime dependencies are pinned.
- Unit tests cover task structure, drift between duplicated templates,
  adversarial artifacts, canned acquisition paths, and run-manifest behavior.
- Raw jobs, locked configuration, model telemetry, and reports are retained.

RewardKit would add judge variance without solving a current need. The facts,
answers, proof sets, and ledger arithmetic are deterministic, so the custom
verifier remains the better choice.

## Security Boundary

The protected ledger is credible for this pilot. The agent can call the
sidecar API but cannot read the corpus file, expected answer, scorer, snapshot
token, or sidecar filesystem. A forged main-container file cannot replace the
collected sidecar artifact.

The benchmark is not contamination-proof after publication. The main service
has public egress, the five task contracts are static, and model aliases plus
downstream OpenRouter routes are not content-addressed. The pilot ran while the
contracts were private, which reduces straightforward lookup but does not
prove closed-corpus isolation. Public evaluation needs opaque runtime-generated
instances or enforced no-network agent execution.

## Reproducibility Boundary

The benchmark commit, Harbor version, harness version, prompt digest, task
digests, launch command, model aliases, token telemetry, and raw traces are
recorded. Exact replay is still limited by absent seeds, mutable provider model
aliases, undisclosed downstream OpenRouter routing, and unknown Modal/harness
cost. These limitations are acceptable for a protocol pilot and unacceptable
for a durable ranking claim.
