# Context Appetite v0.3.1

## Verdict

**Frozen as the first proper historical Context Appetite release record.** The
locked GLM 5.2 plus Terminus 2 run completed all 75 unpublished tasks with
**75/75 strict and domain passes**, no retries, and no infrastructure, deadline,
collection, format, or verifier failures.

This is evidence that one fixed model-harness-sandbox policy followed the
v0.3.1 support contract across all five conditions. It is not a model ranking,
an estimate of intelligence in isolation, or proof of Bayes-optimal acquisition.

## Release Shape

- Suite: Instinct Bench
- Domain and Harbor dataset: `context-appetite`
- Public development split: 6 matched scenario blocks x 5 conditions = 30 tasks
- Unpublished benchmark split: 15 held-out scenario blocks x 5 conditions = 75 tasks
- Source checkout and release-certification commit used for inference: `f1895a8`
- Frozen task-package content commit: `9341d23`
- Harbor: `harbor[modal]==0.20.0`

The five condition labels are experimental strata, not nested task families.
The 21 blueprints vary surface settings over five shared evidence structures;
they are not 21 unrelated Terminal-Bench-style task implementations. The row
counts are balanced design choices, not benchmark standards.

## Configuration

| Axis | Locked value |
| --- | --- |
| Model | `openrouter/z-ai/glm-5.2` |
| Harness | Terminus 2 `2.0.0`, no skills |
| Sandbox | Modal VM runtime, public agent egress |
| Sampling | temperature `0`, no seed, pass@1 |
| Provider request | OpenRouter endpoint tag `z-ai/fp8`, fallback disabled |
| Execution | concurrency 4, retries 0, timeout 300 seconds |
| Contract visibility | unpublished through the run |

OpenRouter returned model/router metadata for `z-ai/glm-5.2`; it did not
independently attest the requested `z-ai/fp8` serving endpoint. Temperature
zero without a provider seed is not deterministic.

## Result

| Measure | Result |
| --- | ---: |
| Planned / completed / benchmark-valid | 75 / 75 / 75 |
| Strict all-pass | 75/75 |
| Domain success: semantic + proof + integrity | 75/75 |
| Semantic / proof / format / integrity | 75/75 each |
| Harness completion | 75/75 |
| Deadline / infrastructure / verifier errors | 0 / 0 / 0 |
| Matched blocks with all five conditions passed | 15/15 |
| Answer-now zero-open and no-catalog | 15/15 |
| Hindsight-minimum acquisition | 42/75 |

The primary Harbor reward is binary task success. Acquisition, latency, tokens,
and cost are diagnostics and do not alter that reward.

## Conditions

| Condition | Strict | Mean credits | Mean opens | Hindsight minimum |
| --- | ---: | ---: | ---: | ---: |
| `answer-now` | 15/15 | 0.00 | 0.00 | 15/15 |
| `single-source` | 15/15 | 3.80 | 1.67 | 9/15 |
| `complementary-evidence` | 15/15 | 9.27 | 3.13 | 3/15 |
| `insufficient-evidence` | 15/15 | 12.07 | 3.60 | 1/15 |
| `reliability-conflict` | 15/15 | 6.47 | 2.13 | 14/15 |

The configuration cleanly distinguished answer-now from look-required cases:
all answer-now tasks were submitted directly, while all 60 other tasks
inspected the catalog and opened evidence. It followed provenance particularly
well in reliability-conflict tasks. Complementary and insufficient cases show
the most cautious over-reading.

Across the run, the agent opened 158 sources for 474 synthetic credits, 29,353
payload bytes, and a 7,402-token byte proxy. It spent 172 credits beyond the
frozen hindsight-minimum proof sets. Those extra reads are not automatically
irrational under uncertainty, and credits are not tokens or dollars.

## Acquisition Baselines

The deterministic baselines below isolate acquisition. Except for immediate
answering, they receive an Oracle terminal decision, so their success column is
optimistic proof coverage rather than agent accuracy.

| Policy | Coverage | Mean credits |
| --- | ---: | ---: |
| Proof-aware Oracle | 75/75 | 4.03 |
| GLM 5.2 + Terminus 2 | 75/75 actual | 6.32 |
| Authority-aware sequential | 75/75 | 7.04 |
| Open all | 75/75 | 15.00 |
| Cheapest first | 24/75 | 1.00 |
| First listed | 21/75 | 3.93 |
| Answer immediately | 15/75 | 0.00 |

