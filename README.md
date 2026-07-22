# instinct-bench

A benchmark suite for agent instinct: when to act from internal capability,
when to seek external context, and when to stop.

Instinct here is not guessing. It is the model's adaptive toolbox: priors,
taste, analogy, style, visual sense, language sense, craft, and learned ways of
working. The benchmark asks whether agents can balance that internal context
against external evidence, tools, references, feedback, and time.

Early domains:

- `context-appetite`: choose how much context is enough before answering.
- `tool-restraint`: know when to use tools and when to act directly.
- `drawing`: make, inspect, repair, and continue from partial shape.
- `writing`: draft, revise, preserve voice, and stop before overworking.

## First Harbor Learning Task

The first implemented task is
[`deployment-outage`](tasks/context-appetite/answer-or-look/deployment-outage),
inside the `context-appetite` domain and `answer-or-look` task set. An agent must
identify an outage-causing deployment while choosing among evidence sources
with visible evidence-credit prices. Correctness and evidence sufficiency gate
task success; efficiency only adjusts successful scores.

This is one look-required Harbor learning instance, not yet a benchmark signal.
Evaluating context appetite requires a population spanning answer-now,
one-source, multi-source, and insufficient-evidence cases.

Run its reference solution with:

```bash
uvx --from 'harbor[modal]==0.20.0' harbor run \
  -p tasks/context-appetite/answer-or-look/deployment-outage \
  -a oracle \
  -e modal
```
