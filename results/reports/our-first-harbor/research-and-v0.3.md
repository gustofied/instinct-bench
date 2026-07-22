# Research And v0.3

## Scientific Framing

The benchmark is best framed as **costly sequential information acquisition**.
An agent begins with a belief state, chooses whether to acquire an observation,
updates its belief, and eventually answers or abstains. This is a finite-horizon
metalevel decision problem with an optimal-stopping action.

That framing improves the original intuition in two ways:

1. Less context is not inherently smarter. The quality of a policy depends on
   the loss of a wrong decision, source costs, source reliability, prior
   uncertainty, and the environment's source distribution.
2. A hindsight-minimal proof is not the same as an ex-ante rational policy. A
   cheap source that proves irrelevant can still have positive expected value
   before it is opened.

The original instinct thesis remains intact: useful agents should know when to
answer, look, ask, abstain, and stop. The benchmark needs an explicit
information environment before it can judge those choices normatively.

## Strong Precedents

- [Principles of Metareasoning](https://doi.org/10.1016/0004-3702(91)90015-C)
  treats computation selection as a decision under uncertainty and derives its
  utility from how it can change external action.
- [Learning to Select Computations](https://arxiv.org/abs/1711.06892) studies
  learned metalevel policies for termination, allocation, and planning using
  value-of-information bounds.
- [Mouselab-MDP](https://cocosci.princeton.edu/papers/Mouselab_MDP-CameraReady.pdf)
  makes hidden information available through costly clicks and records what is
  opened, in what order, and when the participant stops. It is the closest
  human-experiment analogue to the evidence sidecar.
- [Information Sampling Behavior With Explicit Sampling Costs](https://pmc.ncbi.nlm.nih.gov/articles/PMC4942190/)
  compares human stop/continue behavior with an analyzable optimal sampling
  rule. It reinforces the need to state reward and sampling cost.
- [When2Call](https://aclanthology.org/2025.naacl-long.174/) explicitly tests
  when to call a tool, ask a follow-up question, or admit that the tools cannot
  answer. It also ships training data, showing a route from benchmark to
  preference optimization.
- [When2Tool](https://arxiv.org/abs/2605.09252) uses controlled environments
  with tool-necessary and tool-unnecessary boundaries and reports the trade-off
  between accuracy and call reduction. It directly supports matched necessity
  conditions rather than one-off anecdotes.
- [Adaptive-RAG](https://aclanthology.org/2024.naacl-long.389/) chooses among
  no retrieval, one-step retrieval, and iterative retrieval based on task
  complexity. [FLARE](https://aclanthology.org/2023.emnlp-main.495/) makes
  retrieval decisions during generation. Both are useful baselines, though
  neither alone provides our priced proof ledger.
- [The Art of Abstention](https://aclanthology.org/2021.acl-long.84/) motivates
  risk-coverage reporting instead of treating abstention as ordinary error.
- [Harvey LAB](https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark)
  uses short work requests, mixed relevant and peripheral files, strict
  all-pass completion, and criterion-level diagnostics. That supports our
  binary success gate plus separate proof and efficiency details.
- [Harbor artifact collection](https://www.harborframework.com/docs/run-jobs/results-and-artifacts)
  explicitly supports tamper-resistant sidecar evidence after stopping the main
  service. [Terminal-Bench 2.1](https://www.tbench.ai/news/terminal-bench-2-1)
  shows why task drift, resource mismatch, and instruction-test mismatch must
  trigger a benchmark revision rather than be counted as model failure.

## Measurement Contract

### Primary benchmark result

Keep a binary all-pass contract:

```text
task_success = semantic_decision_correct
             AND proof_sufficient
             AND format_contract_met
             AND verifier_integrity
```

Only normally completed trials with a valid verifier enter this denominator.
Agent deadline, provider, sandbox, collection, and verifier failures are
reported as infrastructure. If a later domain intentionally tests deadlines,
the deadline must be explicit in the instruction and versioned contract.

### Separate diagnostics

Report these independently:

- semantic decision correctness
- proof sufficiency and accepted proof path
- answer/abstain mode and confidence
- format/control correctness
- source sequence, source count, and displayed evidence credits
- actual evidence bytes/tokens delivered
- model input, cache, output, latency, and provider cost
- harness completion and parse recovery
- sandbox and harness cost when available
- infrastructure reliability by failure stage

Use Pareto plots for success versus evidence use, model tokens, latency, and
all-in dollars. Do not collapse them into one public number.

### Hindsight and policy metrics

Retain `hindsight_minimum_cost` only as an oracle proof diagnostic. Replace the
clamped gap with:

```text
signed_cost_delta = observed_cost - hindsight_minimum_cost
successful_excess_cost = signed_cost_delta if task_success else null
```

To claim rationality or regret, generate tasks from a known distribution and
define payoffs. One possible RL utility is:

```text
utility = reward_correct
        - loss_wrong
        + reward_valid_abstention
        - sum(opened_source_costs)
```

Set `loss_wrong` larger than the maximum acquisition budget so a cheap wrong
answer never beats a supported correct one. The benchmark should still publish
the components separately. Policy regret is the difference between expected
utility under the best policy for the known generator and expected utility
under the tested policy, averaged over fresh instances. It is not the realized
difference from the cheapest hindsight proof on one case.

## v0.3 Task Population

Build 30 private development instances before freezing an evaluation set:

| Cell | Count | Core behavior |
| --- | ---: | --- |
| Answer now | 6 | Initial context is sufficient under a stated reliability model |
| One source | 6 | One of several sources is sufficient |
| Complementary sources | 6 | Two or three observations must be joined |
| Insufficient evidence | 6 | Correct action is a supported abstention |
| Reliability conflict | 6 | Correlated, noisy, or signed sources must be distinguished |

For every instance, randomize opaque source IDs and list order independently of
price, relevance, payload length, and reliability. Vary wrong-answer loss,
abstention payoff, source cost, and source reliability in declared crossed
conditions. Include multiple sufficient proof paths where appropriate.

Use structured answer submission so semantic fields can be verified separately
from formatting. Record an initial answer/abstain choice and confidence before
research, then allow sequential opens and updates. This exposes whether new
evidence improved the decision instead of inferring confidence from source
count.

After the generator and verifier survive adversarial policy tests, freeze a
separate held-out set with generator version, seed commitments, task digests,
and no development access. Version any task correction as a new dataset release.

## Baselines Before Models

Run deterministic policies over every generated instance:

- answer immediately
- abstain immediately
- cheapest first
- first listed
- open all
- random source
- stop after one
- proof-aware Oracle
- Bayes-optimal policy when the generator supports exact dynamic programming

These baselines catch leaked answers, order confounds, unreachable proofs,
bad payoff scales, and verifier path matching before paid inference.

## Smallest Next Paid Experiment

Do not rerun the existing five tasks across more models. First resolve the
largest uncertainty: how much inspect-first behavior comes from task
presentation and Terminus rather than the model.

A clean control is 72 model trials:

```text
12 private matched instances
x 2 presentation arms
x 3 stochastic rollouts
= 72 trials
```

Arm A uses the current evidence-forward instruction. Arm B presents the same
facts, payoffs, and actions neutrally, with source order randomized. Hold the
model, Terminus version, Modal runtime, budget, and verifier fixed. Precede the
matrix with three Oracle/smoke cells if a 75-cell operational job is useful,
but never include those cells in model accuracy.

Run no more than four trials concurrently after a one-task install preflight
and a four-cell cheap canary. Use no selective retries. Record the intended
matrix before launch and keep every infrastructure cell.

If the presentation effect is material, add a second harness control next. A
fair harness comparison must expose equivalent answer/open/abstain actions and
use the same model, task instances, time budget, and verifier. Publish results
as model-harness configurations, not model-only scores.

## Manifest And Website v2

The next manifest should expose independent axes:

```text
execution_status: completed | deadline | infrastructure_error
failure_stage: provider_wait | terminal_io | sandbox | collection | verifier | null
answer_observed: true | false
semantic_outcome: pass | fail | not_evaluated
proof_outcome: pass | fail | not_evaluated
format_outcome: pass | fail | not_evaluated
harness_completion: confirmed | unconfirmed | not_evaluated
verifier_status: pass | fail | error | not_run
```

The website may show exact all-pass, semantic decision success, evidence
credits per successful task, model dollars per successful task, harness
completion, and infrastructure reliability. Model, harness, and sandbox cost
mix must remain unknown until each component is measured rather than mocked.

## Next Implementation Order

1. Freeze v0.2.1 and its raw 75-trial audit record.
2. Repair manifest classification and metric names; do not rewrite the raw job.
3. Build the private v0.3 generator and deterministic policy tests.
4. Add structured semantic/proof/format verification and accepted proof graphs.
5. Run Oracle, integration, and cheap model canaries.
6. Approve the 72-trial crossed presentation experiment only after trace review.
7. Add the second harness control before any public model ranking.
