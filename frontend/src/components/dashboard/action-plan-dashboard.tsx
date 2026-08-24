import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ClipboardList,
  Clock3,
  FileCheck2,
  Gauge,
  Globe2,
  Layers3,
  Target,
} from "lucide-react";

import DashboardShell from "@/components/dashboard/dashboard-shell";

import type {
  ActionPlanSummary,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  visibilitySummary: VisibilitySummary;
  plan: ActionPlanSummary;
};


function pretty(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


function priorityClass(
  priority: string,
) {
  if (priority === "high") {
    return "bg-red-500/10 text-red-300";
  }

  if (priority === "medium") {
    return "bg-amber-500/10 text-amber-300";
  }

  return "bg-slate-800 text-slate-300";
}


function StatCard({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: typeof Gauge;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">
          {label}
        </span>

        <div className="rounded-xl bg-slate-800 p-2.5">
          <Icon className="h-4 w-4 text-cyan-400" />
        </div>
      </div>

      <div className="mt-5 text-3xl font-semibold text-white">
        {value}
      </div>

      <div className="mt-2 text-xs text-slate-500">
        {detail}
      </div>
    </div>
  );
}


export default function ActionPlanDashboard({
  visibilitySummary,
  plan,
}: Props) {
  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Action Plan"
    >
      <div className="mx-auto max-w-7xl space-y-6 p-5 lg:p-8">
        <section>
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <div className="text-sm text-slate-500">
                Consolidated GEO strategy
              </div>

              <h2 className="mt-1 text-xl font-semibold text-white">
                {plan.target_brand}
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Plan #{plan.plan_id} ·{" "}
                {plan.experiment_name} ·{" "}
                {plan.benchmark_mode}
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-300">
              Stored plan status:{" "}
              <span className="font-medium text-emerald-300">
                {plan.plan_status}
              </span>
            </div>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Actions"
              value={`${plan.total_actions}`}
              detail="Consolidated strategy actions"
              icon={ClipboardList}
            />

            <StatCard
              label="High Priority"
              value={`${plan.high_priority_actions}`}
              detail="Highest-priority stored actions"
              icon={AlertTriangle}
            />

            <StatCard
              label="Stored Open"
              value={`${plan.open_actions}`}
              detail="Status recorded in action plan"
              icon={Clock3}
            />

            <StatCard
              label="Source Mode"
              value={pretty(
                plan.benchmark_mode,
              )}
              detail={plan.experiment_name}
              icon={
                plan.benchmark_mode ===
                "web_search"
                  ? Globe2
                  : Bot
              }
            />
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.5fr_0.8fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="font-semibold text-white">
              Strategy Summary
            </h2>

            <p className="mt-4 text-sm leading-7 text-slate-300">
              {plan.strategy_summary}
            </p>
          </div>

          <div className="rounded-2xl border border-cyan-500/15 bg-cyan-500/5 p-6">
            <div className="text-sm text-slate-500">
              Current Web Signal
            </div>

            <div className="mt-3 text-2xl font-semibold capitalize text-white">
              {
                visibilitySummary
                  .diagnosis
                  .primary_bottleneck
              }{" "}
              bottleneck
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="text-xs text-slate-500">
                  Web visibility
                </div>

                <div className="mt-2 text-lg font-semibold text-white">
                  {visibilitySummary.target
                    .web_visibility_score
                    ?.toFixed(2) ??
                    "N/A"}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="text-xs text-slate-500">
                  Cited coverage
                </div>

                <div className="mt-2 text-lg font-semibold text-white">
                  {visibilitySummary.target
                    .cited_response_coverage
                    ?.toFixed(2) ??
                    "N/A"}
                  %
                </div>
              </div>
            </div>

            <p className="mt-4 text-xs leading-5 text-slate-500">
              Current Web Baseline data is shown
              separately and is not directly compared
              with the historical planning snapshot.
            </p>
          </div>
        </section>

        <section className="rounded-2xl border border-amber-500/15 bg-amber-500/5 p-5">
          <div className="flex gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />

            <div>
              <div className="font-medium text-amber-200">
                Historical plan provenance
              </div>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                {plan.provenance_note}
              </p>
            </div>
          </div>
        </section>

        <section>
          <div className="mb-4">
            <h2 className="font-semibold text-white">
              Priority Actions
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Expand each action to inspect
              implementation, evidence and success
              metrics.
            </p>
          </div>

          <div className="space-y-4">
            {plan.actions.map(
              (action) => (
                <details
                  key={action.id}
                  className="group rounded-2xl border border-slate-800 bg-slate-900/60"
                >
                  <summary className="cursor-pointer list-none p-5 lg:p-6">
                    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
                      <div className="flex min-w-0 gap-4">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-800 text-sm font-semibold text-cyan-300">
                          {action.sort_order}
                        </div>

                        <div className="min-w-0">
                          <h3 className="font-medium text-white">
                            {action.title}
                          </h3>

                          <div className="mt-2 flex flex-wrap gap-2">
                            <span
                              className={[
                                "rounded-lg px-2.5 py-1 text-xs font-medium",
                                priorityClass(
                                  action.priority,
                                ),
                              ].join(" ")}
                            >
                              {action.priority}
                            </span>

                            <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-300">
                              {pretty(
                                action.action_type,
                              )}
                            </span>

                            <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                              Effort:{" "}
                              {action.effort}
                            </span>

                            <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                              Stored status:{" "}
                              {action.status}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="text-xs text-slate-500">
                        {
                          action.impacted_prompt_ids
                            .length
                        }{" "}
                        prompts
                      </div>
                    </div>
                  </summary>

                  <div className="border-t border-slate-800 px-5 pb-6 pt-5 lg:px-6">
                    <div className="grid gap-6 xl:grid-cols-2">
                      <div>
                        <div className="text-xs uppercase tracking-wider text-slate-500">
                          Rationale
                        </div>

                        <p className="mt-3 text-sm leading-6 text-slate-300">
                          {action.rationale}
                        </p>

                        {action.target_page && (
                          <div className="mt-5">
                            <div className="text-xs uppercase tracking-wider text-slate-500">
                              Target page
                            </div>

                            <div className="mt-2 text-sm text-cyan-300">
                              {action.target_page}
                            </div>
                          </div>
                        )}
                      </div>

                      <div>
                        <div className="text-xs uppercase tracking-wider text-slate-500">
                          Implementation
                        </div>

                        <ol className="mt-3 space-y-2">
                          {action.implementation_steps.map(
                            (
                              step,
                              index,
                            ) => (
                              <li
                                key={`${action.id}-step-${index}`}
                                className="flex gap-3 text-sm leading-6 text-slate-300"
                              >
                                <span className="text-cyan-500">
                                  {index + 1}.
                                </span>

                                <span>
                                  {step}
                                </span>
                              </li>
                            ),
                          )}
                        </ol>
                      </div>
                    </div>

                    <div className="mt-6 grid gap-5 lg:grid-cols-3">
                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="flex items-center gap-2 text-sm font-medium text-white">
                          <FileCheck2 className="h-4 w-4 text-cyan-400" />
                          Evidence
                        </div>

                        <ul className="mt-3 space-y-2">
                          {action.evidence.map(
                            (
                              item,
                              index,
                            ) => (
                              <li
                                key={`${action.id}-evidence-${index}`}
                                className="text-xs leading-5 text-slate-400"
                              >
                                • {item}
                              </li>
                            ),
                          )}
                        </ul>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="flex items-center gap-2 text-sm font-medium text-white">
                          <Target className="h-4 w-4 text-emerald-400" />
                          Success Metrics
                        </div>

                        <ul className="mt-3 space-y-2">
                          {action.success_metrics.map(
                            (
                              item,
                              index,
                            ) => (
                              <li
                                key={`${action.id}-metric-${index}`}
                                className="text-xs leading-5 text-slate-400"
                              >
                                • {item}
                              </li>
                            ),
                          )}
                        </ul>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="flex items-center gap-2 text-sm font-medium text-white">
                          <Layers3 className="h-4 w-4 text-violet-400" />
                          Dependencies
                        </div>

                        {action.dependencies.length >
                        0 ? (
                          <ul className="mt-3 space-y-2">
                            {action.dependencies.map(
                              (
                                item,
                                index,
                              ) => (
                                <li
                                  key={`${action.id}-dependency-${index}`}
                                  className="text-xs leading-5 text-slate-400"
                                >
                                  • {item}
                                </li>
                              ),
                            )}
                          </ul>
                        ) : (
                          <div className="mt-3 text-xs text-slate-600">
                            No stored dependencies.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </details>
              ),
            )}
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="font-semibold text-white">
              Recommended Sequence
            </h2>

            <ol className="mt-5 space-y-3">
              {plan.recommended_sequence.map(
                (
                  item,
                  index,
                ) => (
                  <li
                    key={index}
                    className="flex gap-3 text-sm leading-6 text-slate-300"
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 text-xs text-cyan-300">
                      {index + 1}
                    </span>

                    {item}
                  </li>
                ),
              )}
            </ol>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="font-semibold text-white">
              Risks & Limits
            </h2>

            <div className="mt-5 space-y-3">
              {plan.risks_and_limits.map(
                (
                  item,
                  index,
                ) => (
                  <div
                    key={index}
                    className="flex gap-3 rounded-xl border border-slate-800 bg-slate-950/50 p-3"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />

                    <p className="text-xs leading-5 text-slate-400">
                      {item}
                    </p>
                  </div>
                ),
              )}
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <StatCard
            label="Stored Plan Baseline Runs"
            value={String(
              plan.baseline_metrics[
                "analyzed_runs"
              ] ?? "N/A",
            )}
            detail="Frozen when the plan was generated"
            icon={Gauge}
          />

          <StatCard
            label="Resolved Plan Actions"
            value={`${plan.completed_actions}`}
            detail="Based only on stored item status"
            icon={CheckCircle2}
          />

          <StatCard
            label="Action Types"
            value={`${Object.keys(
              plan.action_type_counts,
            ).length}`}
            detail="Distinct optimization categories"
            icon={Layers3}
          />
        </section>
      </div>
    </DashboardShell>
  );
}
