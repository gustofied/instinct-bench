import { ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";

import { DomainDrawer } from "@/components/domain-drawer";
import { Reveal } from "@/components/reveal";
import { benchmarkTelemetry } from "@/lib/benchmark-data";
import { benchmark, benchmarkSummary } from "@/lib/benchmark";
import { cn } from "@/lib/utils";

const costResources = [
  {
    label: "Inference",
    value: benchmarkTelemetry.cost.inferencePerTask,
    status: "recorded",
    tooltip:
      "All model calls on the agent path. Recorded spend: $0.79675688 total, or $0.010623 per task. Judge and verifier inference is evaluation overhead.",
  },
  {
    label: "Runtime",
    value: `≥${benchmarkTelemetry.cost.runtimePerTask}`,
    status: "reconstructed",
    tooltip:
      "The executing sandbox or container environment. Requested-resource reconstruction: at least $0.41226556 total, or $0.005497 per task.",
  },
] as const;

function InfoTooltip({
  align = "right",
  className,
  id,
  label,
  text,
  triggerText,
}: {
  align?: "left" | "responsive" | "right";
  className?: string;
  id: string;
  label: string;
  text: string;
  triggerText: string;
}) {
  return (
    <span
      className={cn(
        "group/info relative inline-flex min-w-0 items-center gap-0.5",
        className,
      )}
    >
      <span>{triggerText}</span>
      <span className="relative inline-flex size-3 shrink-0">
        <button
          aria-describedby={id}
          aria-label={label}
          className="absolute top-1/2 left-1/2 inline-flex size-6 -translate-x-1/2 -translate-y-1/2 cursor-help items-center justify-center font-mono text-[8px] leading-none text-muted underline decoration-dotted underline-offset-2 outline-none hover:text-ink focus-visible:text-ink focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-1 focus-visible:outline-ink"
          type="button"
        >
          ?
        </button>
      </span>
      <span
        className={cn(
          "pointer-events-none invisible absolute bottom-[calc(100%+0.5rem)] z-40 w-56 max-w-[calc(100vw-1.5rem)] border border-ink bg-ink px-3 py-2.5 text-left font-sans text-[11px] leading-[1.5] font-normal whitespace-normal text-paper normal-case opacity-0 transition-opacity group-hover/info:visible group-hover/info:opacity-100 group-focus-within/info:visible group-focus-within/info:opacity-100",
          align === "left" && "left-0",
          align === "right" && "right-0",
          align === "responsive" &&
            "left-0 min-[560px]:right-0 min-[560px]:left-auto",
        )}
        id={id}
        role="tooltip"
      >
        {text}
      </span>
    </span>
  );
}

function CostBreakdown({
  idPrefix,
  items,
}: {
  idPrefix: string;
  items: ReadonlyArray<{
    label: string;
    status: string;
    tooltip: string;
    value: string;
  }>;
}) {
  return (
    <span className="grid min-w-0 grid-cols-2 border-t border-line pt-2.5">
      {items.map(({ label, status, tooltip, value }, index) => (
        <span
          className={cn(
            "grid min-w-0 gap-1 px-2 font-mono",
            index === 0 ? "pl-0" : "border-l border-line",
            index === items.length - 1 && "pr-0",
          )}
          key={label}
        >
          <InfoTooltip
            align={index === 0 ? "left" : "right"}
            className="text-[8px] text-muted"
            id={`${idPrefix}-${label.toLowerCase()}-tooltip`}
            label={`What ${label} means for ${idPrefix}`}
            text={tooltip}
            triggerText={label}
          />
          <strong className="text-[10px] font-medium tabular-nums">
            {value}
          </strong>
          <span className="text-[7px] text-muted uppercase">{status}</span>
        </span>
      ))}
    </span>
  );
}

function TaskMetric({
  children,
  idPrefix,
  label,
  tooltip,
  value,
  valueMarker,
  valueNote,
}: {
  children?: ReactNode;
  idPrefix: string;
  label: string;
  tooltip?: {
    label: string;
    text: string;
  };
  value: string;
  valueMarker?: string;
  valueNote?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col justify-between border border-line px-3 py-3",
        children ? "min-h-[112px]" : "min-h-[58px] min-[560px]:min-h-[112px]",
      )}
    >
      <div className="flex min-h-[34px] items-start justify-between gap-4">
        {tooltip ? (
          <InfoTooltip
            align="responsive"
            className="min-h-6 gap-1 font-mono text-[9px] text-muted"
            id={`${idPrefix}-tooltip`}
            label={tooltip.label}
            text={tooltip.text}
            triggerText={label}
          />
        ) : (
          <span className="inline-flex min-h-6 items-center font-mono text-[9px] text-muted">
            {label}
          </span>
        )}
        <span className="grid justify-items-end font-mono">
          <span className="inline-flex min-h-6 items-center gap-1.5">
            <strong className="text-right text-[16px] leading-none font-medium tabular-nums">
              {value}
            </strong>
            {valueMarker && (
              <span className="text-[8px] text-muted">{valueMarker}</span>
            )}
          </span>
          {valueNote && (
            <span className="text-[7px] text-muted uppercase">{valueNote}</span>
          )}
        </span>
      </div>
      {children}
    </div>
  );
}

