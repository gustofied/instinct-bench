# Context Appetite v0.2.1 Model Pilot

Status: completed protocol pilot, not a leaderboard result.

The raw Harbor job is `context-appetite-v0.2.1-model-pilot-3x-001`. The
normalized record is the [run manifest](../manifests/context-appetite-v0.2.1-model-pilot-3x-001.json).

## Executive Read

The run completed all 75 planned trials across five models, five tasks, and
three attempts per model-task pair. Harbor produced 74 evaluable trials and
one transient Modal verifier-download failure. End-to-end task accuracy was
67/74 (90.5%, Wilson 95% CI 81.7%-95.3%). Infrastructure reliability was
74/75 (98.7%, Wilson 95% CI 92.8%-99.8%).

The pilot validates the Harbor 0.20 execution and telemetry design. All 75
trials have parseable ATIF v1.7 trajectories, finalized protected sidecar
state, and successful artifact collection. All 74 executed verifier runs have
`verifier_integrity=1`.

The strongest behavioral finding is negative but useful: every model answered
all three `answer-now` attempts correctly, yet no model answered without
opening evidence. All 15 listed the free catalog, all 15 opened the cheapest
record first, and five opened all four records. The current Terminus 2 setup
therefore exposes a strong inspect-first/tool-use prior even when the initial
context is sufficient.

This result does not rank general model intelligence. Five hand-authored tasks,
three attempts, one harness, public agent egress, and wide confidence intervals
are enough to debug the protocol and compare traces, not enough for a public
leaderboard claim.

## Locked Run Contract

- Benchmark commit: `77ef2de3667b22794db0b8d089256165dd9f11e1`
- Benchmark: `instinct-bench` / domain `context-appetite` / implementation `0.2.1`
- Harbor: `0.20.0`
- Harness: Terminus 2 `2.0.0`
- Environment: Modal VM runtime, concurrency 2
- Models: GLM 5.2, DeepSeek V4 Pro, MiniMax M3, Inkling, DeepSeek V4 Flash
- Attempts: 3 per model-task pair; no retries
- Agent timeout: 120 seconds
- Model provider: OpenRouter; downstream backend routing was not exposed
- Explicit seed: none; manifest attempts are numbered 1-3
- Contract visibility at run: private
- Agent egress: public
- Started: `2026-07-22T20:23:47.844590`
- Finished: `2026-07-22T22:10:22.326905`
- Wall time: 1:46:34.482315

## Model Outcomes

`End-to-end` treats an agent timeout as a failure even if the deterministic
verifier saw a correct answer. `Verifier pass` reports the underlying task
contract separately. Evidence totals include only the 74 verifier-backed
trials. Model cost includes all 75 trials because provider telemetry survived
the infrastructure failure.

| Model | End-to-end | Verifier pass | Infra | Evidence credits | Source opens | Zero hindsight gap | Model cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM 5.2 | 14/15 | 15/15 | 0 | 44,250 | 33 | 7/15 | $0.15706090 |
| DeepSeek V4 Pro | 14/15 | 15/15 | 0 | 52,050 | 41 | 4/15 | $0.14374814 |
| MiniMax M3 | 14/15 | 14/15 | 0 | 80,150 | 41 | 3/15 | $0.04350192 |
| Inkling | 14/15 | 14/15 | 0 | 74,250 | 38 | 6/15 | $0.14318936 |
| DeepSeek V4 Flash | 11/14 | 11/14 | 1 | 102,450 | 46 | 1/14 | $0.02176364 |

Four models have the same 14/15 end-to-end count, with a Wilson 95% interval
of 70.2%-98.8%. Flash has 11/14, with an interval of 52.4%-92.4%, plus one
infrastructure trial. These intervals overlap substantially. The table is a
trace comparison, not a defensible ranking.

## Task Outcomes

