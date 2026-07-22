import { Schema } from "effect";

const Stage = Schema.Literal("shaping", "study");

const TaskSet = Schema.Struct({
  name: Schema.String,
  material: Schema.String,
  tasks: Schema.Number,
  verifier: Schema.String,
  stage: Stage,
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

const Domain = Schema.Struct({
  name: Schema.String,
  judgment: Schema.String,
  stage: Stage,
  taskSets: Schema.Array(TaskSet),
  trajectories: Schema.Array(Trajectory),
  artifacts: Schema.Array(Artifact),
});

const Suite = Schema.Struct({
  name: Schema.String,
  slug: Schema.String,
  description: Schema.String,
  domains: Schema.Array(Domain),
});

const BenchmarkManifest = Schema.Struct({
  name: Schema.String,
  version: Schema.String,
  status: Schema.String,
  mock: Schema.Boolean,
  suites: Schema.Array(Suite),
});

const source: unknown = {
  name: "instinct-bench",
  version: "0.1",
  status: "shaping",
  mock: true,
  suites: [
    {
      name: "instinct-bench",
      slug: "instinct-bench",
      description: "Stable tasks for repeatable comparison.",
      domains: [
        {
          name: "context-appetite",
          judgment: "Knowing how much context is enough.",
          stage: "shaping",
          taskSets: [
            {
              name: "minimum-context / qa",
              material: "variable-context questions",
              tasks: 24,
              verifier: "exact + rubric",
              stage: "shaping",
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
              artifacts: 4,
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
          ],
        },
        {
          name: "tool-restraint",
          judgment: "Calling a tool only when it improves the work.",
          stage: "shaping",
          taskSets: [
            {
              name: "tool-restraint / choice",
              material: "tool-enabled tasks",
              tasks: 18,
              verifier: "trace grader",
              stage: "shaping",
            },
          ],
          trajectories: [
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
          ],
          artifacts: [
            {
              name: "task.yaml",
              role: "task definition",
              source: "tool-use-009",
              size: "2.9 KB",
            },
            {
              name: "trajectory.jsonl",
              role: "tool + reasoning trace",
              source: "run-0039",
              size: "102 KB",
            },
            {
              name: "verifier-report.json",
              role: "reward breakdown",
              source: "run-0039",
              size: "5.8 KB",
            },
          ],
        },
        {
          name: "drawing",
          judgment: "Inspecting, repairing, and continuing a partial form.",
          stage: "study",
          taskSets: [
            {
              name: "drawing / continuation",
              material: "image sequences",
              tasks: 12,
              verifier: "vlm + human",
              stage: "study",
            },
          ],
          trajectories: [
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
              artifacts: 3,
            },
          ],
          artifacts: [
            {
              name: "prompt.png",
              role: "partial form",
              source: "draw-form-003",
              size: "780 KB",
            },
            {
              name: "final.png",
              role: "submitted artifact",
              source: "draw-form-003",
              size: "1.2 MB",
            },
            {
              name: "verifier-report.json",
              role: "reward breakdown",
              source: "run-0034",
              size: "7.1 KB",
            },
          ],
        },
        {
          name: "writing",
          judgment: "Revising without sanding away the voice.",
          stage: "study",
          taskSets: [
            {
              name: "writing / revision",
              material: "drafts + revisions",
              tasks: 16,
              verifier: "pairwise judge",
              stage: "study",
            },
          ],
          trajectories: [
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
              artifacts: 3,
            },
          ],
          artifacts: [
            {
              name: "draft.md",
              role: "source draft",
              source: "voice-edit-021",
              size: "8.4 KB",
            },
            {
              name: "revision.md",
              role: "submitted artifact",
              source: "run-0028",
              size: "7.9 KB",
            },
            {
              name: "verifier-report.json",
              role: "reward breakdown",
              source: "run-0028",
              size: "5.2 KB",
            },
          ],
        },
      ],
    },
    {
      name: "instinct-bench-live",
      slug: "instinct-bench-live",
      description: "Recurring tasks drawn from changing conditions.",
      domains: [
        {
          name: "coastal-reading",
          judgment: "Reading current coastal conditions from public observations.",
          stage: "study",
          taskSets: [
            {
              name: "coastal-reading / duck-nc",
              material: "camera frames + colocated sensors",
              tasks: 1,
              verifier: "timestamped sensor truth",
              stage: "study",
            },
          ],
          trajectories: [
            {
              id: "run-live-0001",
              task: "duck-nc-2026-07-22",
              model: "gpt-5",
              harness: "codex",
              variant: "daily",
              result: "review",
              reward: 0.63,
              steps: 10,
              cost: "$0.08",
              artifacts: 3,
            },
          ],
          artifacts: [
            {
              name: "frame.jpg",
              role: "timestamped observation",
              source: "duck-nc-2026-07-22",
              size: "640 KB",
            },
            {
              name: "observation.json",
              role: "colocated sensor truth",
              source: "duck-nc-2026-07-22",
              size: "4.1 KB",
            },
            {
              name: "verifier-report.json",
              role: "reward breakdown",
              source: "run-live-0001",
              size: "5.9 KB",
            },
          ],
        },
      ],
    },
  ],
};

export type BenchmarkDomain = Schema.Schema.Type<typeof Domain>;

export const benchmark = Schema.decodeUnknownSync(BenchmarkManifest)(source);