function SectionHeading({
  count,
  description,
  id,
  title,
}: {
  count: string;
  description: string;
  id: string;
  title: string;
}) {
  return (
    <div className="mb-3 grid grid-cols-1 gap-1 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end sm:gap-6">
      <div>
        <h2 className="font-serif text-[21px] font-normal leading-none" id={id}>
          {title}
        </h2>
        <p className="mt-1 text-[12px] text-muted">{description}</p>
      </div>
      <span className="font-mono text-[9px] text-muted uppercase">{count}</span>
    </div>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="mx-auto w-[calc(100%-1.25rem)] max-w-[1024px] pb-10 md:w-[calc(100%-2rem)]">
        <Reveal>
          <header className="grid min-h-[58px] grid-cols-[auto_1fr] items-center gap-x-3 gap-y-2 border-b border-line py-2.5 min-[560px]:grid-cols-[1fr_auto_1fr] min-[560px]:gap-0 min-[560px]:py-2">
            <a
              className="col-start-1 row-start-1 flex items-center justify-self-start"
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
            </a>

            <nav
              className="col-span-2 row-start-2 flex items-center justify-center gap-3 font-mono text-[9px] min-[560px]:col-span-1 min-[560px]:col-start-2 min-[560px]:row-start-1 md:gap-6 md:font-sans md:text-[12px]"
              aria-label="Benchmark suites"
            >
              <a className="text-muted hover:text-ink hover:underline" href="#instinct-bench">
                instinct-bench
              </a>
              <a
                className="text-muted hover:text-ink hover:underline"
                href="#instinct-bench-live"
              >
                instinct-bench-live
              </a>
              <span
                aria-disabled="true"
                className="cursor-default text-muted opacity-[0.45]"
              >
                instinct-learning
              </span>
            </nav>

            <nav
              aria-label="Project links"
              className="col-start-2 row-start-1 flex items-center justify-self-end gap-2 font-mono text-[9px] text-muted uppercase min-[560px]:col-start-3"
            >
              <a
                className="hover:text-ink hover:underline"
                href="https://x.com/instinctbench"
                rel="noreferrer"
                target="_blank"
              >
                X
              </a>
              <span aria-hidden="true">/</span>
              <a
                className="hover:text-ink hover:underline"
                href="https://hub.harborframework.com/organizations/instinct-bench"
                rel="noreferrer"
                target="_blank"
              >
                Harbor
              </a>
              <span aria-hidden="true">/</span>
              <a
                className="hover:text-ink hover:underline"
                href="https://github.com/gustofied/instinct-bench"
                rel="noreferrer"
                target="_blank"
              >
                GitHub
              </a>
            </nav>
          </header>
        </Reveal>

        <Reveal delay={0.04}>
          <section aria-labelledby="page-title">
            <div className="grid min-h-0 grid-cols-1 items-center gap-6 pt-9 pb-7 md:min-h-[262px] md:grid-cols-[minmax(0,2fr)_minmax(240px,0.75fr)] md:gap-14 md:py-8">
              <h1
                id="page-title"
                className="flex min-h-[104px] min-w-0 items-center leading-none md:min-h-[154px]"
              >
                <span className="sr-only">{benchmark.name}</span>
                <img
                  className="block h-auto w-full max-w-[760px] -translate-y-[11%] object-contain object-left"
                  src="/instinct-bench-wordmark.png?v=3"
                  alt=""
                  width="1419"
                  height="259"
                />
              </h1>

              <div className="border-t border-line pt-5 md:border-t-0 md:border-l md:pt-0 md:pl-7">
                <p className="mx-auto max-w-[44ch] text-center font-serif text-[17px] leading-[1.5] text-copy md:mx-0 md:max-w-none md:text-left">
                  Testing the capacities that make agents useful: taste,
                  restraint, context judgment, craft, and control.
                </p>
                <div className="mt-5 flex justify-center md:justify-start">
                  <a
                    aria-label="Made by gustofied"
                    className="group inline-flex cursor-pointer items-center outline-none md:border-t md:border-line md:pt-3"
                    href="https://x.com/gustofied"
                    rel="noreferrer"
                    target="_blank"
                  >
                    <span className="font-signature text-[18px] leading-none text-marker">
                      made by{" "}
                      <span className="underline decoration-marker/70 underline-offset-4 group-hover:decoration-2 group-focus-visible:decoration-2">
                        @gustofied
                      </span>
                    </span>
                  </a>
                </div>
              </div>
            </div>

            <div className="grid gap-2.5">
              <div className="grid grid-cols-3 border border-line md:grid-cols-4">
                {[
                  {
                    label: "domains",
                    value: benchmarkSummary.domainCount.toString().padStart(2, "0"),
                  },
                  {
                    label: "tasks",
                    value: benchmarkSummary.taskCount.toString().padStart(2, "0"),
                  },
                ].map(({ label, value }, index) => (
                  <div
                    className={cn(
                      "flex min-h-[66px] flex-col items-start justify-center gap-1.5 px-3 py-2.5",
                      index > 0 && "border-l border-line",
                    )}
                    key={label}
                  >
                    <span className="font-mono text-[9px] text-muted uppercase">
                      {label}
                    </span>
                    <strong className="font-mono text-[15px] font-medium">
                      {value}
                    </strong>
                  </div>
                ))}

                <div className="flex min-h-[66px] flex-col items-start justify-center gap-1.5 border-l border-line px-3 py-2.5">
                  <span className="font-mono text-[9px] text-muted uppercase">
                    avg score
                  </span>
                  <strong className="font-mono text-[15px] font-medium">
                    {benchmarkSummary.averageScore?.toFixed(2) ?? "—"}
                  </strong>
                </div>

                <div className="col-span-3 flex min-h-[66px] items-center justify-between gap-4 border-t border-line px-3 py-2.5 md:col-span-1 md:flex-col md:items-start md:justify-center md:gap-1.5 md:border-t-0 md:border-l">
                  <span className="font-mono text-[9px] text-muted uppercase">
                    best agent
                  </span>
                  <span className="grid min-w-0 grid-cols-[auto_minmax(0,1fr)] gap-x-1.5 gap-y-0.5 text-right font-mono md:text-left">
                    <span className="text-[8px] text-muted">Model:</span>
                    <strong className="truncate text-[9px] font-medium">
                      {benchmarkSummary.bestRun?.model ?? "—"}
                    </strong>
                    <span className="text-[8px] text-muted">Harness:</span>
                    <strong className="truncate text-[9px] font-medium">
                      {benchmarkSummary.bestRun?.harness ?? "—"}
                    </strong>
                    <span className="text-[8px] text-muted">Runtime:</span>
                    <strong className="truncate text-[9px] font-medium">
                      {benchmarkSummary.bestRun?.runtime ?? "—"}
                    </strong>
                  </span>
                </div>
              </div>

              <div className="grid gap-2.5 min-[560px]:grid-cols-2">
                <TaskMetric
                  idPrefix="cost"
                  label="$ / task"
                  tooltip={{
                    label: "How cost per task is measured",
                    text: "Agent-path lower bound from v0.3.0. Recorded inference is $0.010623 per task and reconstructed main runtime is at least $0.005497 per task. Verifier runtime, reconstructed at $0.001614 per task, and other evaluation overhead are excluded.",
                  }}
                  value={`≥${benchmarkTelemetry.cost.lowerBoundPerTask}`}
                  valueNote="agent path floor"
                >
                  <CostBreakdown idPrefix="cost" items={costResources} />
                </TaskMetric>
                <TaskMetric
                  idPrefix="latency"
                  label="latency"
                  tooltip={{
                    label: "How latency is measured",
                    text: "Agent execution time, from instruction received to final submission.",
                  }}
                  value={`${benchmarkTelemetry.latency.p50Seconds}s`}
                  valueMarker="p50"
                />
              </div>
            </div>
          </section>
        </Reveal>

        {benchmark.suites.map((suite, suiteIndex) => (
          <Reveal delay={0.08 + suiteIndex * 0.04} key={suite.slug}>
            <section
              className="scroll-mt-6 pt-10"
              id={suite.slug}
              aria-labelledby={`${suite.slug}-title`}
            >
              <SectionHeading
                count={`${suite.domains.length.toString().padStart(2, "0")} ${suite.domains.length === 1 ? "domain" : "domains"}`}
                description={suite.description}
                id={`${suite.slug}-title`}
                title={suite.name}
              />
              <div className="border border-line">
                {suite.domains.map((domain, domainIndex) => (
                  <DomainDrawer
                    defaultOpen={
                      domainIndex === 0 && domain.availability === "available"
                    }
                    domain={domain}
                    key={domain.name}
                    live={suite.mode === "live"}
                  />
                ))}
              </div>
            </section>
          </Reveal>
        ))}

        <Reveal delay={0.2}>
          <footer className="mt-10 flex flex-col items-start justify-between gap-8 border-t border-line py-5 md:flex-row md:items-center">
            <span className="font-mono text-[9px] text-muted uppercase">
              instinct-bench
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
