# Context Appetite

Context Appetite is the first domain in Instinct Bench. It evaluates whether an
agent can answer, inspect optional evidence, abstain, and stop under a declared
information and price environment.

This directory contains the v0.3.0 generator output. The five labels are
experimental conditions, not another dataset or task-family layer:

1. `answer-now`
2. `single-source`
3. `complementary-evidence`
4. `insufficient-evidence`
5. `reliability-conflict`

Each matched scenario block presents the same latent entity under all five
conditions. The public development split has six blocks and 30 tasks. The
held-out evaluation split has 15 disjoint blocks and 75 private tasks.
Price and list position are matched across evidence-requiring conditions
within a block and counterbalanced across blocks; release analysis therefore
uses the scenario block as the unit of resampling.
Evaluation task IDs are assigned by a release-secret-keyed permutation, so the
numeric suffix does not encode condition or block. Evaluation dataset order is
separately secret-keyed and does not preserve the five-condition cycle.

## Layout

```text
evals/context-appetite/
|-- README.md
|-- release-v0.3.0.json       # public commitment, created before inference
|-- dev/                      # 30 committed generated tasks
`-- eval-private/             # 75 generated tasks, ignored by Git

src/instinct_bench/context_appetite/
|-- blueprints.py
|-- generator.py
|-- schemas.py
|-- baselines.py
`-- templates/
```

The frozen v0.2.1 learning pilot remains under `tasks/context-appetite/`; it is
not rewritten into this release.

## Generate

Regenerate the public development set:

```bash
uv run python tools/generate_context_appetite.py \
  --split dev \
  --output evals/context-appetite/dev \
  --replace
```

Generate the private evaluation set from a mode-`0600`, 32-byte-or-longer
secret and write the public commitment:

```bash
uv run python tools/generate_context_appetite.py \
  --split eval \
  --secret-file ~/.config/instinct-bench/context-appetite-v0.3.0.secret \
  --output evals/context-appetite/eval-private \
  --commitment-output evals/context-appetite/release-v0.3.0.json
```

The public commitment contains only release identifiers, the SHA-256 secret
commitment, commitments to the complete private task population and complete
Harbor package set, and counts. It contains no task mapping, condition labels,
source contents, or answer.

## Agent Contract

The agent receives the initial decision record, its provenance, the common
payoff table, and the `evidence` CLI. `evidence list` exposes opaque IDs, price,
authority, declared reliability, lineage, and neutral descriptions without
revealing payloads. `evidence open` returns one payload and records the charge.
The typed `evidence submit` decision is final.

The main service has public egress because Harbor 0.20 Modal Compose requires
that baseline. Private task contracts therefore remain private through the
official run. Source contents and the append-only ledger live in a non-root
sidecar; hidden truth and accepted proof paths live only in a separate
no-network verifier.

## Verifier And Reward

Harbor reward is binary:

```text
semantic decision
AND accepted proof path opened
AND typed format
AND verifier integrity
```

Accepted proof paths are OR-of-AND sets, so alternative sufficient evidence is
valid. Evidence credits, source count, payload bytes/token proxy, confidence,
policy utility, model tokens, latency, provider dollars, harness completion,
and infrastructure state remain separate diagnostics.

The deterministic policy baselines are acquisition tests. Except for the two
immediate terminal policies, they assume an oracle terminal decision after
opening evidence. They detect presentation shortcuts and compare proof
coverage versus cost; they are not model scores.

## Validation

```bash
uv run python -m unittest discover -s dev_tests -v
uvx ruff check .

harbor run \
  -p evals/context-appetite/dev \
  -a oracle \
  -e modal \
  --print-config
```

The full preregistered protocol, release gates, fixed model-harness setup, and
reporting contract are in
[`docs/context-appetite-v0.3.0-plan.md`](../../docs/context-appetite-v0.3.0-plan.md).
