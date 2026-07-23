# Context Appetite v0.3.1 Release Gate

Context Appetite v0.3.1 is release-ready for its locked proper-agent canary.
This report covers task quality and runtime integrity, not model performance.

## Release Shape

- Suite: Instinct Bench
- Domain and Harbor dataset: `context-appetite`
- Public development split: 6 matched scenario blocks x 5 conditions = 30 tasks
- Unpublished benchmark split: 15 held-out scenario blocks x 5 conditions = 75 tasks
- Task release checkpoint: `4458249`
- Proper-agent run lock checkpoint: `6aff569`
- Harbor: `harbor[modal]==0.20.0`

The five condition labels are experimental strata, not nested task families.
The 21 blueprints provide varied surface settings over five shared evidence
structures. They are not 21 unrelated Terminal-Bench-style implementations.
The row counts are balanced design choices, not benchmark standards or magic
sample sizes.

## Gates

| Gate | Result |
| --- | --- |
| Unit and adversarial tests | 108/108 passed |
| Ruff format and lint | Passed |
| JSON and diff validation | Passed |
| Public package validation | 30/30 tasks, 6/6 blocks |
| Unpublished package validation | 75/75 tasks, 15/15 blocks |
| Held-out block and condition review | 15/15 mappings reviewed |
| Harbor 0.20 config resolution | Public and unpublished datasets passed |
| Public development Oracle matrix | 30/30 passed |
| Unpublished Oracle canary | 1/1 passed |
| Unpublished Oracle matrix | 75/75 passed |
| Artifact collection | Public 60/60; benchmark 150/150 entries `ok` |
| Authenticated evidence snapshots | Public 30/30; benchmark 75/75 complete |
| Separate-verifier runtime checks | Public 150/150; benchmark 375/375 passed |

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

The renewed final-digest Oracle jobs completed cleanly without resume,
directory removal, or selective retry: 30/30 public development tasks and
75/75 unpublished benchmark tasks passed.

## Privacy

The tracked release commitment contains no task mapping, condition, hidden
truth, source contents, or proof path. The unpublished release metadata, raw
Oracle job, and normalized trial manifest remain local. Only aggregate,
truth-free gate evidence is committed here so the first proper-agent run is
not contaminated.

Modal Compose requires public agent egress. Static public development tasks
therefore cannot support a clean public-egress accuracy denominator. The 75
unpublished tasks receive one preregistered run before publication. Later
public-set results require a network boundary that blocks benchmark artifacts
and external model APIs, or must be labeled as public-set protocol results.

## Verdict

The family is ready for the locked five-condition canary. A clean canary
trajectory audit unlocks the one-shot 75-task run. The result must report the
complete model+harness+prompt+skills+sandbox+provider configuration and keep
task success separate from acquisition and cost diagnostics.

Registry upload remains a separate action that Adam will request explicitly.
