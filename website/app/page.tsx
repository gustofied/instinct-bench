import { ArrowUpRight } from "lucide-react";

import { DomainDrawer } from "@/components/domain-drawer";
import { Reveal } from "@/components/reveal";
import { benchmark, benchmarkSummary } from "@/lib/benchmark";
import { cn } from "@/lib/utils";

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
          <header className="grid min-h-[58px] grid-cols-1 items-center gap-1.5 border-b border-line py-3 md:grid-cols-[1fr_auto_1fr] md:gap-0 md:py-2">
            <a
              className="flex items-center justify-center gap-2.5 md:justify-start"
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
              <span className="shrink-0 font-mono text-[10px] font-semibold uppercase">
                instinct-bench
              </span>
            </a>

            <nav
              className="flex items-center justify-center gap-4 text-[12px] md:gap-6"
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

            <span className="justify-self-center font-mono text-[9px] text-muted uppercase md:justify-self-end">
              mock data / v{benchmark.version}
            </span>
          </header>
        </Reveal>

        <Reveal delay={0.04}>
          <section aria-labelledby="page-title">
            <div className="grid min-h-0 grid-cols-1 items-center gap-6 py-7 md:min-h-[262px] md:grid-cols-[minmax(0,2fr)_minmax(240px,0.75fr)] md:gap-14 md:py-8">
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
                <p className="font-serif text-[17px] leading-[1.5] text-copy">
                  Testing the capacities that make agents useful: taste,
                  restraint, context judgment, craft, and control.
                </p>
                <a
                  aria-label="Made by gustofied"
                  className="group mt-5 inline-flex items-center border-t border-line pt-3"
                  href="https://x.com/gustofied"
                  rel="noreferrer"
                  target="_blank"
                >
                  <span className="font-signature text-[18px] leading-none text-marker group-hover:underline">
                    made by @gustofied
                  </span>
                </a>
              </div>
            </div>

            <div className="grid grid-cols-2 border-y border-line sm:grid-cols-4">
              {[
                {
                  label: "domains",
                  value: benchmarkSummary.domainCount.toString().padStart(2, "0"),
                },
                {
                  label: "tasks",
                  value: benchmarkSummary.taskCount.toString().padStart(2, "0"),
                },
                {
                  label: "avg score",
                  value: benchmarkSummary.averageScore?.toFixed(2) ?? "—",
                },
                {
                  label: "best model",
                  value: benchmarkSummary.bestRun?.model ?? "—",
                  score: benchmarkSummary.bestRun?.reward.toFixed(2),
                },
              ].map(({ label, score, value }, index) => (
                <div
                  className={cn(
                    "flex min-h-14 items-center justify-between gap-4 px-4",
                    index > 0 && "border-l border-line",
                    index === 2 && "border-t border-l-0 sm:border-t-0 sm:border-l",
                    index === 3 && "border-t sm:border-t-0",
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
