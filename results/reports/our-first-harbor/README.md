# Our First Harbor

Status: post-run engineering and scientific review, 2026-07-23.

This dossier reviews the first complete `context-appetite` Harbor build and the
75-trial model pilot at commit `46832c4`. It uses the local `eval-engineering`
workflow: map the agent and environment, inspect traces, audit the verifier,
separate target behavior from infrastructure, then approve or revise the next
experiment.

## Read This In Order

1. [Build review](build-review.md): what was built, what Harbor taught us, and
   which parts are sound.
2. [Pilot audit](pilot-audit.md): findings first, corrected run accounting, and
   the honest claim supported by the 75 traces.
3. [Research and v0.3 design](research-and-v0.3.md): scientific precedents,
   scoring, task population, and the next controlled run.
4. [Job archive](job-archive.md): the non-destructive cleanup record for the
   local Harbor dashboard.

The original as-run artifacts remain available:

- [Historical pilot report](../context-appetite-v0.2.1-model-pilot-3x-001.md)
- [Normalized run manifest](../../manifests/context-appetite-v0.2.1-model-pilot-3x-001.json)
- Raw job: `jobs/context-appetite-v0.2.1-model-pilot-3x-001`

## Verdict

The engineering pilot is successful. Harbor 0.20, Terminus 2, Modal, the
protected evidence sidecar, artifact collection, separate verifier, ATIF
traces, and normalized reporting all worked together. The run is valuable and
must be retained.

The scientific benchmark is not ready for a leaderboard or another broad model
sweep. Five fixed tasks cannot estimate a general context-appetite policy, and
the current presentation confounds source position, source price, prompt
demand, and Terminus behavior. The next money should buy a controlled
experiment over private randomized instances, not more repetitions of these
five cases.

## Corrected Snapshot

- 75 planned trial cells and 75 raw trial directories.
- 69 trials completed the agent phase normally and produced a valid verifier
  result.
- 5 trials hit the hidden 120-second agent deadline; their protected ledgers
  are useful diagnostics, not primary task outcomes.
- 1 trial completed the agent phase but failed while downloading the verifier
  directory from Modal.
- Of the 69 benchmark-valid trials, 67 passed the exact all-pass contract.
- One additional MiniMax result was semantically correct and sufficiently
  evidenced but reversed an explicitly requested candidate order.
- The remaining normal-completion failure was an Inkling abstention after
  omitting evidence that could still have resolved causality.
- All 15 `answer-now` runs opened evidence despite sufficient initial context.

No new paid 75-run sweep is authorized by this review. The proposed next run is
described in [research and v0.3 design](research-and-v0.3.md).
