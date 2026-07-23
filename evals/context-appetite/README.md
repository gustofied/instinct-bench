# Context Appetite

Context Appetite is the first domain in Instinct Bench. It evaluates whether an
agent can answer, inspect optional evidence, abstain, and stop under a declared
information and price environment.

This directory contains the v0.3.1 public development output. The five labels are
experimental conditions, not another dataset or task-family layer:

1. `answer-now`
2. `single-source`
3. `complementary-evidence`
4. `insufficient-evidence`
5. `reliability-conflict`

Each matched scenario block presents the same latent entity under all five
conditions. The public development split has six blocks and 30 tasks. Each
held-out evaluation release has 15 disjoint blocks and 75 private tasks.
Price and list position are matched across evidence-requiring conditions
within a block and counterbalanced across blocks; release analysis therefore
uses the scenario block as the unit of resampling.
Evaluation task IDs are assigned by a release-secret-keyed permutation, so the
numeric suffix does not encode condition or block. Evaluation dataset order is
separately secret-keyed and does not preserve the five-condition cycle.
The 21 scenario blueprints reuse five controlled evidence structures. They are
matched surface settings, not 21 unrelated task implementations.

## Layout

```text
evals/context-appetite/
|-- README.md
|-- release-v0.3.0.json        # historical public commitment
|-- official-run-v0.3.0.json   # historical locked protocol
|-- dev/                       # 30 committed v0.3.1 tasks
`-- eval-private-v0.3.1/       # future private tasks, ignored by Git

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

Generate a fresh private evaluation set from a mode-`0600`,
32-byte-or-longer secret and write its public commitment:

```bash
uv run python tools/generate_context_appetite.py \
  --split eval \
  --secret-file ~/.config/instinct-bench/context-appetite-v0.3.1.secret \
  --output evals/context-appetite/eval-private-v0.3.1 \
  --commitment-output evals/context-appetite/release-v0.3.1.json
```

The generator creates private directories as mode `0700` and private files as
mode `0600` or owner-executable `0700`. It refuses group/world-readable release
secrets and refuses to replace an older private release directory.

Validate every generated package and print the complete matched-block mapping:

```bash
uv run python tools/validate_context_appetite_release.py \
  --split eval \
  --secret-file ~/.config/instinct-bench/context-appetite-v0.3.1.secret \
  --dataset-dir evals/context-appetite/eval-private-v0.3.1
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
valid. For plain `INSUFFICIENT`, material proof is the event-specific ambiguity
record plus the independent completeness audit; candidate identities are not
required unless the terminal contract asks for them. Evidence credits, source
count, payload bytes/token proxy, confidence, policy utility, model tokens,
latency, provider dollars, harness completion, and infrastructure state remain
separate diagnostics.

The deterministic policy baselines are acquisition tests. Except for the two
immediate terminal policies, they assume an oracle terminal decision after
opening evidence. They detect presentation shortcuts and compare proof
coverage versus cost; they are not model scores.

## Validation

```bash
uv run python -m unittest discover -s dev_tests -v
uv run --with 'ruff==0.14.3' ruff check .

uvx --from 'harbor[modal]==0.20.0' harbor run \
  -p evals/context-appetite/dev \
  -a oracle \
  -e modal \
  --print-config
```

Before publishing, verify Harbor authentication and package resolution:

```bash
uvx --from 'harbor==0.20.0' harbor auth status
uvx --from 'harbor==0.20.0' harbor publish \
  evals/context-appetite/dev \
  --tag v0.3.1
```

Publishing is private by default. Add `--public` only after the namespace,
task digests, Oracle result, and release report have been checked.

The corrected release and proper-agent protocol are in
[`docs/context-appetite-v0.3.1.md`](../../docs/context-appetite-v0.3.1.md).
The historical preregistration remains in
[`docs/context-appetite-v0.3.0-plan.md`](../../docs/context-appetite-v0.3.0-plan.md).
The completed 75-task result and trace audit are in
[`results/reports/context-appetite-v0.3.0`](../../results/reports/context-appetite-v0.3.0/README.md).
