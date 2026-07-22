"use client";

import { Minus, Plus } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useState } from "react";

import type { BenchmarkDomain } from "@/lib/benchmark";
import { cn } from "@/lib/utils";

type TrajectoryResult = BenchmarkDomain["trajectories"][number]["result"];

function Status({ value }: { value: TrajectoryResult }) {
  const color =
    value === "pass"
      ? "bg-ink"
      : value === "review"
        ? "bg-registration-yellow"
        : value === "fail" || value === "shaping"
          ? "bg-marker"
          : "border border-marker bg-transparent";

  return (
    <span className="inline-flex items-center gap-2 font-mono text-[9px] uppercase">
      <span className={cn("size-1.5 shrink-0", color)} aria-hidden="true" />
      {value}
    </span>
  );
}

function PanelHeading({ count, title }: { count: number; title: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-line pb-2">
      <h3 className="font-mono text-[9px] font-medium uppercase">{title}</h3>
      <span className="font-mono text-[9px] text-muted">
        {count.toString().padStart(2, "0")}
      </span>
    </div>
  );
}

export function DomainDrawer({
  defaultOpen = false,
  domain,
  live = false,
}: {
  defaultOpen?: boolean;
  domain: BenchmarkDomain;
  live?: boolean;
}) {
  const available = domain.availability === "available";
  const [open, setOpen] = useState(defaultOpen && available);
  const reduceMotion = useReducedMotion();
  const panelId = `domain-${domain.slug}-panel`;
  const triggerId = `domain-${domain.slug}-trigger`;
  const taskCount = domain.taskSets.reduce((total, taskSet) => total + taskSet.tasks, 0);
  const scores = domain.trajectories.map((trajectory) => trajectory.reward);
  const score = live
    ? domain.trajectories[0]?.reward
    : scores.length
      ? Math.max(...scores)
      : undefined;

  if (!available) {
    return (
      <article className="border-b border-line last:border-b-0">
        <div className="grid min-h-[72px] grid-cols-1 items-center gap-2 px-4 py-3 md:grid-cols-[minmax(160px,0.82fr)_minmax(240px,1.4fr)_230px_28px] md:gap-4">
          <strong className="min-w-0 font-mono text-[12px] font-medium text-copy">
            {domain.name}
          </strong>
          <span className="text-[13px] text-muted">{domain.judgment}</span>
          <span className="justify-self-start font-mono text-[9px] text-muted uppercase md:col-span-2 md:justify-self-end">
            coming later
          </span>
        </div>
      </article>
    );
  }

  return (
    <article className="border-b border-line last:border-b-0">
      <button
        aria-controls={panelId}
        aria-expanded={open}
        aria-label={`${open ? "Collapse" : "Expand"} ${domain.name}`}
        className="group grid min-h-[72px] w-full cursor-pointer grid-cols-[minmax(0,1fr)_28px] items-center gap-x-4 gap-y-2 bg-transparent px-4 py-3 text-left hover:bg-faint md:grid-cols-[minmax(160px,0.82fr)_minmax(240px,1.4fr)_230px_28px] md:gap-4"
        id={triggerId}
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        <strong className="min-w-0 font-mono text-[12px] font-medium">
          {domain.name}
        </strong>
        <span className="col-span-2 row-start-2 text-[13px] text-copy md:col-span-1 md:row-auto">
          {domain.judgment}
        </span>
        <span className="col-span-2 row-start-3 flex items-center justify-start gap-4 md:col-span-1 md:row-auto md:justify-between">
          <span className="font-mono text-[10px] text-copy">
            {domain.taskSets.length.toString().padStart(2, "0")} {domain.taskSets.length === 1 ? "set" : "sets"}
          </span>
          <span className="font-mono text-[10px] text-copy">
            {taskCount.toString().padStart(2, "0")} tasks
          </span>
          {score !== undefined ? (
            <span className="font-mono text-[10px] text-copy">
              {score.toFixed(2)} {live ? "latest" : "best"}
            </span>
          ) : null}
        </span>
        <span className="col-start-2 row-start-1 grid size-7 place-items-center border border-line text-muted transition-colors group-hover:border-ink group-hover:text-ink md:col-auto md:row-auto">
          {open ? (
            <Minus aria-hidden="true" size={13} strokeWidth={1.5} />
          ) : (
            <Plus aria-hidden="true" size={13} strokeWidth={1.5} />
          )}
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            animate={{ height: "auto", opacity: 1 }}
            className="overflow-hidden"
            exit={{ height: 0, opacity: 0 }}
            id={panelId}
            initial={{ height: 0, opacity: 0 }}
            role="region"
            aria-labelledby={triggerId}
            transition={
              reduceMotion
                ? { duration: 0 }
                : { duration: 0.18, ease: "easeOut" }
            }
          >
            <div className="grid grid-cols-1 border-t border-line bg-faint md:grid-cols-3">
              <section className="min-w-0 border-b border-line p-4 md:border-b-0">
                <PanelHeading count={domain.taskSets.length} title="Task sets" />
                <div className="divide-y divide-line">
                  {domain.taskSets.map((taskSet) => (
                    <div className="grid gap-1.5 py-3" key={taskSet.name}>
                      <div className="flex items-start justify-between gap-4">
                        <strong className="font-mono text-[11px] font-medium">
                          {taskSet.name}
                        </strong>
                        <span className="shrink-0 font-mono text-[9px] text-muted">
                          {taskSet.tasks.toString().padStart(2, "0")} tasks
                        </span>
                      </div>
                      <span className="text-[12px] text-copy">{taskSet.material}</span>
                      <span className="font-mono text-[9px] text-muted uppercase">
                        {taskSet.verifier}
                      </span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="min-w-0 border-b border-line p-4 md:border-b-0 md:border-l">
                <PanelHeading count={domain.trajectories.length} title="Trajectories" />
                <div className="divide-y divide-line">
                  {domain.trajectories.map((trajectory) => (
                    <div className="grid gap-1.5 py-3" key={trajectory.id}>
                      <div className="flex items-start justify-between gap-4">
                        <strong className="font-mono text-[11px] font-medium">
                          {trajectory.id}
                        </strong>
                        <Status value={trajectory.result} />
                      </div>
                      <span className="text-[12px] text-copy">
                        {trajectory.model} / {trajectory.harness}
                      </span>
                      <span className="font-mono text-[9px] text-muted uppercase">
                        {trajectory.reward.toFixed(2)} reward / {trajectory.steps} steps / {trajectory.cost}
                      </span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="min-w-0 p-4 md:border-l">
                <PanelHeading count={domain.artifacts.length} title="Artifacts" />
                <div className="divide-y divide-line">
                  {domain.artifacts.map((artifact) => (
                    <div
                      className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 py-2.5"
                      key={`${artifact.source}-${artifact.name}`}
                    >
                      <strong className="min-w-0 [overflow-wrap:anywhere] font-mono text-[10px] font-medium">
                        {artifact.name}
                      </strong>
                      <span className="font-mono text-[9px] text-muted">{artifact.size}</span>
                      <span className="col-span-2 text-[11px] text-copy">{artifact.role}</span>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </article>
  );
}
