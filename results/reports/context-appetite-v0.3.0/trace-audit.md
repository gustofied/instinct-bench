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

| Task | Block | Opened | Frozen omission | Material audit |
| --- | --- | ---: | --- | --- |
| `ca-eval-004` | 014 | 3 sources / 7 credits | second candidate record | supported |
| `ca-eval-006` | 012 | 3 sources / 7 credits | completeness audit | unsupported |
| `ca-eval-012` | 007 | 3 sources / 7 credits | second candidate record | supported |
| `ca-eval-016` | 006 | 3 sources / 7 credits | second candidate record | supported |

Each trace made the correct semantic decision, met the typed format, completed
normally, and passed verifier integrity. Each failed the frozen all-four-source
proof graph. That graph was over-specified for three trials: their opened
event-specific logs already established that both actions were
indistinguishable, and their independent audits established corpus
completeness. The omitted candidate record would only have named the second
candidate, which the terminal response did not request.

`ca-eval-006` is the genuine premature stop. It opened both candidate records
and the ambiguity log but omitted the completeness audit, so it had not shown
that no resolving evidence remained.

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
- frozen-verifier-successful insufficient-evidence tasks exhausted all four
  sources before abstaining.

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

Forty-nine of 71 frozen strict passes matched the frozen hindsight-minimum
evidence cost. The remaining strict passes spent 92 excess synthetic credits
in total. This accounting is preserved as history; it should not be used to
compare against v0.3.1 because the insufficient-evidence proof contract changed.

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

The immutable frozen verifier result is 71/75, with no infrastructure,
integrity, or formatting failures. The post-hoc material audit is 74/75:
three frozen failures were caused by an instruction/proof-graph mismatch, and
one was a genuine unsupported abstention. The run is suitable as an amended
one-configuration protocol record, not as an unqualified 71/75 material-proof
headline.
