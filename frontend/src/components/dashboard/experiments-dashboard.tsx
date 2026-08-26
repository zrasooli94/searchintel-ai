"use client";

import {
  Activity,
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock3,
  FlaskConical,
  Gauge,
  Globe2,
  Layers3,
  TriangleAlert,
} from "lucide-react";

import DashboardShell from "@/components/dashboard/dashboard-shell";
import RetrievalMonitoringPanel from "@/components/dashboard/retrieval-monitoring-panel";

import type {
  ExperimentComparison,
  ExperimentMetricValue,
  ExperimentsSummary,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  projectId: number;
  visibilitySummary: VisibilitySummary;
  experiments: ExperimentsSummary;
  comparison: ExperimentComparison | null;
};


function percent(
  value: number | null,
) {
  if (value === null) {
    return "N/A";
  }

  return `${value.toFixed(2)}%`;
}


function metricValue(
  value: number | null,
) {
  if (value === null) {
    return "N/A";
  }

  return value.toFixed(2);
}


function deltaText(
  value: number | null,
) {
  if (value === null) {
    return "—";
  }

  if (value > 0) {
    return `+${value.toFixed(2)}`;
  }

  return value.toFixed(2);
}


function deltaClass(
  value: number | null,
) {
  if (value === null) {
    return "text-slate-500";
  }

  if (value > 0) {
    return "text-emerald-600";
  }

  if (value < 0) {
    return "text-red-600";
  }

  return "text-slate-500";
}