This is why public presentation must show a success-acquisition frontier.
Success alone cannot distinguish the evaluated policy from open-all.

## Runtime Integrity

- 75/75 protected evidence snapshots were authenticated and complete.
- 150/150 Harbor artifact entries reported `ok`.
- 375/375 separate-verifier runtime checks passed.
- Every protected ledger ended with exactly one final submission.
- No duplicate or unknown opens, invalid JSON turns, or extra-text warnings.
- Every Terminus trajectory recorded both completion confirmations.

The implementation follows the useful release disciplines of Harvey LAB and
Terminal-Bench without importing an LLM judge: strict all-pass is kept beside
dense diagnostics; the outcome is execution-verified; expected truth remains
outside the agent image; artifacts fail closed; and raw jobs remain the audit
record. Harbor's sidecar collection and separate no-network verifier are the
runtime boundary.

## Trace Review

A machine audit covered all 75 trials. Full human review covered one official
trace from every matched block, three official traces per condition, both
latency/acquisition outliers, and all five repaired canary traces.

The reviewed behavior matched the intended conditions. One trial,
`ca-eval-006`, issued a harmless `ls -la` before using the evidence CLI; the
workspace was empty, no contract files were exposed, and no network use was
observed. One
single-source trial, `ca-eval-073`, contained highly repetitive internal
reasoning and accumulated 90.36 seconds of model-call wait before completing
correctly. That is a genuine efficiency observation, not a scoring failure.

See [trace-audit.md](trace-audit.md) for scope and examples.
The fuller [post-run review](post-run-review.md) separates run validity from
construct validity and records candidate v0.4 questions without changing this
release.

## Tokens And Cost

| Telemetry | Result |
| --- | ---: |
| Model calls | 368 |
| Input / cached input / output tokens | 666,979 / 535,872 / 98,421 |
| OpenRouter model cost | $0.75592892 |
| Model cost per task | $0.010079 |

Harness and Modal sandbox dollars were unavailable, so total dollars per task
and a dollar cost mix are intentionally `null`.

## Latency

Raw Harbor phase durations are preserved per trial in the normalized manifest.
For this run, agent execution was 46.26 seconds p50 and 68.79 seconds p95;
model-call wait was 38.42 seconds p50 and 62.03 seconds p95. Whole-trial
duration was 144.84 seconds p50 and 170.54 seconds p95, including environment
setup, collection/setup, and verification. Percentile figures use nearest-rank
p95 over 75 trials.

## Limits

- One model, harness, sandbox, provider request, and rollout per task.
- Fifteen matched scenario blocks do not justify an IID confidence interval or
  a population-level model ranking.
- The task explicitly exposes authority, reliability, lineage, and payoff. It
  measures supported evidence routing and stopping under that contract, not
  latent uncertainty discovery in the broad.
- Confidence is recorded but remains exploratory and unscored.
- Modal Compose required public agent egress. Contracts were private, opaque,
  synthetic, and precommitted during the run, and no trace used the network,
  but this is not a cryptographically closed environment.
- Static public development tasks cannot enter a clean public-egress accuracy
  denominator. After publication, future runs must be labeled public-set
  protocol results unless benchmark artifacts and external model APIs are
  blocked.

## Release State

The 30 development tasks are committed. The 75 one-shot tasks and release
secret remain local and unpublished. This report, the detailed manifest, and
the trace audit expose task-condition mappings and successful source routes.
Their publication closes the hidden-comparison phase for v0.3.1. Later
internet-enabled reruns must be labeled public-set protocol results.

Harbor registry upload remains a separate action. No v0.4 work begins from this
report.

## Artifacts

- [Detailed normalized manifest](../../manifests/context-appetite-v0.3.1-glm52-t2-eval-001.json)
- [Trace audit](trace-audit.md)
- [Candid post-run review](post-run-review.md)
- [Oracle release gate](oracle-gate.json)
- [Domain protocol](../../../docs/context-appetite-v0.3.1.md)
- [Public release commitment](../../../evals/context-appetite/release-v0.3.1.json)
- [Official run lock](../../../evals/context-appetite/official-run-v0.3.1.json)
