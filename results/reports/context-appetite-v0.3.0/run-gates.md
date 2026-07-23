# Run Gates

The release used separate scratch and official jobs so setup checks and Oracle
validation never enter model-performance denominators.

| Gate | Job | Outcome |
| --- | --- | --- |
| Terminus/Modal preflight | `context-appetite-v0.3.0-modal-t2-preflight-001` | setup completed; no benchmark trial |
| Private Oracle | `context-appetite-v0.3.0-oracle-smoke-001` | 75/75 strict; 375/375 runtime checks |
| Paid five-condition canary | `context-appetite-v0.3.0-glm52-t2-canary-001` | 5/5 strict; all traces inspected |
| Official evaluation | `context-appetite-v0.3.0-glm52-t2-eval-001` | 75/75 completed; 71 domain passes |

## Precommitment

The private population and exact model run were locked before paid inference.
The public release commitment records commitments to the secret seed, dataset,
and complete Harbor package set. The official run lock records the model, harness,
provider request, sampling settings, sandbox, concurrency, timeout, and retry
policy. Private task IDs and final dataset order were independently permuted by
the release secret.

The official job ran against commit `a6e35fe`, whose run lock points to task
release commit `b68a419`. No valid model failure was retried or replaced.

## Preflight

The install-only preflight completed in about 55 seconds. It established that
Terminus 2 could install in the Modal VM runtime with the pinned tmux and
asciinema dependencies. It deliberately ran no task or verifier and is marked
publication-excluded.

## Oracle

The Oracle run completed all 75 private tasks in 33 minutes 10 seconds. Every
task received strict binary reward 1, every sidecar artifact was collected,
and all five runtime isolation checks passed on all 75 tasks. The Oracle is QA
evidence, not model performance, and remains publication-excluded.

## Canary

The paid canary covered exactly one task from each condition. All five passed,
with behavior ranging from zero opens on answer-now through all four opens on
insufficient-evidence. The five full trajectories and artifacts were inspected
before the official run.

The canary cost $0.0535302 in model inference. On `ca-eval-016`, the canary
opened all four sources and passed; the official rollout opened three and
failed proof. That matched-task divergence is direct evidence that temperature
zero without a supported seed is not deterministic.

## Official Run

The official run lasted 50 minutes 34 seconds at concurrency four. It produced
75 result records from 75 planned trials with:

- no retries or selective reruns;
- no deadlines, cancellations, or infrastructure exceptions;
- no collection or verifier errors;
- 75 protected evidence artifacts;
- 375/375 runtime integrity checks;
- 75 confirmed Terminus completions;
- no invalid JSON turns or extra-text parser warnings.

The normalized manifest is marked `eligible`, not `published`: it is eligible
for the repository release and website pipeline after this audit, while Harbor
Hub publication remains a separate action.

## Reproducibility

The manifests preserve task package digests, the normalized release metadata
digest, prompt digest, model/harness/sandbox configuration, sanitized launch
command, per-trial trajectories, verifier details, evidence artifacts, token
telemetry, latency, and provider charges. Raw local Harbor jobs remain the
audit source and are intentionally not copied into Git.