function MetricCard({
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


function ComparisonRow({
  label,
  metric,
  percentValues = true,
  neutralDelta = false,
}: {
  label: string;
  metric: ExperimentMetricValue;
  percentValues?: boolean;
  neutralDelta?: boolean;
}) {
  const render = (
    value: number | null,
  ) =>
    percentValues
      ? percent(value)
      : metricValue(value);

  return (
    <div className="grid grid-cols-[1.4fr_1fr_1fr_0.8fr] items-center gap-4 border-b border-slate-200/65 px-5 py-4 transition hover:bg-slate-50/50 last:border-0">
      <div className="text-sm text-slate-700">
        {label}
      </div>

      <div className="text-sm text-slate-400">
        {render(metric.baseline)}
      </div>

      <div className="text-sm text-slate-800">
        {render(metric.comparison)}
      </div>

      <div
        className={[
          "text-sm font-medium",
          neutralDelta
            ? "text-slate-400"
            : deltaClass(
                metric.delta,
              ),
        ].join(" ")}
      >
        {deltaText(metric.delta)}
      </div>
    </div>
  );
}


export default function ExperimentsDashboard({
  projectId,
  visibilitySummary,
  experiments,
  comparison,
}: Props) {
  const comparisonBaseline =
    comparison
      ? experiments.experiments.find(
          (item) =>
            item.id
            === comparison.baseline_experiment_id
        )
      : null;

  const comparisonExperiment =
    comparison
      ? experiments.experiments.find(
          (item) =>
            item.id
            === comparison.comparison_experiment_id
        )
      : null;

  const comparisonAnalysisCurrent =
    comparison !== null
    && comparisonBaseline?.analysis_is_current
    === true
    && comparisonExperiment?.analysis_is_current
    === true;

  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Experiments"
    >
      <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
        <section>
          <div>
            <div className="crystal-eyebrow">
              Controlled measurement
            </div>

            <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
              GEO Experiments
            </h2>

            <p className="mt-1.5 text-sm text-slate-500">
              Compare like-for-like measurement modes
              and track optimization changes.
            </p>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <MetricCard
              label="Total Experiments"
              value={`${experiments.total_experiments}`}
              detail="Stored GEO experiments"
              icon={FlaskConical}
            />

            <MetricCard
              label="Completed"
              value={`${experiments.completed_experiments}`}
              detail="Frozen measurement sets"
              icon={CheckCircle2}
            />

            <MetricCard
              label="Draft"
              value={`${experiments.draft_experiments}`}
              detail="Not formally completed"
              icon={Clock3}
            />
          </div>
        </section>

        <section>
          <div className="mb-4">
            <h2 className="font-semibold text-slate-950">
              Experiment Registry
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Memory and live-web experiments remain
              separate measurement modes.
            </p>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            {experiments.experiments.map(
              (experiment) => {
                const web =
                  experiment.benchmark_mode ===
                  "web_search";

                return (
                  <div
                    key={experiment.id}
                    className="crystal-card rounded-[22px] p-5 lg:p-6"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="crystal-eyebrow">
                          {experiment.phase}
                        </div>

                        <h3 className="mt-2 text-xl font-medium tracking-[-0.025em] text-slate-950">
                          {experiment.name}
                        </h3>
                      </div>

                      <span
                        className={[
                          "rounded-lg px-2.5 py-1 text-xs font-medium",
                          experiment.status ===
                          "completed"
                            ? "bg-emerald-500/10 text-emerald-300"
                            : "bg-amber-500/10 text-amber-300",
                        ].join(" ")}
                      >
                        {experiment.status}
                      </span>
                    </div>

                    <div className="mt-5 flex items-center gap-2">
                      <div
                        className={[
                          "flex items-center gap-2 rounded-lg px-2.5 py-1 text-xs",
                          web
                            ? "bg-cyan-500/10 text-cyan-300"
                            : "bg-violet-500/10 text-violet-300",
                        ].join(" ")}
                      >
                        {web ? (
                          <Globe2 className="h-3.5 w-3.5" />
                        ) : (
                          <Bot className="h-3.5 w-3.5" />
                        )}

                        {experiment.benchmark_mode}
                      </div>
                    </div>

                    <div className="mt-6 grid grid-cols-2 gap-3">
                      <div className="crystal-subcard rounded-2xl p-3.5">
                        <div className="text-xs text-slate-500">
                          Runs
                        </div>

                        <div className="mt-1 text-lg font-semibold text-slate-950">
                          {experiment.runs}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-3.5">
                        <div className="text-xs text-slate-500">
                          Prompts
                        </div>

                        <div className="mt-1 text-lg font-semibold text-slate-950">
                          {experiment.prompts}
                        </div>
                      </div>
                    </div>

                    {!experiment.analysis_is_current && (
                      <div className="mt-5 flex gap-2 rounded-2xl border border-amber-200 bg-amber-50/75 p-3.5 text-xs leading-5 text-amber-800">
                        <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />

                        <div>
                          <div className="font-medium">
                            Analysis update recommended
                          </div>

                          <div className="mt-1 text-amber-700/75">
                            {experiment.analysis_stale_responses}
                            {" of "}
                            {experiment.analysis_total_responses}
                            {" analyzed responses use legacy or unknown analysis."}
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="mt-5 space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">
                          Response coverage
                        </span>

                        <span className="text-slate-800">
                          {percent(
                            experiment
                              .target_response_coverage,
                          )}
                        </span>
                      </div>

                      {web ? (
                        <>
                          <div className="flex justify-between">
                            <span className="text-slate-500">
                              Web visibility
                            </span>

                            <span className="text-slate-800">
                              {metricValue(
                                experiment
                                  .web_visibility_score_v1,
                              )}
                            </span>
                          </div>

                          <div className="flex justify-between">
                            <span className="text-slate-500">
                              Verified coverage
                            </span>

                            <span className="text-slate-800">
                              {percent(
                                experiment
                                  .entity_verified_target_mention_rate,
                              )}
                            </span>
                          </div>

                          <div className="flex justify-between">
                            <span className="text-slate-500">
                              Retrieved coverage
                            </span>

                            <span className="text-slate-800">
                              {percent(
                                experiment
                                  .grounded_target_mention_rate,
                              )}
                            </span>
                          </div>

                          <div className="flex justify-between">
                            <span className="text-slate-500">
                              Cited coverage
                            </span>

                            <span className="text-slate-800">
                              {percent(
                                experiment
                                  .target_cited_response_coverage,
                              )}
                            </span>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="flex justify-between">
                            <span className="text-slate-500">
                              Visibility score V1
                            </span>

                            <span className="text-slate-800">
                              {
                                experiment
                                  .visibility_score_v1
                              }
                            </span>
                          </div>

                          <div className="flex justify-between">
                            <span className="text-slate-500">
                              Mention rate
                            </span>

                            <span className="text-slate-800">
                              {percent(
                                experiment.mention_rate,
                              )}
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                );
              },
            )}
          </div>
        </section>

        <RetrievalMonitoringPanel
          projectId={projectId}
          experiments={experiments}
        />

        {comparison && (
          <section className="crystal-panel rounded-[22px]">
            <div className="p-5 pb-4 lg:p-6 lg:pb-4">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <h2 className="font-semibold text-slate-950">
                    Same-Mode Comparison
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Direct comparison is allowed only
                    when benchmark modes match.
                  </p>
                </div>

                <div className="flex items-center gap-3 text-sm">
                  <span className="rounded-lg bg-slate-100 px-3 py-1.5 text-slate-700">
                    {comparison.baseline_name}
                  </span>

                  <ArrowRight className="h-4 w-4 text-slate-400" />

                  <span className="rounded-lg bg-slate-100 px-3 py-1.5 text-slate-700">
                    {comparison.comparison_name}
                  </span>
                </div>
              </div>
            </div>

            {!comparisonAnalysisCurrent && (
              <div className="mx-5 mt-2 flex gap-2 rounded-2xl border border-amber-200 bg-amber-50/75 p-4 text-sm text-amber-800 lg:mx-6">
                <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />

                <div>
                  <div className="font-medium">
                    Analysis generations differ or are stale
                  </div>

                  <div className="mt-1 text-xs leading-5 text-amber-700/75">
                    Re-analyze legacy responses before treating this comparison as analysis-generation consistent.
                  </div>
                </div>
              </div>
            )}

            <div className="mt-5 grid grid-cols-[1.4fr_1fr_1fr_0.8fr] gap-4 border-y border-slate-200/70 bg-slate-50/55 px-5 py-3 text-[11px] uppercase tracking-[0.1em] text-slate-500">
              <div>
                Metric
              </div>

              <div>
                Baseline
              </div>

              <div>
                Comparison
              </div>

              <div>
                Delta
              </div>
            </div>

            <ComparisonRow
              label="Raw Mention Rate"
              metric={comparison.mention_rate}
            />

            <ComparisonRow
              label="Raw Prompt Coverage"
              metric={comparison.prompt_coverage}
            />

            <ComparisonRow
              label="Verified Mention Rate"
              metric={
                comparison
                  .entity_verified_target_mention_rate
              }
            />

            <ComparisonRow
              label="Verified Prompt Coverage"
              metric={
                comparison
                  .entity_verified_target_prompt_coverage
              }
            />

            <ComparisonRow
              label="Citation Rate"
              metric={comparison.citation_rate}
            />

            <ComparisonRow
              label="Raw Mention SOV"
              metric={
                comparison
                  .target_share_of_voice
              }
              neutralDelta
            />

            <ComparisonRow
              label="Verified Mention SOV"
              metric={
                comparison
                  .entity_verified_target_share_of_voice
              }
            />

            <ComparisonRow
              label="Visibility Score V1"
              metric={
                comparison
                  .visibility_score_v1
              }
              percentValues={false}
            />

            <ComparisonRow
              label="Average Mention Position"
              metric={
                comparison
                  .average_mention_position
              }
              percentValues={false}
            />
          </section>
        )}

        <section className="grid gap-6 xl:grid-cols-[1fr_1.5fr]">
          <div className="crystal-panel rounded-[22px] p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-slate-950">
                  Measurement Modes
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Do not compare unlike experiment modes.
                </p>
              </div>

              <Layers3 className="h-5 w-5 text-slate-400" />
            </div>

            <div className="mt-6 space-y-4">
              <div className="crystal-subcard rounded-[18px] border-violet-200/80 bg-violet-50/55 p-4">
                <div className="flex items-center gap-2 font-medium text-violet-700">
                  <Bot className="h-4 w-4" />
                  Memory
                </div>

                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Measures model-memory or latent brand
                  knowledge without live web retrieval.
                </p>
              </div>

              <div className="crystal-subcard rounded-[18px] border-blue-200/80 bg-blue-50/55 p-4">
                <div className="flex items-center gap-2 font-medium text-blue-700">
                  <Globe2 className="h-4 w-4" />
                  Web Search
                </div>

                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Measures live-web retrieval,
                  first-party evidence exposure and
                  citation behavior.
                </p>
              </div>
            </div>
          </div>

          <div className="crystal-panel rounded-[22px] p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-slate-950">
                  Web Experiments
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Stored live-web measurement sets.
                </p>
              </div>

              <Activity className="h-5 w-5 text-[#5f75ff]" />
            </div>

            {experiments.experiments
              .filter(
                (item) =>
                  item.benchmark_mode ===
                  "web_search",
              )
              .map(
                (item) => (
                  <div
                    key={item.id}
                    className="mt-6 border-t border-slate-200/70 pt-6 first:mt-5 first:border-t-0 first:pt-0"
                  >
                    <div className="text-lg font-semibold text-slate-950">
                      {item.name}
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-3">
                      <div className="crystal-subcard rounded-2xl p-4">
                        <div className="text-xs text-slate-500">
                          Web visibility
                        </div>

                        <div className="crystal-value mt-2 text-xl font-medium">
                          {metricValue(
                            item
                              .web_visibility_score_v1,
                          )}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-4">
                        <div className="text-xs text-slate-500">
                          Raw coverage
                        </div>

                        <div className="crystal-value mt-2 text-xl font-medium">
                          {percent(
                            item
                              .target_response_coverage,
                          )}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-4">
                        <div className="text-xs text-slate-500">
                          Verified coverage
                        </div>

                        <div className="crystal-value mt-2 text-xl font-medium">
                          {percent(
                            item
                              .entity_verified_target_mention_rate,
                          )}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-4">
                        <div className="text-xs text-slate-500">
                          Source presence
                        </div>

                        <div className="crystal-value mt-2 text-xl font-medium">
                          {percent(
                            item
                              .target_source_presence_rate,
                          )}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-4">
                        <div className="text-xs text-slate-500">
                          Retrieved
                        </div>

                        <div className="crystal-value mt-2 text-xl font-medium">
                          {percent(
                            item
                              .grounded_target_mention_rate,
                          )}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-4">
                        <div className="text-xs text-slate-500">
                          Cited
                        </div>

                        <div className="crystal-value mt-2 text-xl font-medium">
                          {percent(
                            item
                              .target_cited_response_coverage,
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-50/70 px-4 py-3 text-xs">
                      <span className="text-slate-500">
                        Analysis freshness
                      </span>

                      <span
                        className={
                          item.analysis_is_current
                            ? "text-emerald-300"
                            : "text-amber-300"
                        }
                      >
                        {item.analysis_current_responses}
                        {" / "}
                        {item.analysis_total_responses}
                        {" current"}
                      </span>
                    </div>

                    <p className="mt-5 text-xs leading-5 text-slate-500">
                      Compare this web_search experiment
                      only with compatible measurement sets
                      using the same prompt and measurement
                      configuration.
                    </p>
                  </div>
                ),
              )}
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