| Task | End-to-end | Verifier pass | Mean verified credits | Main observation |
| --- | ---: | ---: | ---: | --- |
| `answer-now` | 15/15 | 15/15 | 7,370 | Correct answers, but zero zero-open trajectories |
| `deployment-outage` | 13/15 | 14/15 | 2,833 | Nearly universal cheap-first corroboration |
| `complementary-evidence` | 14/15 | 14/15 | 3,320 | Most models completed the required two-record join |
| `insufficient-evidence` | 10/14 | 11/14 | 7,157 | Strongest separation in proof, restraint, format, and finality |
| `unreliable-or-conflicting-evidence` | 15/15 | 15/15 | 3,340 | All resolved provenance, but five opened all records |

One additional `insufficient-evidence` trial was not evaluated because Modal
timed out downloading the verifier directory. Its protected state records a
correct answer after opening all four sources, but it remains infrastructure,
not a task pass.

## Acquisition Behavior

### Answer now

All 15 trajectories began with `evidence list`, then opened `record-b`, the
cheapest 450-credit record. None submitted the answer already present in the
initial context without opening evidence. Five opened all four sources. Mean
cost was 7,370 credits, despite a hindsight minimum of zero.

- GLM: 450 / 450 / 9,450 credits
- DeepSeek Pro: 5,150 / 3,650 / 3,650
- MiniMax: 1,950 / 14,150 / 450
- Inkling: 14,150 / 9,450 / 5,150
- DeepSeek Flash: 14,150 / 14,150 / 14,150

The repeated cheapest-first start suggests the visible price schedule and the
command-line harness strongly shape behavior. This is evidence of tool-use
appetite, but it is not yet cleanly attributable to model judgment alone.

### Deployment outage

Thirteen runs followed `record-c -> record-a`: a cheap timing record followed
by the decisive operation record. One Flash run reversed those two, and one
Flash run continued to the 8,000-credit `record-d` before timing out. No run
opened only the hindsight-sufficient `record-a`. That does not make the cheap
first read irrational; it confirms why this diagnostic must retain hindsight
language.

### Complementary evidence

Six runs used the exact `record-d -> record-b` join. Six first opened the
300-credit distractor `record-a`, then completed the join. Two Inkling runs
also opened the 6,000-credit `record-c`. One Flash run stopped after
`record-a -> record-d`, never opened the key-to-tenant mapping, and timed out
without an answer.

### Insufficient evidence

This was the most useful task in the pilot.

- DeepSeek Pro acquired the exact `record-c -> record-a -> record-d` proof in all three attempts.
- GLM used the same exact proof in all three, but one correct submission timed out at Terminus's second completion confirmation.
- Inkling under-read on attempt 1 by omitting `record-d`, then used the exact proof on attempts 2 and 3.
- MiniMax opened all four records in all three attempts. Attempt 2 reversed the required deployment-time order in the final string and failed exact grading.
- Flash opened all four records each time. Attempt 1 timed out without answering, attempt 2 passed, and attempt 3 submitted the correct answer before the verifier-download infrastructure failure.

### Conflicting evidence

All 15 runs correctly chose `feed-west`. Five used the exact independent
provenance chain `record-d -> record-b`; five opened all four records. GLM used
the exact two-record path three times, Inkling twice, and the other trajectories
varied between three and four sources. The exposed provenance labels make this
a metadata-reliability condition, as intended.

## Non-Pass Trial Audit

| Trial | Classification | What happened |
| --- | --- | --- |
| `complementary-evidence__CUmfxWv` | Flash agent failure | Opened `record-a` and `record-d`; timed out without the required join or answer |
| `deployment-outage__g4pdPJW` | Flash agent failure | Opened three sources for 10,300 credits; timed out without an answer |
| `insufficient-evidence__mqJETDJ` | Flash agent failure | Opened all four sources; timed out without an answer |
| `deployment-outage__xJQn2qn` | Pro finality failure | Correct evidence and answer; only one Terminus completion confirmation before timeout |
| `insufficient-evidence__aWaPNkL` | GLM finality failure | Correct proof and answer; only one Terminus completion confirmation before timeout |
| `insufficient-evidence__gn5UAJu` | MiniMax task failure | Opened all evidence but reversed the explicitly required deployment-time answer order |
| `insufficient-evidence__XTJXUG8` | Inkling task failure | Submitted the correct abstention string after only two of three required proof records |
| `insufficient-evidence__ScoQwhN` | Modal infrastructure | Correct answer and finalized sidecar state; verifier directory download timed out |

