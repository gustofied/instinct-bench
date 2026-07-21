import { Schema } from "effect";

const EvaluationStage = Schema.Literal("shaping", "study");

const Evaluation = Schema.Struct({
  name: Schema.String,
  judgment: Schema.String,
  material: Schema.String,
  tasks: Schema.Number,
  verifier: Schema.String,
  stage: EvaluationStage,
});

const TrajectoryResult = Schema.Literal("pass", "review", "fail");

const Trajectory = Schema.Struct({
  id: Schema.String,
  task: Schema.String,
  model: Schema.String,
  harness: Schema.String,
  variant: Schema.String,
  result: TrajectoryResult,
  reward: Schema.Number,
  steps: Schema.Number,
  cost: Schema.String,
  artifacts: Schema.Number,
});

const Artifact = Schema.Struct({
  name: Schema.String,
  role: Schema.String,
  source: Schema.String,
  size: Schema.String,
});

const BenchmarkManifest = Schema.Struct({
  name: Schema.String,
  version: Schema.String,
  status: Schema.String,
  mock: Schema.Boolean,
  evaluations: Schema.Array(Evaluation),
  trajectories: Schema.Array(Trajectory),
  artifacts: Schema.Array(Artifact),
});

const source: unknown = {
  name: "instinct-bench",
  version: "0.1",
  status: "shaping",
  mock: true,
  evaluations: [
    {
      name: "context-appetite",
      judgment: "Knowing how much context is enough.",
      material: "variable-context questions",
      tasks: 24,
      verifier: "exact + rubric",
      stage: "shaping",
    },
    {
      name: "tool-restraint",
      judgment: "Calling a tool only when it improves the work.",
      material: "tool-enabled tasks",
      tasks: 18,
      verifier: "trace grader",
      stage: "shaping",
    },
    {
      name: "drawing",
      judgment: "Inspecting, repairing, and continuing a partial form.",
      material: "image sequences",
      tasks: 12,
      verifier: "vlm + human",
      stage: "study",
    },
    {
      name: "writing",
      judgment: "Revising without sanding away the voice.",
      material: "drafts + revisions",
      tasks: 16,
      verifier: "pairwise judge",
      stage: "study",
    },
  ],
  trajectories: [
    {
      id: "run-0042",
      task: "context-short-014",
      model: "laguna-xs-2.1",
      harness: "pool",
      variant: "4k context",
      result: "pass",
      reward: 0.92,
      steps: 7,
      cost: "$0.03",
      artifacts: 5,
    },
    {
      id: "run-0039",
      task: "tool-use-009",
      model: "claude-sonnet-4",
      harness: "terminus-2",
      variant: "tools on",
      result: "pass",
      reward: 0.86,
      steps: 11,
      cost: "$0.11",
      artifacts: 3,
    },
    {
      id: "run-0034",
      task: "draw-form-003",
      model: "gpt-5",
      harness: "codex",
      variant: "visual",
      result: "review",
      reward: 0.71,
      steps: 16,
      cost: "$0.14",
      artifacts: 4,
    },
    {
      id: "run-0028",
      task: "voice-edit-021",
      model: "gemini-2.5-pro",
      harness: "terminus-2",
      variant: "editorial",
      result: "fail",
      reward: 0.44,
      steps: 9,
      cost: "$0.07",
      artifacts: 2,
    },
  ],
  artifacts: [
    {
      name: "task.yaml",
      role: "task definition",
      source: "context-short-014",
      size: "3.2 KB",
    },
    {
      name: "instruction.md",
      role: "agent prompt",
      source: "context-short-014",
      size: "1.8 KB",
    },
    {
      name: "trajectory.jsonl",
      role: "tool + reasoning trace",
      source: "run-0042",
      size: "84 KB",
    },
    {
      name: "verifier-report.json",
      role: "reward breakdown",
      source: "run-0042",
      size: "6.4 KB",
    },
    {
      name: "final.png",
      role: "submitted artifact",
      source: "draw-form-003",
      size: "1.2 MB",
    },
  ],
};

export const benchmark = Schema.decodeUnknownSync(BenchmarkManifest)(source);
