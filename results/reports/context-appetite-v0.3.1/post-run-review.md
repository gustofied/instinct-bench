# Context Appetite v0.3.1 Post-Run Review

This post-run review refers to unpublished task-condition mappings and
trace-derived acquisition behavior. Publishing it closes the hidden-comparison
phase for v0.3.1; later internet-enabled runs are public-set protocol results.

## Bottom Line

The official run is operationally valid and the frozen score is exactly
75/75. The stronger conclusion is narrower: GLM 5.2 with Terminus 2 reliably
followed an explicit evidence-support contract, varied acquisition by
condition, and never failed finality or integrity.

The run does not establish broad context appetite or model intelligence. Binary
success is at ceiling, open-all also receives 75/75, the evidence structures
repeat, and authority/reliability cues are explicit. Acquisition behavior,
rather than task success alone, contains most of the useful signal.

## Denominator And Validity

| Axis | Count |
| --- | ---: |
| Planned unique tasks | 75 |
| Raw result records | 75 |
| Normally completed | 75 |
| Benchmark-valid | 75 |
| Strict passes | 75 |
| Domain passes | 75 |
| Semantic / proof / format / integrity passes | 75 each |
| Confirmed Terminus completions | 75 |
| Deadline / infrastructure / verifier errors | 0 / 0 / 0 |
| Retries | 0 |

There are no official non-passes to reinterpret and no missing cells. The
pre-repair 4/5 canary is excluded: it exposed an instruction/proof mismatch,
the contract was repaired and relocked, and both a repaired canary and renewed
Oracle gates passed before the official run. The official job was not resumed,
selectively retried, or rewritten.

The 75 rows are 15 matched scenario blocks crossed with five conditions. They
must not be treated as 75 IID draws. A block bootstrap or conventional
confidence interval adds little when every block is 5/5 and the generator has
only five evidence structures.

## Verifier Review

The deterministic verifier has a clean hard gate:

```text
semantic decision
AND accepted material proof path
AND typed format
AND verifier integrity
```

The primary Harbor reward is binary. Cost cannot rescue a wrong answer or
penalize a valid success. Accepted proof is OR-of-AND rather than a single
hidden path. Plain `INSUFFICIENT` requires event-specific ambiguity plus
corpus-completeness evidence, matching the visible terminal contract.

False-negative risk is materially lower than in v0.3.0:

- an independently implemented deterministic semantic audit validates every
  generated proof path and near-miss across all 105 public and unpublished
  packages;
- the first v0.3.1 canary's real false negative was repaired before the release
  digests and official run were locked;
- 17 fully read official traces agreed with all verifier outcomes.

False-positive risk remains bounded but not nonexistent. The verifier confirms
opened source IDs and exact structured decisions rather than reconstructing
natural-language entailment at runtime. The independent linter proves that
those generated sources materially contain the required claims, but a bug
shared by the generator and linter is still conceptually possible. No
materially unsupported pass appeared in the human sample. An LLM judge would
add variance without solving this deterministic target and is not warranted.

## Acquisition And Stopping

| Condition | Mean credits | Mean opens | Exact hindsight minimum |
| --- | ---: | ---: | ---: |
| Answer now | 0.00 | 0.00 | 15/15 |
| Single source | 3.80 | 1.67 | 9/15 |
| Complementary | 9.27 | 3.13 | 3/15 |
| Insufficient | 12.07 | 3.60 | 1/15 |
| Reliability conflict | 6.47 | 2.13 | 14/15 |

The clearest positive result is 15/15 direct answer-now behavior. Those trials
used the signed initial record and did not even call the free catalog. The
remaining 60 tasks all listed/statused and opened evidence. Reliability cases
mostly followed the authoritative ledger/receipt chain without exhausting the
corpus.

The clearest weakness is conservative over-acquisition. Complementary and
insufficient cases frequently opened three or four sources even after a
material proof set was available. Across all valid successes:

- 158 source opens;
- 474 synthetic credits, 6.32 per task;
- 42/75 hindsight-minimum paths;
- 172 credits beyond hindsight-minimum proof sets;
- 17 open-all paths at 15 credits.

This is not Bayesian policy regret. The hindsight minimum is known only after
all task truth is visible. Extra reads may be defensible under the explicit
`-200` wrong-answer loss, especially where an unopened source could resolve an
apparent ambiguity.

The success-cost frontier is still informative. The evaluated agent achieved
75/75 at 6.32 credits per task. Optimistic acquisition baselines achieved:

- proof-aware Oracle: 75/75 at 4.03 credits;
- authority-aware sequential: 75/75 at 7.04 credits;
- open-all: 75/75 at 15.00 credits;
- cheapest-first: 24/75 at 1.00 credit;
- first-listed: 21/75 at 3.93 credits.

Those baselines receive an Oracle terminal decision and are not model scores.
They show that neither a fixed first source nor pure price minimization solves
the family, while task success alone cannot distinguish the model from open-all.

## Confidence And Format

Every final decision used valid typed syntax and every Terminus trajectory
completed the required two-step confirmation. Confidence was unscored:

| Condition | Mean | Range |
| --- | ---: | ---: |
| Answer now | 0.995 | 0.995 |
| Single source | 0.983 | 0.97-0.99 |
| Complementary | 0.967 | 0.95-0.99 |
| Reliability conflict | 0.971 | 0.90-0.98 |
| Insufficient | 0.948 | 0.90-0.98 |

