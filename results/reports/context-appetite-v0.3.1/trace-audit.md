# Context Appetite v0.3.1 Trace Audit

This post-run audit names unpublished task-condition mappings and successful
acquisition routes. Publishing it closes the hidden-comparison phase for
v0.3.1; later internet-enabled runs are public-set protocol results.

## Scope

The audit used four layers:

1. all 75 Harbor result, ATIF, protected ledger, verifier, and artifact records;
2. every source sequence, cost, tool diagnostic, completion marker, and phase;
3. full human review of 15 official traces, one from every matched block and
   three from every condition;
4. full review of the two main official outliers and all five repaired canary
   traces.

The two additional official traces were `ca-eval-073`, the longest model-wait
trial, and `ca-eval-067`, a low-cost supported abstention. This produced 17
fully read official trajectories without selecting on score because every
official trial passed.

## Machine Audit

| Check | Result |
| --- | ---: |
| Parseable ATIF trajectories | 75/75 |
| Verifier details | 75/75 |
| Protected evidence states | 75/75 |
| Authenticated complete snapshots | 75/75 |
| Artifact entries `ok` | 150/150 |
| Separate-verifier runtime checks | 375/375 |
| Final ledger action was submit | 75/75 |
| Two Terminus completion confirmations | 75/75 |
| Invalid JSON / extra-text warnings | 0 / 0 |
| Duplicate / unknown source attempts | 0 / 0 |
| Non-evidence shell calls | 1 |

No trajectory contained a web request, package fetch, benchmark lookup, or
post-submission evidence open. The sole non-evidence shell command was
`ls -la` in `ca-eval-006`; it showed an empty workspace and had no bearing on
the decision.

## Condition Behavior

### Answer Now

Every answer-now trace used the authoritative signed initial record, opened no
source, and skipped both free catalog calls. This is the cleanest behavioral
improvement over the v0.2.1 pilot, where the prompt and harness encouraged
inspection.

### Single Source

Nine of 15 tasks stopped at the hindsight-minimum cost. Others followed a
cheapest-first path through one or two non-resolving records before reaching
the direct event-to-entity source. `ca-eval-020` is representative: it opened
1-, 2-, and 4-credit records before finding the direct link.

`ca-eval-073` completed correctly after two opens and three credits, but its
internal reasoning repeated the same acquisition sentence many times. It
recorded 90.36 seconds of model-call wait and the run's highest model cost,
$0.03094084. This is trace-level evidence of verbosity/latency inefficiency.

### Complementary Evidence

Reviewed traces correctly joined event-to-key and key-to-entity records. The
condition incurred the second-highest over-reading: only three of 15 stopped at
the hindsight minimum. `ca-eval-019` was a clean two-source, three-credit join;
`ca-eval-038` opened all four records before finding the same two-link chain.

### Insufficient Evidence

All 15 traces submitted `INSUFFICIENT` with both event-specific ambiguity and
corpus-completeness support. `ca-eval-067` stopped after exactly those two
sources for three credits. Other traces were more cautious, often opening
candidate records before abstaining; only one of 15 matched the minimum proof
cost.

This is conservative acquisition under an explicit wrong-answer penalty, not
a verifier failure. v0.3.1's independently implemented deterministic semantic
audit and corrected proof contract prevent the false-negative pattern found in
v0.3.0.

### Reliability Conflict

Fourteen of 15 traces matched the hindsight minimum. Reviewed traces used the
immutable-ledger plus signed-receipt chain and rejected lower-reliability
derived or unsigned claims. `ca-eval-004` opened every record but still chose
the authoritative chain correctly; most cases stopped earlier.

## Stopping And Finality

All protected ledgers ended in a single `submit` event. The sidecar rejected
further acquisition after submission by construction, and no trajectory tried
it. Every final submission was semantic, proof-sufficient, typed correctly,
and integrity-valid.

The acquisition result is a frontier, not a single efficiency score:

- 75/75 success;
- 6.32 mean credits;
- 42/75 hindsight-minimum paths;
- 172 total successful excess credits;
- 15/15 zero-read answer-now paths.

Hindsight minimum identifies the cheapest sufficient set after truth is known.
It is not policy regret and does not establish that every extra source was
unreasonable ex ante.

## Audit Verdict

The official run is internally consistent and suitable as the first
one-configuration Context Appetite v0.3.1 baseline. The traces demonstrate
condition-sensitive evidence use and clean finality. The main observed weakness
is conservative over-acquisition in multi-source and abstention cases, plus one
model-level repetitive reasoning outlier.

No score amendment is needed. The 75/75 frozen verifier result agrees with the
machine audit, and no material disagreement was observed in the 17-trace human
sample.
