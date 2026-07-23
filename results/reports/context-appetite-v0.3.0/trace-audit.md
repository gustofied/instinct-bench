# Trace Audit

## Scope

The audit combined a machine pass over all 75 official records with full trace
review of:

- every one of the four non-passes;
- all five paid-canary traces;
- 15 successful official traces from complete matched blocks 001, 008, and
  015, covering every condition three times.

All 75 trials had a parseable ATIF trajectory, verifier details, protected
evidence state, and five passing runtime checks. Machine review found no
duplicate or unknown source opens, invalid JSON turns, or extra-text warnings.

## Non-Passes

| Task | Block | Decision | Opened | Omitted material |
| --- | --- | --- | ---: | --- |
| `ca-eval-004` | 014 | `INSUFFICIENT` | 3 sources / 7 credits | second candidate control record |
| `ca-eval-006` | 012 | `INSUFFICIENT` | 3 sources / 7 credits | independent completeness audit |
| `ca-eval-012` | 007 | `INSUFFICIENT` | 3 sources / 7 credits | second candidate control record |
| `ca-eval-016` | 006 | `INSUFFICIENT` | 3 sources / 7 credits | second candidate control record |

Each trace made the correct semantic decision, met the typed format, completed
normally, and passed verifier integrity. Each skipped the 8-credit source and
therefore failed the accepted proof graph. The unopened records could have
resolved the ambiguity or were needed to establish corpus completeness, so the
verifier is not merely enforcing an arbitrary reading path.

This failure mode is best described as **premature abstention after partial
support**: the agent recognized uncertainty correctly but stopped before it had
proved that the available evidence could not resolve it.

## Successful Sample

The three fully audited matched blocks showed condition-sensitive acquisition:

- answer-now tasks were submitted directly from the authoritative initial
  record;
- single-source tasks ranged from exact one-source solutions to broader
  corroboration;
- complementary tasks joined the required records, sometimes with one or two
  extra reads;
- reliability-conflict tasks followed declared authority and lineage rather
  than the cheapest unsigned claim;
- successful insufficient-evidence tasks exhausted all four sources before
  abstaining.

One sampled trace issued a harmless non-evidence `ls -la`; no sampled trace
escaped the evidence protocol, corrupted state, or relied on a parser failure.

## Acquisition Shape

Among the 60 evidence-requiring tasks, first actions were not reducible to a
single visible shortcut:

| Condition | Cheapest first | First-listed first | Proof source first | Full sequence by ascending cost |
| --- | ---: | ---: | ---: | ---: |
| `single-source` | 13/15 | 3/15 | 7/15 | 14/15 |
| `complementary-evidence` | 10/15 | 4/15 | 13/15 | 10/15 |
| `insufficient-evidence` | 13/15 | 3/15 | 15/15 | 13/15 |
| `reliability-conflict` | 4/15 | 6/15 | 13/15 | 7/15 |

The model usually used a cheap-first policy, but declared reliability changed
that behavior sharply in conflict cases. Dataset order, task IDs, source list
position, price, and proof role were precommitted and counterbalanced, so the
result is not explained by a fixed first-listed shortcut.

## Efficiency

Forty-nine of 71 successful trials matched the hindsight-minimum evidence
cost. The remaining successful trials spent 92 excess synthetic credits in
total. Over-acquisition was concentrated in single-source and complementary
tasks, while successful insufficient-evidence trials necessarily spent all 15
credits under the frozen proof contract.

Hindsight-minimum cost is descriptive. It does not prove that every extra read
was irrational under uncertainty, and the report does not label excess cost as
Bayesian regret.

## Residual Risk

- The 15-block bootstrap is exploratory because the release contains only 15
  independently generated scenario blocks.
- The endpoint request was frozen, but provider response metadata does not
  independently attest the exact `z-ai/fp8` route.
- Public agent egress weakens the isolation guarantee even though contracts
  were private, opaque, synthetic, and committed before inference.
- A single rollout per task measures this realized policy, not its variance.

## Audit Verdict

The four failures are valid construct failures, not infrastructure, verifier,
or formatting artifacts. The official denominator is 75, the supported-domain
headline is 71, and semantic correctness should remain visible beside it at
75. The run is suitable for release as a one-configuration benchmark result.