The five Harbor `AgentTimeoutError` records split into two different behaviors:
three Flash runs never submitted an answer, while Pro and GLM submitted correct
answers but did not complete Terminus's two-step finalization within 120
seconds. Keeping verifier success and end-to-end success separate preserves
that distinction.

## Tool And Format Diagnostics

Across raw protected state, the 75 trials made 75 catalog calls, 203 source
opens, one status call, and 72 final answer submissions. There were no duplicate
open attempts. Flash made the only unknown-source call by trying to open the
already inferred deployment ID as if it were a source.

MiniMax made 12 non-evidence shell calls, mostly `ls`, `which evidence`, and
`evidence --help`. Flash made four. DeepSeek Pro, GLM, and Inkling made none.
Flash produced all three invalid-JSON turns. Terminus also logged extra-text
warning lines for Flash (88), Inkling (41), MiniMax (15), and Pro (14); GLM had
none. These warnings were usually recoverable and are diagnostics rather than
task failures.

## Tokens And Cost

| Model | Input tokens | Cached input | Output tokens | Recorded model cost |
| --- | ---: | ---: | ---: | ---: |
| GLM 5.2 | 118,258 | 57,211 | 22,310 | $0.15706090 |
| DeepSeek V4 Pro | 139,502 | 77,440 | 26,952 | $0.14374814 |
| MiniMax M3 | 197,124 | 156,552 | 18,281 | $0.04350192 |
| Inkling | 133,996 | 55,168 | 13,576 | $0.14318936 |
| DeepSeek V4 Flash | 172,327 | 41,600 | 26,591 | $0.02176364 |
| **Total** | **761,207** | **387,971** | **107,710** | **$0.50926395698** |

These are Harbor's provider telemetry fields. Cached input is reported
separately and may overlap provider input accounting, so the columns are not
summed into a synthetic total-token number.

The 74 verifier-backed trials consumed 353,150 synthetic evidence credits,
35,669 payload bytes, and an 8,967-token deterministic evidence proxy over
199 source opens. The infrastructure trial's finalized sidecar adds 13,100
credits, 696 bytes, 175 proxy tokens, and four opens, but those values are not
included in verifier-backed benchmark aggregates.

Harbor exposed no Terminus harness charge or Modal sandbox charge. The
manifest therefore records both as `null`, and total all-in spend is unknown.
Only the $0.50926395698 model-provider subtotal is supported by telemetry.

## Integrity And Security

- All 75 ATIF trajectories parse as schema `ATIF-v1.7`.
- All 75 protected sidecar snapshots are finalized and internally complete.
- All 75 artifact manifests parse; all 150 recorded artifact operations have status `ok`.
- All 74 verifier outputs have `verifier_integrity=1`.
- The one missing verifier output is explicitly classified as infrastructure.
- No result was retried, omitted, or replaced after observing its outcome.

The run used private task contracts before push, but agents had public egress.
This reduces straightforward repository lookup during this run; it does not
provide a strict closed-corpus guarantee. Static public contracts under Modal
VM networking remain unsuitable for a secure public leaderboard.

## Interpretation

The pilot demonstrates that the benchmark can separately observe correctness,
proof acquisition, synthetic evidence cost, tool behavior, and harness
finality. It also exposes three design confounds that should be addressed
before scaling:

1. Terminus 2's command-line and confirmation behavior contributes a strong tool-use and finality prior.
2. Five static tasks are too small to distinguish stable policy quality from task memorization or rollout variance.
3. Explicit seeds, downstream OpenRouter route, and all-in sandbox cost were not available, limiting exact reproducibility and cost comparison.

The next scientifically useful iteration is not a larger leaderboard over the
same five cases. It is a generated/private held-out population with neutral
labels and varied cost-relevance relationships, plus at least one contrasting
harness. Keep binary task success, evidence cost, real token use, and finality
as separate outputs. For the appetite thesis specifically, preserve and expand
answer-now cases until some configurations reliably choose the zero-open path.