The ordering is directionally sensible, but it is not calibration evidence.
All outcomes were correct, source reliability was explicitly visible, and all
answer-now trials copied the initial record's 0.995 reliability. Confidence
should remain exploratory in historical reporting.

## Harness Effects

The result characterizes a complete agent configuration, not GLM 5.2 alone.
Terminus 2's command-line system prompt, evidence CLI, and explicit completion
confirmation shape behavior.

- All 60 evidence-requiring trials issued both `evidence list` and
  `evidence status`, suggesting a stable harness/prompt routine.
- All 15 answer-now trials bypassed that routine, so the harness did not force
  blanket tool use.
- Every trace used two completion confirmations, adding one model call after
  the final evidence submission.
- One trace, `ca-eval-073`, repeated internal reasoning heavily and accumulated
  90.36 seconds of model wait despite a correct two-source outcome.
- One trace issued `ls -la`; no trace used web/network or package commands.

A future harness comparison is necessary before attributing acquisition style,
latency, or verbosity to the model.

## Difficulty And Construct Validity

v0.3.1 validly measures **supported evidence routing and stopping under an
explicit information and payoff contract**. It includes answer-now,
single-source, complementary, insufficient, and reliability-conflict behavior.
Costs and display positions are counterbalanced, task IDs/order are secret
permuted, and a fixed first-listed or cheapest policy fails.

The construct is narrower than the name can imply:

- answer-now states an authoritative event-to-entity answer directly;
- other conditions state that initial context does not identify the answer;
- catalogs expose authority, reliability, lineage, and synthetic price;
- the same five evidence structures recur under 21 surface blueprints;
- a fresh Terminus session prevents cross-trial memory, but structural
  regularity still makes each individual task recognizable;
- one strong configuration reached a binary ceiling.

The run therefore cannot show broad instinct, latent uncertainty discovery,
Bayes-optimal metareasoning, or general research ability. It does show that the
agent can act on explicit sufficiency, provenance, ambiguity, and completeness
signals without a fixed read-count shortcut.

## Harbor, Isolation, And Reproducibility

The Harbor 0.20 packaging held:

- non-root main and sidecar containers;
- no task truth or verifier code in the main image;
- narrow source-ID-only evidence API and append-only protected ledger;
- sidecar-local authenticated snapshot after main termination;
- 150/150 collected artifact entries `ok`;
- separate deterministic no-network verifier;
- 375/375 runtime integrity checks;
- task/package, dataset, seed, prompt, model, harness, and run-lock
  commitments preserved in the manifest.

The remaining boundary is Modal Compose public egress. Contracts were
unpublished, opaque, and precommitted during inference, and no trajectory used
the network, so no contamination was observed. Once tasks are public, raw
egress permits benchmark-solution lookup. Future public-set results need a
network boundary or explicit public-set labeling.

Task generation and verifier behavior are deterministic and reproducible from
the frozen release secret and code. Agent behavior is not: temperature zero
had no seed, and the provider telemetry does not attest the requested
`z-ai/fp8` endpoint beyond the model/router identity.

The detailed normalized manifest is answer/proof-redacted but still maps private
task IDs to conditions, blocks, and successful source sequences. Publishing it
closes the hidden-comparison phase even while the task packages remain local.
Later internet-enabled runs are public-set protocol results.

## Scientific Claim

v0.3.1 supports:

> Under the locked GLM 5.2, Terminus 2, OpenRouter, and Modal configuration, the
> agent made 75 supported and correctly formatted decisions across 15 matched
> five-condition blocks. It answered all authoritative initial-context cases
> without acquisition and used more evidence when proof required it.

It does not support:

- a model leaderboard or comparison;
- a model-only ability claim;
- an IID 100% population accuracy estimate;
- rational-optimal or minimum-context claims;
- calibrated confidence;
- total dollars per task, because harness and sandbox dollars are unavailable;
- a closed-network security claim;
- a literal token interpretation of synthetic evidence credits.

## Historical Reporting Work

The only post-run changes belong to provenance and reporting:

- published answer/proof-redacted, trace-derived official manifest;
- manifest normalizer 2.3 with raw Harbor phase durations;
- backward-compatible schema support and artifact tests;
- final release report, trace audit, and this candid review.

No v0.3.1 task, instruction, source, generator, verifier, score, proof path,
dataset package, run lock, or raw official result was changed after inference.
The reporting record is published without the release secret or generated
private task packages.

## Candidate v0.4 Questions

These are design candidates, not approved implementation work:

1. Reduce explicit sufficiency cues and test whether agents infer when initial
   context is authoritative without being told the answer class.
2. Add more genuinely different evidence structures and source counts rather
   than more surface blueprints.
3. Use a controlled network/search action or a sandbox that blocks benchmark
   repositories and external model APIs.
4. Cross model and harness with one major variable changed at a time.
5. Add repeated rollouts and a held-out generated population before intervals
   or rankings.
6. Define confidence scoring and negative outcomes before claiming calibration.
7. Introduce known priors/source likelihoods only if policy regret or value of
   information is meant to become a formal target.

v0.3.1 should remain immutable while those questions are reviewed separately.
