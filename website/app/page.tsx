import { ArrowUpRight } from "lucide-react";

import { DomainDrawer } from "@/components/domain-drawer";
import { Reveal } from "@/components/reveal";
import { benchmark } from "@/lib/benchmark";
import { cn } from "@/lib/utils";

const domains = benchmark.suites.flatMap((suite) => suite.domains);
const trajectories = domains.flatMap((domain) => domain.trajectories);
const taskCount = domains.reduce(
  (total, domain) =>
    total + domain.taskSets.reduce((domainTotal, taskSet) => domainTotal + taskSet.tasks, 0),
  0,
);
const averageScore =
  trajectories.reduce((total, trajectory) => total + trajectory.reward, 0) /
  trajectories.length;
const bestRun = trajectories.reduce((best, trajectory) =>
  trajectory.reward > best.reward ? trajectory : best,
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
                  src="/instinct-bench-wordmark.png?v=3"
                  alt=""
                  width="1419"
                  height="259"
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
                {
                  label: "domains",
                  value: domains.length.toString().padStart(2, "0"),
                },
                { label: "tasks", value: taskCount.toString().padStart(2, "0") },
                { label: "avg score", value: averageScore.toFixed(2) },
                {
                  label: "best model",
                  value: bestRun.model,
                  score: bestRun.reward.toFixed(2),
                },
              ].map(({ label, score, value }, index) => (
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
                  <span className="flex min-w-0 items-baseline justify-end gap-1.5">
                    <strong
                      className={cn(
                        "font-mono font-medium",
                        label === "best model" ? "truncate text-[10px]" : "text-base",
                      )}
                    >
                      {value}
                    </strong>
                    {score ? (
                      <span className="shrink-0 font-mono text-[9px] text-marker">
                        / {score}
                      </span>
                    ) : null}
                  </span>
                </div>
              ))}
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
                title={suite.name}
              />
              <div className="border border-line">
                {suite.domains.map((domain) => (
                  <DomainDrawer
                    available={domain.name === "context-appetite"}
                    defaultOpen={domain.name === "context-appetite"}
                    domain={domain}
                    key={domain.name}
                    live={suite.slug === "instinct-bench-live"}
                  />
                ))}
              </div>
            </section>
          </Reveal>
        ))}

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
