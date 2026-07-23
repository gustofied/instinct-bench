# Context Appetite v0.3.0

## Verdict

**Eligible as a one-configuration benchmark release.** The official run
completed all 75 held-out tasks with no infrastructure, deadline, collection,
or verifier errors. GLM 5.2 with Terminus 2 made the correct semantic decision
on every task and acquired sufficient proof on 71.

The release headline is therefore **71/75 supported decisions (94.67%)**.
Semantic accuracy was **75/75**. The distinction matters: all four non-passes
were correct `INSUFFICIENT` decisions submitted before the last material source
had been opened.

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
| Domain success: semantic + proof + integrity | 71/75 (94.67%) |
| Strict all-pass | 71/75 (94.67%) |
| Semantic decision | 75/75 (100%) |
| Sufficient proof | 71/75 (94.67%) |
| Format / verifier integrity / harness completion | 75/75 each |
| Deadline / infrastructure / verifier errors | 0 / 0 / 0 |
| Answer-now zero-open | 15/15 (100%) |
| Successful trials at hindsight-minimum cost | 49/71 (69.01%) |

The empirical 95% percentile interval from resampling the 15 matched scenario
blocks is 89.33% to 98.67%. It is an exploratory block-resampling summary, not
a row-IID confidence interval or a strong population guarantee.

## Conditions

| Condition | Domain success | Semantic | Mean credits | Opened sources |
| --- | ---: | ---: | ---: | --- |
| `answer-now` | 15/15 | 15/15 | 0.00 | 0 in all 15 |
| `single-source` | 15/15 | 15/15 | 4.40 | 1:7, 2:4, 3:2, 4:2 |
| `complementary-evidence` | 15/15 | 15/15 | 8.87 | 2:3, 3:7, 4:5 |
| `insufficient-evidence` | 11/15 | 15/15 | 12.87 | 3:4, 4:11 |
| `reliability-conflict` | 15/15 | 15/15 | 6.93 | 2:13, 3:1, 4:1 |

The model answered immediately on every answer-now task. In ten of those runs
it did not even inspect the free catalog or status endpoint. At the other end,
all 11 successful insufficient-evidence runs opened all four sources. The four
failures opened three and stopped before the 8-credit source.

## Economics

The run used 496 synthetic evidence credits, 31,220 evidence payload bytes, and
a 7,863-token evidence proxy. Successful trials acquired 92 credits beyond the
hindsight-minimum proof sets in total, or 1.30 credits per successful trial.
Credits are experimental prices, not tokens or dollars.

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

The most useful failure mode is also clear. On four insufficient-evidence
tasks, the agent reached the right terminal conclusion but treated three
sources as enough to establish that conclusion. The unopened source either
contained a second candidate control record or the completeness audit needed
to establish a closed corpus. The proof failures are therefore part of the
construct, not hidden-format or grader noise.

The release supports this narrower claim: **under a known information and
payoff environment, this model-harness policy reached supported decisions on
94.67% of tasks and varied acquisition with evidence necessity.** Evidence cost
is reported beside that success rate rather than blended into it.

## Limits

- One model, one harness, one sandbox, and one rollout per held-out task.
- Temperature zero was not deterministic because the endpoint exposes no
  sampling seed; the canary and official run diverged on one repeated task.
- The agent had public egress because Harbor 0.20 Modal Compose requires it.
  Contracts were private, opaque, and precommitted through the run, but the
  setup is not a cryptographically closed network.
- Every rollout used the instruction example's `0.84` confidence value, so the
  run contains no useful calibration signal.
- Prices are synthetic and evidence authority/reliability are declared.
- The held-out contracts remain private. The post-run release index exposes
  only task-to-condition/block mapping and commitments, not answer truth.

## Artifacts

- [Official manifest](../../manifests/context-appetite-v0.3.0-glm52-t2-eval-001.json)
- [Release index](../../manifests/context-appetite-v0.3.0-release-index.json)
- [Run gates](run-gates.md)
- [Trace audit](trace-audit.md)
- [Preregistered protocol](../../../docs/context-appetite-v0.3.0-plan.md)
- [Public release commitment](../../../evals/context-appetite/release-v0.3.0.json)
- [Official run lock](../../../evals/context-appetite/official-run-v0.3.0.json)
