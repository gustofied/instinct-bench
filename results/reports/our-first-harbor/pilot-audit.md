# Pilot Audit

Review object: commit `46832c4`, run
`context-appetite-v0.2.1-model-pilot-3x-001`.

## Findings

### P1: The manifest turns hidden-deadline failures into task failures

`tools/normalize_harbor_job.py:53-63` classifies every
`AgentTimeoutError` as a valid failed task before considering the verifier
result. That produces contradictory rows for `deployment-outage__xJQn2qn` and
`insufficient-evidence__aWaPNkL`: both have `task_outcome=fail` while the
protected verifier reports `task_success=1`, `correctness=1`,
`evidence_sufficient=1`, and `verifier_integrity=1`.

The five deadline traces are not one failure class:

- Three Flash trials had no submitted answer when the outer deadline fired
  while waiting on a model-provider response.
- The Pro trial had already submitted a correct supported answer, then timed
  out awaiting the next model response needed for Terminus confirmation.
- The GLM trial had already submitted a correct supported answer, then timed
  out in the terminal-capture path around finalization.

The task instruction never makes 120 seconds part of context appetite. Under
the `eval-engineering` protocol, timeout is infrastructure unless the deadline
is an explicit target capability. The primary accounting should therefore be
69 normally completed, verifier-valid trials; five agent-deadline
infrastructure cells; and one verifier-download infrastructure cell. Keep the
post-timeout ledgers as diagnostics.

The next manifest schema needs independent fields for agent execution,
decision observed, verifier status, semantic result, proof result, format
result, and harness completion. One `task_outcome` cannot represent this run.

### P1: The information environment is underspecified for rationality claims

The current prompt says task success comes first and cost is reported
separately (`tasks/context-appetite/*/instruction.md`). It does not state the
reliability of initial context, the loss for a wrong answer, the value of
abstention, or how source reliability and price were generated. The binary
reward also imposes no evidence penalty.

Opening a cheap corroborating source can therefore be rational. The 15
`answer-now` traces establish an inspect-first prior in this prompt and harness;
they do not establish irrational over-research. Representative traces
explicitly infer that they should inspect evidence even though the exact answer
is already present.

The first listed source is also the cheapest source in all five tasks. Across
the 75 protected ledgers, 57 trials opened that source first. Position and price
are therefore perfectly confounded for the first action. The conflicting
evidence task is not fully price-sorted, and its varied first choices show that
descriptions matter too, but this does not identify the causal influence of
price, position, prompt, model, or harness.

### P1: `hindsight_cost_gap` labels under-reading as efficient

Every task scorer computes:

```python
hindsight_cost_gap = max(0, observed_cost - hindsight_minimum_cost)
```

See `tasks/context-appetite/insufficient-evidence/tests/score.py:276-280`.
When an agent opens less than the required proof set, its negative shortfall is
clamped to zero. The historical report's `Zero hindsight gap` column therefore
includes failed under-reading trajectories. Flash's only zero-gap row was a
failed complementary-evidence run below the required cost, and one Inkling
zero-gap row was the failed insufficient-evidence under-read.

Use a signed `cost_delta_from_minimum` for diagnostics. Report excess cost only
conditional on semantic and proof success. Hindsight minimum remains a
descriptive oracle path, never an ex-ante policy optimum.

### P1: Five repeated cases cannot support model ranking or confidence bounds

The run repeats the same five fixed scenarios three times per model. Those are
five task clusters, not 74 independent samples from a target population. The
Wilson intervals in the historical report treat trial rows as independent and
should not be used for inference. There is no held-out generator, source-value
distribution, explicit seed, or contrasting harness.

The model tables remain useful trace summaries. They are not estimates of
general context appetite. Future uncertainty should be calculated over a
frozen population of independently generated task instances, with resampling
clustered by instance.

### P2: Exact answer formatting is mixed into the target capability

`insufficient-evidence__gn5UAJu` opened every source and submitted the correct
two candidates with a valid abstention, but reversed the explicitly requested
deployment-time order. Exact all-pass failure is defensible because the prompt
requires that order. It is not a context-acquisition failure.

Preserve strict all-pass reward, but expose separate `decision_correct`,
`proof_sufficient`, and `format_correct` metrics. For unordered semantic fields,
accept structured sets or canonicalize them before comparison.

### P2: `selective_decision_correct` is not correctness

At `score.py:281-283`, this metric only checks that a non-empty answer uses the
same abstain/non-abstain mode as the expected answer. It returns 1 for the
MiniMax reversed-order failure. Rename it to `abstention_mode_match`; do not put
it on a website as decision accuracy.

### P2: Symbolic credits are not context tokens or dollars

The 74 verifier-backed trials opened only 35,669 payload bytes, represented by
an 8,967-token deterministic byte proxy, while spending 353,150 synthetic
credits. Source prices range from 300 to 12,000 independently of payload size.

