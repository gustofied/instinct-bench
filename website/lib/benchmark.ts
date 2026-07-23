import { Schema } from "effect";

import { benchmarkSource } from "@/lib/benchmark-data";
import {
  BenchmarkManifest,
  type BenchmarkTrajectory,
} from "@/lib/benchmark-schema";

export type { BenchmarkDomain } from "@/lib/benchmark-schema";

export const benchmark = Schema.decodeUnknownSync(BenchmarkManifest)(benchmarkSource);

const domains = benchmark.suites.flatMap((suite) => suite.domains);
const availableDomains = domains.filter(
  (domain) => domain.availability === "available",
);
const trajectories = availableDomains.flatMap((domain) => domain.trajectories);

const bestRun = trajectories.reduce<BenchmarkTrajectory | undefined>(
  (best, run) => (!best || run.reward > best.reward ? run : best),
  undefined,
);

export const benchmarkSummary = {
  domainCount: domains.length,
  taskCount: availableDomains.reduce(
    (total, domain) =>
      total +
      domain.taskSets.reduce(
        (domainTotal, taskSet) => domainTotal + taskSet.tasks,
        0,
      ),
    0,
  ),
  averageScore:
    trajectories.length > 0
      ? trajectories.reduce((total, run) => total + run.reward, 0) /
        trajectories.length
      : undefined,
  bestRun,
} as const;
