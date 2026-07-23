# Context Appetite v0.3.0

## Verdict

**Preserved as a one-configuration protocol release with an audit amendment.**
The official run completed all 75 held-out tasks with no infrastructure,
deadline, collection, or verifier errors. The frozen verifier emitted
**71/75 strict passes**, and GLM 5.2 with Terminus 2 made the correct semantic
decision on every task.

A post-hoc material-proof review found that three frozen non-passes had already
opened enough evidence for the requested plain `INSUFFICIENT` decision. The
scientifically defensible interpretation is therefore **74/75 materially
supported decisions**, alongside the immutable **71/75 frozen verifier score**
and **75/75 semantic decisions**.

This is a valid result for one fixed model-harness-sandbox configuration. It is
not a model ranking, an estimate of model intelligence in isolation, or a claim
of Bayes-optimal evidence acquisition.

## Configuration

| Axis | Locked value |
| --- | --- |
| Release | Instinct Bench: Context Appetite v0.3.0 |
| Evaluation set | 15 matched blocks x 5 conditions = 75 private tasks |
| Model | `openrouter/z-ai/glm-5.2` |
| Harness | Terminus 2 `2.0.0`, no skills |
| Sandbox | Modal VM runtime, public agent egress |
| Sampling | temperature `0`, no seed, one rollout per task |
| Provider request | OpenRouter endpoint tag `z-ai/fp8`, fallback disabled |
| Execution | Harbor `0.20.0`, concurrency 4, retries 0, timeout 300 seconds |

The locked request specified that route with fallback disabled, but returned
telemetry identifies the model/router rather than independently attesting the
serving endpoint. The endpoint is reported as **requested**, not
provider-confirmed.

## Results

| Measure | Result |
| --- | ---: |
| Planned / completed / benchmark-valid | 75 / 75 / 75 |
| Frozen domain success: semantic + proof + integrity | 71/75 (94.67%) |
| Frozen strict all-pass | 71/75 (94.67%) |
| Post-hoc materially supported decisions | 74/75 (98.67%) |
| Semantic decision | 75/75 (100%) |
| Frozen proof-path coverage | 71/75 (94.67%) |
| Format / verifier integrity / harness completion | 75/75 each |
| Deadline / infrastructure / verifier errors | 0 / 0 / 0 |
| Answer-now zero-open | 15/15 (100%) |
| Successful trials at hindsight-minimum cost | 49/71 (69.01%) |

The original 71/75 block-resampling interval is retained in the frozen
manifest but is not promoted after the materiality amendment. Fifteen blocks
are too few for a strong population claim, and the post-hoc adjudication was
not preregistered.

## Conditions

| Condition | Frozen strict | Material audit | Semantic | Mean credits |
| --- | ---: | ---: | ---: | ---: |
| `answer-now` | 15/15 | 15/15 | 15/15 | 0.00 |
| `single-source` | 15/15 | 15/15 | 15/15 | 4.40 |
| `complementary-evidence` | 15/15 | 15/15 | 15/15 | 8.87 |
| `insufficient-evidence` | 11/15 | 14/15 | 15/15 | 12.87 |
| `reliability-conflict` | 15/15 | 15/15 | 15/15 | 6.93 |

The model answered immediately on every answer-now task. In ten of those runs
it did not even inspect the free catalog or status endpoint. At the other end,
all 11 frozen-verifier successes in `insufficient-evidence` opened all four
sources. Four runs opened three sources. Three had nevertheless established
ambiguity and corpus completeness; one had not established completeness.

## Economics

The run used 496 synthetic evidence credits, 31,220 evidence payload bytes, and
a 7,863-token evidence proxy. Under the frozen all-four-source contract,
71 strict passes acquired 92 credits beyond its hindsight-minimum proof sets.
That efficiency accounting is historical and should not be compared directly
with the corrected v0.3.1 proof contract. Credits are experimental prices, not
tokens or dollars.

Model telemetry recorded 674,494 input tokens, 544,128 cached input tokens,
107,448 output tokens, and 378 model calls. Mean trial duration was 157.02
seconds; the call-weighted mean model latency was 10.69 seconds.

OpenRouter model inference cost **$0.79675688**, or **$0.010623 per task**.
Harness and Modal sandbox costs were unavailable, so total cost per task and a
model/harness/sandbox cost split are intentionally not reported.

## Interpretation

The strongest positive result is conditional behavior. The same fixed agent
answered with no evidence when the initial record was authoritative, acquired
one or more sources when needed, joined complementary evidence, followed
declared provenance through conflicts, and abstained when the corpus could not
support a unique answer.

The audit found one genuine stopping failure: `ca-eval-006` omitted the
completeness audit and therefore could not establish that the corpus contained
no resolving evidence. In `ca-eval-004`, `ca-eval-012`, and `ca-eval-016`, the
agent had already opened an event-specific ambiguity record and an independent
completeness audit. Requiring the omitted second candidate identity exceeded
the user-visible terminal contract.

The release supports this narrower claim: **under a known information and
payoff environment, this model-harness policy made 75 correct decisions, 74
were materially supported, and evidence acquisition varied with necessity.**
The frozen Harbor score remains visible for provenance rather than being
silently rewritten.

## Limits

- One model, one harness, one sandbox, and one rollout per held-out task.
- Temperature zero was not deterministic because the endpoint exposes no
  sampling seed; the canary and official run diverged on one repeated task.
- The agent had public egress because Harbor 0.20 Modal Compose requires it.
  Contracts were private, opaque, and precommitted through the run, but the
  setup is not a cryptographically closed network.
- Every rollout used the instruction example's `0.84` confidence value, so the
  run contains no useful calibration signal.
- The material-proof review is post-hoc. It corrects an instruction/verifier
  mismatch but is not a replacement preregistered benchmark score.
- Prices are synthetic and evidence authority/reliability are declared.
- The held-out contracts remain private. The post-run release index exposes
  only task-to-condition/block mapping and commitments, not answer truth.

## Artifacts

- [Official manifest](../../manifests/context-appetite-v0.3.0-glm52-t2-eval-001.json)
- [Release index](../../manifests/context-appetite-v0.3.0-release-index.json)
- [Run gates](run-gates.md)
- [Trace audit](trace-audit.md)
- [Post-hoc material-proof audit](material-proof-audit.json)
- [Preregistered protocol](../../../docs/context-appetite-v0.3.0-plan.md)
- [Public release commitment](../../../evals/context-appetite/release-v0.3.0.json)
- [Official run lock](../../../evals/context-appetite/official-run-v0.3.0.json)
