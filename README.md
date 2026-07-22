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

## First Harbor Task

The first frozen task is
[`deployment-outage`](tasks/context-appetite/answer-or-look/deployment-outage),
inside the `context-appetite` domain and `answer-or-look` task set. An agent must
identify an outage-causing deployment while choosing among evidence sources
with visible context prices. Correctness and context use are scored separately,
and the combined reward is gated by correctness.

Run its reference solution with:

```bash
harbor run \
  -p tasks/context-appetite/answer-or-look/deployment-outage \
  -a oracle \
  -e docker
```
