import { ArrowUpRight } from "lucide-react";

import { Reveal } from "@/components/reveal";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { benchmark } from "@/lib/benchmark";
import { cn } from "@/lib/utils";

const mobileCell =
  "max-md:grid max-md:w-full max-md:grid-cols-[90px_minmax(0,1fr)] max-md:items-baseline max-md:border-0 max-md:px-0 max-md:py-1.5 max-md:before:font-mono max-md:before:text-[9px] max-md:before:text-muted max-md:before:uppercase max-md:before:content-[attr(data-label)]";

const taskCount = benchmark.evaluations.reduce(
  (total, evaluation) => total + evaluation.tasks,
  0,
);

function SectionHeading({
  count,
  description,
  title,
}: {
  count: string;
  description: string;
  title: string;
}) {
  return (
    <div className="mb-3 grid grid-cols-[minmax(0,1fr)_auto] items-end gap-6 max-sm:grid-cols-1 max-sm:gap-1">
      <div>
        <h2 className="font-serif text-[21px] font-normal leading-none">{title}</h2>
        <p className="mt-1 text-[12px] text-muted">{description}</p>
      </div>
      <span className="font-mono text-[9px] text-muted uppercase">{count}</span>
    </div>
  );
}

function Status({ value }: { value: string }) {
  const color =
    value === "pass"
      ? "bg-ink"
      : value === "review"
        ? "bg-registration-yellow"
        : value === "fail"
          ? "bg-marker"
          : value === "shaping"
            ? "bg-marker"
            : "border border-marker bg-transparent";

  return (
    <span className="inline-flex items-center gap-2 font-mono text-[9px] uppercase">
      <span className={cn("size-1.5 shrink-0", color)} aria-hidden="true" />
      {value}
    </span>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="mx-auto w-[calc(100%-2rem)] max-w-[1024px] pb-10 max-md:w-[calc(100%-1.25rem)]">
        <Reveal>
          <header className="grid min-h-[58px] grid-cols-[1fr_auto_1fr] items-center border-b border-line py-2 max-md:grid-cols-1 max-md:gap-1.5 max-md:py-3">
            <a
              className="flex items-center gap-2.5 max-md:justify-center"
              href="/"
              aria-label="instinct-bench home"
            >
              <img
                className="h-[27px] w-auto"
                src="/instinct-bench-mark.png"
                alt=""
                width="615"
                height="455"
              />
              <span className="font-mono text-[10px] font-semibold uppercase">
                instinct-bench
              </span>
            </a>

            <nav
              className="flex items-center justify-center gap-6 text-[12px] max-md:gap-4"
              aria-label="Page sections"
            >
              <a className="text-muted hover:text-ink hover:underline" href="#evals">
                evals
              </a>
              <a
                className="text-muted hover:text-ink hover:underline"
                href="#trajectories"
              >
                trajectories
              </a>
              <a className="text-muted hover:text-ink hover:underline" href="#artifacts">
                artifacts
              </a>
            </nav>

            <span className="justify-self-end font-mono text-[9px] text-muted uppercase max-md:justify-self-center">
              mock data / v{benchmark.version}
            </span>
          </header>
        </Reveal>

        <Reveal delay={0.04}>
          <section aria-labelledby="page-title">
            <div className="grid min-h-[262px] grid-cols-[minmax(0,2fr)_minmax(240px,0.75fr)] items-center gap-14 py-8 max-md:min-h-0 max-md:grid-cols-1 max-md:gap-6 max-md:py-7">
              <h1
                id="page-title"
                className="flex min-h-[154px] min-w-0 items-center leading-none max-md:min-h-[104px]"
              >
                <span className="sr-only">{benchmark.name}</span>
                <img
                  className="block h-auto w-full max-w-[760px] -translate-y-[11%] object-contain object-left"
                  src="/instinct-bench-wordmark.png?v=2"
                  alt=""
                  width="1420"
                  height="248"
                />
              </h1>

              <div className="border-l border-line pl-7 max-md:border-t max-md:border-l-0 max-md:pt-5 max-md:pl-0">
                <p className="font-serif text-[17px] leading-[1.5] text-copy">
                  Testing the capacities that make agents useful: taste,
                  restraint, context judgment, craft, and control.
                </p>
                <a
                  aria-label="Made by gustofied on X"
                  className="group mt-5 inline-flex items-center gap-2 border-t border-line pt-3"
                  href="https://x.com/gustofied"
                  rel="noreferrer"
                  target="_blank"
                >
                  <span className="font-signature text-[18px] leading-none text-marker group-hover:underline">
                    made by @gustofied
                  </span>
                  <svg
                    aria-hidden="true"
                    className="size-3 shrink-0 -translate-y-px text-ink"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </a>
              </div>
            </div>

            <div className="grid grid-cols-4 border-y border-line max-sm:grid-cols-2">
              {[
                ["evals", benchmark.evaluations.length.toString().padStart(2, "0")],
                ["tasks", taskCount.toString().padStart(2, "0")],
                ["runs", benchmark.trajectories.length.toString().padStart(2, "0")],
                ["files", benchmark.artifacts.length.toString().padStart(2, "0")],
              ].map(([label, value], index) => (
                <div
                  className={cn(
                    "flex min-h-14 items-center justify-between gap-4 px-4",
                    index > 0 && "border-l border-line",
                    index === 2 && "max-sm:border-t max-sm:border-l-0",
                    index === 3 && "max-sm:border-t",
                  )}
                  key={label}
                >
                  <span className="font-mono text-[9px] text-muted uppercase">{label}</span>
                  <strong className="font-mono text-base font-medium">{value}</strong>
                </div>
              ))}
            </div>
          </section>
        </Reveal>

        <Reveal delay={0.08}>
          <section
            className="scroll-mt-6 pt-10"
            id="evals"
            aria-labelledby="evals-title"
          >
            <SectionHeading
              count={`${benchmark.evaluations.length.toString().padStart(2, "0")} evals / ${taskCount} tasks`}
              description="Judgments expressed as repeatable tasks."
              title="Eval index"
            />
            <Card>
              <CardContent className="p-0">
                <Table className="table-fixed max-md:block">
                  <TableHeader className="max-md:sr-only">
                    <TableRow className="border-line hover:bg-transparent">
                      <TableHead className="w-[23%]">Eval</TableHead>
                      <TableHead className="w-[32%]">Judgment</TableHead>
                      <TableHead className="w-[18%]">Material</TableHead>
                      <TableHead className="w-[9%]">Tasks</TableHead>
                      <TableHead className="w-[18%]">Verifier / stage</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody className="max-md:block">
                    {benchmark.evaluations.map((evaluation, index) => (
                      <TableRow
                        className="h-[70px] border-line hover:bg-faint max-md:block max-md:h-auto max-md:px-4 max-md:py-3"
                        key={evaluation.name}
                      >
                        <TableCell className={cn("w-[23%]", mobileCell)} data-label="Eval">
                          <span className="flex items-baseline">
                            <span className="w-[30px] shrink-0 font-mono text-[9px] text-marker">
                              {(index + 1).toString().padStart(2, "0")}
                            </span>
                            <strong className="font-medium">{evaluation.name}</strong>
                          </span>
                        </TableCell>
                        <TableCell className={cn("w-[32%] text-copy", mobileCell)} data-label="Judgment">
                          {evaluation.judgment}
                        </TableCell>
                        <TableCell className={cn("w-[18%] text-copy", mobileCell)} data-label="Material">
                          {evaluation.material}
                        </TableCell>
                        <TableCell className={cn("w-[9%] font-mono", mobileCell)} data-label="Tasks">
                          {evaluation.tasks.toString().padStart(2, "0")}
                        </TableCell>
                        <TableCell className={cn("w-[18%]", mobileCell)} data-label="Verifier">
                          <span className="flex flex-col items-start gap-1.5">
                            <span className="text-[12px] text-copy">{evaluation.verifier}</span>
                            <Status value={evaluation.stage} />
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </section>
        </Reveal>

        <Reveal delay={0.12}>
          <section
            className="scroll-mt-6 pt-10"
            id="trajectories"
            aria-labelledby="trajectories-title"
          >
            <SectionHeading
              count={`${benchmark.trajectories.length.toString().padStart(2, "0")} mock runs`}
              description="Attempts, costs, and outputs."
              title="Trajectories"
            />
            <Card>
              <CardContent className="p-0">
                <Table className="table-fixed max-md:block">
                  <TableHeader className="max-md:sr-only">
                    <TableRow className="border-line hover:bg-transparent">
                      <TableHead className="w-[25%]">Task / run</TableHead>
                      <TableHead className="w-[25%]">Model / harness</TableHead>
                      <TableHead className="w-[14%]">Variant</TableHead>
                      <TableHead className="w-[12%]">Result</TableHead>
                      <TableHead className="w-[8%]">Reward</TableHead>
                      <TableHead className="w-[8%]">Steps</TableHead>
                      <TableHead className="w-[8%]">Cost</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody className="max-md:block">
                    {benchmark.trajectories.map((trajectory) => (
                      <TableRow
                        className="h-[68px] border-line hover:bg-faint max-md:block max-md:h-auto max-md:px-4 max-md:py-3"
                        key={trajectory.id}
                      >
                        <TableCell className={cn("w-[25%]", mobileCell)} data-label="Task">
                          <span className="flex flex-col gap-1">
                            <strong className="font-medium">{trajectory.task}</strong>
                            <span className="font-mono text-[9px] text-muted uppercase">
                              {trajectory.id} / {trajectory.artifacts} files
                            </span>
                          </span>
                        </TableCell>
                        <TableCell className={cn("w-[25%]", mobileCell)} data-label="Agent">
                          <span className="flex flex-col gap-1">
                            <span>{trajectory.model}</span>
                            <span className="font-mono text-[9px] text-muted uppercase">{trajectory.harness}</span>
                          </span>
                        </TableCell>
                        <TableCell className={cn("w-[14%] text-copy", mobileCell)} data-label="Variant">
                          {trajectory.variant}
                        </TableCell>
                        <TableCell className={cn("w-[12%]", mobileCell)} data-label="Result">
                          <Status value={trajectory.result} />
                        </TableCell>
                        <TableCell className={cn("w-[8%] font-mono", mobileCell)} data-label="Reward">
                          {trajectory.reward.toFixed(2)}
                        </TableCell>
                        <TableCell className={cn("w-[8%] font-mono", mobileCell)} data-label="Steps">
                          {trajectory.steps.toString().padStart(2, "0")}
                        </TableCell>
                        <TableCell className={cn("w-[8%] font-mono", mobileCell)} data-label="Cost">
                          {trajectory.cost}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </section>
        </Reveal>

        <Reveal delay={0.16}>
          <section
            className="scroll-mt-6 pt-10"
            id="artifacts"
            aria-labelledby="artifacts-title"
          >
            <SectionHeading
              count={`${benchmark.artifacts.length.toString().padStart(2, "0")} mock files`}
              description="Task, trace, verifier, and submitted output."
              title="Artifacts"
            />
            <Card>
              <CardContent className="p-0">
                <Table className="table-fixed max-md:block">
                  <TableHeader className="max-md:sr-only">
                    <TableRow className="border-line hover:bg-transparent">
                      <TableHead className="w-[28%]">File</TableHead>
                      <TableHead className="w-[34%]">Role</TableHead>
                      <TableHead className="w-[25%]">Source</TableHead>
                      <TableHead className="w-[13%]">Size</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody className="max-md:block">
                    {benchmark.artifacts.map((artifact, index) => (
                      <TableRow
                        className="h-[58px] border-line hover:bg-faint max-md:block max-md:h-auto max-md:px-4 max-md:py-3"
                        key={artifact.name}
                      >
                        <TableCell className={cn("w-[28%]", mobileCell)} data-label="File">
                          <span className="flex items-baseline">
                            <span className="w-[30px] shrink-0 font-mono text-[9px] text-marker">
                              {(index + 1).toString().padStart(2, "0")}
                            </span>
                            <strong className="font-mono text-[12px] font-medium">{artifact.name}</strong>
                          </span>
                        </TableCell>
                        <TableCell className={cn("w-[34%] text-copy", mobileCell)} data-label="Role">
                          {artifact.role}
                        </TableCell>
                        <TableCell className={cn("w-[25%] font-mono text-[11px]", mobileCell)} data-label="Source">
                          {artifact.source}
                        </TableCell>
                        <TableCell className={cn("w-[13%] font-mono", mobileCell)} data-label="Size">
                          {artifact.size}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </section>
        </Reveal>

        <Reveal delay={0.2}>
          <footer className="mt-10 flex items-center justify-between gap-8 border-t border-line py-5 max-md:flex-col max-md:items-start">
            <span className="font-mono text-[9px] text-muted uppercase">
              instinct-bench / mock interface
            </span>
            <a
              className="inline-flex items-center gap-1 text-[12px] hover:underline"
              href="https://github.com/gustofied/instinct-bench"
              target="_blank"
              rel="noreferrer"
            >
              source
              <ArrowUpRight aria-hidden="true" size={11} strokeWidth={1.5} />
            </a>
          </footer>
        </Reveal>
      </div>
    </main>
  );
}