The benchmark currently measures behavior under a displayed symbolic price
schedule. It does not measure literal context-window consumption or all-in
cost. Harbor reported model-provider cost, but not Terminus or Modal cost.
Website labels must say `evidence credits` until the cost model is calibrated.

### P2: Required source sets will not scale to alternative proofs

The current five corpora appear to have one intended sufficient proof path, so
hard-coded `required_sources` are acceptable for the pilot and block memorized
answers. Generated tasks may contain multiple independent sufficient paths.
The verifier should then accept a family of proof sets or evaluate a proof
graph, rather than require one hidden author path.

### P2: The free catalog deliberately leaks useful routing metadata

`evidence list` reveals descriptions, order, and prices at zero credits. The
conflicting task directly labels records as unsigned, generated, signed, and
immutable. That task therefore measures use of supplied provenance metadata,
not discovery of reliability. This is already documented and is a valid task
type, but v0.3 needs matched conditions with neutral labels and reliability
learned from payloads or an explicit source model.

### P3: Publication metadata should be tightened before a registry release

The tasks use Harbor schema `1.3`, omit `[task].version`, and rely on mutable
model aliases. Harbor 0.20 accepts the current tasks and the run is valid, but
the latest task documentation illustrates schema `1.4`. Before publication,
confirm the exact 0.20 schema support, assign task versions, freeze dataset
membership, and record provider revisions where available. Do not migrate the
historical pilot in place.

## Corrected Accounting

| Axis | Result | Meaning |
| --- | ---: | --- |
| Planned cells | 75/75 | Five models x five tasks x three attempts |
| Agent phase completed normally | 70/75 | Includes the later verifier-download failure |
| Benchmark-valid | 69/75 | Normal agent completion plus valid verifier |
| Infrastructure | 6/75 | Five hidden agent deadlines, one verifier download |
| Strict all-pass | 67/69 | Exact answer/format, required proof, integrity |
| Semantic decision plus proof | 68/69 | Canonicalizes the MiniMax candidate order |
| Verifier snapshots recovered | 74/75 | Includes all five deadline-aborted trials |
| Verifier `task_success` in recovered snapshots | 69/74 | Diagnostic, not the primary denominator |
| Semantic decision plus proof in snapshots | 70/74 | Adds the MiniMax equivalent answer |
| Answer-now zero-open | 0/15 | Every run listed and opened evidence |

The historical `67/74 end-to-end` number is reproducible from the old manifest,
but it mixes 69 normal-completion trials with five hidden-deadline trials. It
should remain only as an as-run implementation statistic.

## Task-Level Read

**`answer-now`.** The clearest negative diagnostic. All models recovered the
right answer, but all opened the same cheapest and first-listed source. This
reveals inspect-first behavior under the current interface. It does not yet
measure calibrated confidence.

**`deployment-outage`.** Mostly an obvious cheap-first route: 13 runs used
`record-c -> record-a`. The extra cheap read is reasonable under uncertainty,
so this task mainly validates sequential logging and stopping after decisive
evidence.

**`complementary-evidence`.** A useful two-hop join control. One deadline trace
stopped before acquiring the second mapping, but the deadline occurred while
waiting on the provider; do not infer a stable model failure from one aborted
rollout.

**`insufficient-evidence`.** The strongest task. It surfaced under-reading,
open-all behavior, abstention, formatting, and harness finality. It should
remain as a development template after semantic and formatting metrics are
separated.

**`unreliable-or-conflicting-evidence`.** All runs resolved the provenance
chain. The visible labels make it an easy metadata-following task. Keep it as a
control and add neutral-label counterparts.

## Model-Level Read

GLM and DeepSeek Pro reached valid supported decisions with less symbolic
evidence than Flash. Flash had the lowest provider bill but the most evidence
use, three deadline-aborted no-answer traces, and the only malformed JSON
turns. This is a promising example of why price per token can differ from cost
per successful task.

It is not publishable evidence that one model has better context appetite.
There are only five fixed tasks, one harness, mutable provider routes, and no
all-in sandbox cost. Report model, harness, environment, and protocol as one
agent configuration until crossed controls exist.

## Honest Claim

Today we can say:

> On five private synthetic tasks, Instinct Bench successfully captured and
> verified sequential evidence acquisition for Terminus 2 agents running on
> Harbor 0.20 and Modal. Among 69 normally completed, verifier-valid trials, 67
> passed the exact contract and 68 reached a semantically valid, sufficiently
> evidenced decision. All 15 answer-now trials opened evidence, showing a strong
> inspect-first behavior in this prompt-harness setup.

We cannot yet say that the benchmark ranks model intelligence, measures
confidence, estimates a rational policy, or proves that a model that reads less
is smarter.

## Go Or No-Go

- **Go:** retain and commit this audit, keep the 75 raw trajectories, use the
  sidecar/verifier architecture as the v0.3 base, and build private generated
  task instances.
- **No-go:** publish a leaderboard, tune on these five tasks, add more models to
  the same matrix, or put one blended score on the website.
