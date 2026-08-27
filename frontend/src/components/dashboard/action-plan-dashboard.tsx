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
import SiteRAGActionPlanPanel from "@/components/dashboard/site-rag-action-plan-panel";

import type {
  ActionPlanSummary,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  visibilitySummary: VisibilitySummary;
  webVisibilitySummary: VisibilitySummary | null;
  plan: ActionPlanSummary | null;
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
    return "border border-red-200 bg-red-50 text-red-700";
  }

  if (priority === "medium") {
    return "border border-amber-200 bg-amber-50 text-amber-700";
  }

  return "border border-slate-200 bg-slate-50 text-slate-600";
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
    <div className="crystal-card rounded-[20px] p-5">
      <div className="flex items-start justify-between gap-4">
        <span className="crystal-eyebrow">
          {label}
        </span>

        <div className="crystal-icon h-10 w-10">
          <Icon className="h-[18px] w-[18px] text-[#5f75ff]" />
        </div>
      </div>

      <div className="crystal-value mt-5 text-3xl font-medium">
        {value}
      </div>

      <div className="mt-3 text-xs leading-5 text-slate-500">
        {detail}
      </div>
    </div>
  );
}


export default function ActionPlanDashboard({
  visibilitySummary,
  webVisibilitySummary,
  plan,
}: Props) {
  if (!plan) {
    return (
      <DashboardShell
        summary={visibilitySummary}
        title="Action Plan"
      >
        <div className="crystal-page mx-auto max-w-[1450px] p-5 lg:p-8 xl:px-10">
          <section className="crystal-panel rounded-[22px] p-8">
            <div className="flex min-h-[340px] items-center justify-center text-center">
              <div className="max-w-xl">
                <div className="crystal-icon mx-auto h-12 w-12">
                  <ClipboardList className="h-5 w-5 text-[#5f75ff]" />
                </div>

                <div className="crystal-eyebrow mt-5">
                  Consolidated GEO strategy
                </div>

                <h2 className="mt-3 text-2xl font-medium tracking-[-0.035em] text-slate-950">
                  No stored action plan yet
                </h2>

                <p className="mt-3 text-sm leading-7 text-slate-500">
                  This project does not yet have a persisted
                  GEO action plan. Complete the compatible
                  opportunity and diagnosis workflow before
                  generating a historical strategy plan.
                </p>

                <p className="mt-3 text-xs leading-5 text-slate-400">
                  Missing plan data is an empty state, not an
                  application error.
                </p>
              </div>
            </div>
          </section>
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Action Plan"
    >
      <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
        <section>
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <div className="crystal-eyebrow">
                Consolidated GEO strategy
              </div>

              <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
                {plan.target_brand}
              </h2>

              <p className="mt-1.5 text-sm text-slate-500">
                Plan #{plan.plan_id} ·{" "}
                {plan.experiment_name} ·{" "}
                {plan.benchmark_mode}
              </p>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-slate-600">
              Stored plan status
              <span className="font-medium text-emerald-700">
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
          <div className="crystal-panel rounded-[22px] p-6">
            <h2 className="font-semibold text-slate-950">
              Strategy Summary
            </h2>

            <p className="mt-4 text-sm leading-7 text-slate-700">
              {plan.strategy_summary}
            </p>
          </div>

          <div className="rounded-[22px] border border-violet-200/70 bg-gradient-to-br from-violet-50/70 via-white to-blue-50/70 p-6 shadow-[0_14px_40px_rgba(79,70,229,0.045)]">
            <div className="crystal-eyebrow">
              Current Web Signal
            </div>

            <div className="mt-3 text-2xl font-semibold capitalize text-slate-950">
              {
                webVisibilitySummary
                  ?.diagnosis
                  .primary_bottleneck
                  ?? "unavailable"
              }{" "}
              bottleneck
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="crystal-subcard rounded-2xl p-4">
                <div className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-500">
                  Web visibility
                </div>

                <div className="crystal-value mt-2 text-xl font-medium">
                  {webVisibilitySummary?.target
                    .web_visibility_score
                    ?.toFixed(2) ??
                    "N/A"}
                </div>
              </div>

              <div className="crystal-subcard rounded-2xl p-4">
                <div className="text-xs text-slate-500">
                  Cited coverage
                </div>

                <div className="crystal-value mt-2 text-xl font-medium">
                  {webVisibilitySummary?.target
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

        <section className="rounded-[22px] border border-amber-200 bg-amber-50/65 p-5">
          <div className="flex gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

            <div>
              <div className="font-medium text-amber-800">
                Historical plan provenance
              </div>

              <p className="mt-2 text-sm leading-7 text-slate-600">
                {plan.provenance_note}
              </p>
            </div>
          </div>
        </section>

        <SiteRAGActionPlanPanel
          data={plan.site_rag}
        />

        <section>
          <div className="mb-4">
            <div className="crystal-eyebrow">
              Execution priorities
            </div>

            <h2 className="mt-2 text-xl font-medium tracking-[-0.025em] text-slate-950">
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
                  className="group crystal-card overflow-hidden rounded-[22px]"
                >
                  <summary className="cursor-pointer list-none p-5 lg:p-6">
                    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
                      <div className="flex min-w-0 gap-4">
                        <div className="crystal-step-badge">
                          {action.sort_order}
                        </div>

                        <div className="min-w-0">
                          <h3 className="text-[15px] font-medium leading-6 text-slate-950">
                            {action.title}
                          </h3>

                          <div className="mt-2 flex flex-wrap gap-2">
                            <span
                              className={[
                                "rounded-full px-2.5 py-1 text-xs font-medium",
                                priorityClass(
                                  action.priority,
                                ),
                              ].join(" ")}
                            >
                              {action.priority}
                            </span>

                            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-700">
                              {pretty(
                                action.action_type,
                              )}
                            </span>

                            <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-500">
                              Effort:{" "}
                              {action.effort}
                            </span>

                            <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-500">
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

                  <div className="border-t border-slate-200/70 bg-slate-50/25 px-5 pb-6 pt-5 lg:px-6">
                    <div className="grid gap-6 xl:grid-cols-2">
                      <div>
                        <div className="crystal-eyebrow">
                          Rationale
                        </div>

                        <p className="mt-3 text-sm leading-6 text-slate-700">
                          {action.rationale}
                        </p>

                        {action.target_page && (
                          <div className="mt-5">
                            <div className="crystal-eyebrow">
                              Target page
                            </div>

                            <div className="mt-2 text-sm font-medium text-violet-600">
                              {action.target_page}
                            </div>
                          </div>
                        )}
                      </div>

                      <div>
                        <div className="crystal-eyebrow">
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
                                className="flex gap-3 text-sm leading-6 text-slate-700"
                              >
                                <span className="font-medium text-violet-600">
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
                      <div className="crystal-subcard rounded-[18px] p-4">
                        <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                          <FileCheck2 className="h-4 w-4 text-[#5f75ff]" />
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
                                className="text-xs leading-5 text-slate-600"
                              >
                                • {item}
                              </li>
                            ),
                          )}
                        </ul>
                      </div>

                      <div className="crystal-subcard rounded-[18px] p-4">
                        <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                          <Target className="h-4 w-4 text-emerald-600" />
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
                                className="text-xs leading-5 text-slate-600"
                              >
                                • {item}
                              </li>
                            ),
                          )}
                        </ul>
                      </div>

                      <div className="crystal-subcard rounded-[18px] p-4">
                        <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                          <Layers3 className="h-4 w-4 text-violet-600" />
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
                                  className="text-xs leading-5 text-slate-600"
                                >
                                  • {item}
                                </li>
                              ),
                            )}
                          </ul>
                        ) : (
                          <div className="mt-3 text-xs text-slate-500">
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
          <div className="crystal-panel rounded-[22px] p-6">
            <div className="crystal-eyebrow">
              Execution roadmap
            </div>

            <h2 className="mt-2 text-xl font-medium tracking-[-0.025em] text-slate-950">
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
                    className="flex gap-3 text-sm leading-6 text-slate-700"
                  >
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl border border-violet-200 bg-violet-50 text-xs font-medium text-violet-700">
                      {index + 1}
                    </span>

                    {item}
                  </li>
                ),
              )}
            </ol>
          </div>

          <div className="crystal-panel rounded-[22px] p-6">
            <div className="crystal-eyebrow">
              Guardrails
            </div>

            <h2 className="mt-2 text-xl font-medium tracking-[-0.025em] text-slate-950">
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
                    className="crystal-subcard flex gap-3 rounded-[16px] p-3.5"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />

                    <p className="text-xs leading-5 text-slate-600">
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
