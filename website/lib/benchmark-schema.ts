import { Schema } from "effect";

export const BenchmarkStage = Schema.Literal("shaping", "study");
export const DomainAvailability = Schema.Literal("available", "planned");
export const SuiteMode = Schema.Literal("fixed", "live");

export const TaskSet = Schema.Struct({
  name: Schema.String,
  material: Schema.String,
  tasks: Schema.Number,
  verifier: Schema.String,
  stage: BenchmarkStage,
});

export const TrajectoryResult = Schema.Literal("pass", "review", "fail");

export const Trajectory = Schema.Struct({
  id: Schema.String,
  task: Schema.String,
  model: Schema.String,
  harness: Schema.String,
  runtime: Schema.String,
  variant: Schema.String,
  result: TrajectoryResult,
  reward: Schema.Number,
  steps: Schema.Number,
  cost: Schema.String,
  artifacts: Schema.Number,
});

export const Artifact = Schema.Struct({
  name: Schema.String,
  role: Schema.String,
  source: Schema.String,
  size: Schema.String,
});

export const Domain = Schema.Struct({
  name: Schema.String,
  slug: Schema.String,
  judgment: Schema.String,
  stage: BenchmarkStage,
  availability: DomainAvailability,
  taskSets: Schema.Array(TaskSet),
  trajectories: Schema.Array(Trajectory),
  artifacts: Schema.Array(Artifact),
});

export const Suite = Schema.Struct({
  name: Schema.String,
  slug: Schema.String,
  mode: SuiteMode,
  description: Schema.String,
  domains: Schema.Array(Domain),
});

export const BenchmarkManifest = Schema.Struct({
  name: Schema.String,
  version: Schema.String,
  status: BenchmarkStage,
  mock: Schema.Boolean,
  suites: Schema.Array(Suite),
});

export type BenchmarkDomain = Schema.Schema.Type<typeof Domain>;
export type BenchmarkManifest = Schema.Schema.Type<typeof BenchmarkManifest>;
export type BenchmarkTrajectory = Schema.Schema.Type<typeof Trajectory>;
