# Context Appetite v0.3.1 Release Gate

Context Appetite v0.3.1 is release-ready as a Harbor development dataset and
private evaluation family. This report covers task quality and runtime
integrity, not model performance.

## Release Shape

- Suite: Instinct Bench
- Domain and Harbor dataset: `context-appetite`
- Public development split: 6 matched scenario blocks x 5 conditions = 30 tasks
- Private evaluation split: 15 held-out scenario blocks x 5 conditions = 75 tasks
- Source checkpoint: `f19cf35`
- Harbor: `harbor[modal]==0.20.0`

The five condition labels are experimental strata, not nested task families.
The 21 blueprints provide varied surface settings over five shared evidence
structures. They are not 21 unrelated Terminal-Bench-style implementations.
The row counts are balanced design choices, not benchmark standards or magic
sample sizes.

## Gates

| Gate | Result |
| --- | --- |
| Unit and adversarial tests | 99/99 passed |
| Ruff format and lint | Passed |
| JSON and diff validation | Passed |
| Public package validation | 30/30 tasks, 6/6 blocks |
| Private package validation | 75/75 tasks, 15/15 blocks |
| Held-out block and condition review | 15/15 mappings reviewed |
| Harbor 0.20 config resolution | Public and private datasets passed |
| Public development Oracle matrix | 30/30 passed |
| Private Oracle canary | 1/1 passed |
| Private Oracle matrix | 75/75 passed |
| Artifact collection | Public 60/60; private 150/150 entries `ok` |
| Authenticated evidence snapshots | Public 30/30; private 75/75 complete |
| Separate-verifier runtime checks | Public 150/150; private 375/375 passed |

Every Oracle trial returned binary reward, task success, semantic success,
proof sufficiency, format compliance, correctness, and verifier integrity of
`1`. Oracle results are release QA and are excluded from agent performance.

## Engineering History

The first permission preflight correctly failed because mode `0700` on the
transported Oracle solution prevented Harbor's configured non-root agent from
executing it. A second canary isolated the enclosing `solution/` directory as
part of the same contract. v0.3.1 now normalizes private roots and task
directories to `0700`, data files to `0600`, and transported `solution/` paths
to `0755`. Package digests commit to both contents and file/directory modes.

The full Oracle job initially completed 25 valid passes before 50 Modal
environment starts hit a local DNS `ConnectionError`. Harbor's exact-job
resume removed and reran only those infrastructure-error trial directories
under the locked config. The final job contains the original 25 valid trials
plus 50 recovered trials: 75 completed, 75 passed, zero final exceptions, and
no task-selective retry.

## Privacy

The tracked public commitment contains no task mapping, condition, hidden
truth, source contents, or proof path. The private release metadata, raw
Oracle job, and normalized trial manifest remain local. Only aggregate,
truth-free gate evidence is committed here so future proper-agent runs are not
contaminated.

Modal Compose requires public agent egress. Static public development tasks
therefore cannot support a hidden leaderboard claim. Formal comparisons must
use a fresh private release commitment or another architecture that enforces a
closed network boundary.

## Verdict

The family is ready to publish privately to Harbor and test proper agent
configurations. The next comparison must predeclare the complete
model+harness+prompt+skills+sandbox+provider route, use all 75 private tasks
with pass@1, and report task success separately from acquisition and cost
diagnostics.

Registry upload remains an external account step: `harbor auth status`
currently reports that this machine is not authenticated.
