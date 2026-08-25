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
} from "lucide-react";

import DashboardShell from "@/components/dashboard/dashboard-shell";

import type {
  ExperimentComparison,
  ExperimentMetricValue,
  ExperimentsSummary,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
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
    return "text-emerald-400";
  }

  if (value < 0) {
    return "text-red-400";
  }

  return "text-slate-400";
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
    <div className="grid grid-cols-[1.4fr_1fr_1fr_0.8fr] items-center gap-4 border-b border-slate-800/70 px-5 py-4 last:border-0">
      <div className="text-sm text-slate-300">
        {label}
      </div>

      <div className="text-sm text-slate-400">
        {render(metric.baseline)}
      </div>

      <div className="text-sm text-slate-200">
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
  visibilitySummary,
  experiments,
  comparison,
}: Props) {
  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Experiments"
    >
      <div className="mx-auto max-w-7xl space-y-6 p-5 lg:p-8">
        <section>
          <div>
            <div className="text-sm text-slate-500">
              Controlled measurement
            </div>

            <h2 className="mt-1 text-xl font-semibold text-white">
              GEO Experiments
            </h2>

            <p className="mt-1 text-sm text-slate-500">
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
            <h2 className="font-semibold text-white">
              Experiment Registry
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Memory and live-web experiments remain
              separate measurement modes.
            </p>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            {experiments.experiments.map(
              (experiment) => {
                const web =
                  experiment.benchmark_mode ===
                  "web_search";

                return (
                  <div
                    key={experiment.id}
                    className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-xs uppercase tracking-wider text-slate-500">
                          {experiment.phase}
                        </div>

                        <h3 className="mt-2 text-lg font-semibold text-white">
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
                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                        <div className="text-xs text-slate-500">
                          Runs
                        </div>

                        <div className="mt-1 text-lg font-semibold text-white">
                          {experiment.runs}
                        </div>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                        <div className="text-xs text-slate-500">
                          Prompts
                        </div>

                        <div className="mt-1 text-lg font-semibold text-white">
                          {experiment.prompts}
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">
                          Response coverage
                        </span>

                        <span className="text-slate-200">
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

                            <span className="text-slate-200">
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

                            <span className="text-slate-200">
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

                            <span className="text-slate-200">
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

                            <span className="text-slate-200">
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

                            <span className="text-slate-200">
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

                            <span className="text-slate-200">
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

        {comparison && (
          <section className="rounded-2xl border border-slate-800 bg-slate-900/60">
            <div className="border-b border-slate-800 p-5 lg:p-6">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <h2 className="font-semibold text-white">
                    Same-Mode Comparison
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Direct comparison is allowed only
                    when benchmark modes match.
                  </p>
                </div>

                <div className="flex items-center gap-3 text-sm">
                  <span className="rounded-lg bg-slate-800 px-3 py-1.5 text-slate-300">
                    {comparison.baseline_name}
                  </span>

                  <ArrowRight className="h-4 w-4 text-slate-600" />

                  <span className="rounded-lg bg-slate-800 px-3 py-1.5 text-slate-300">
                    {comparison.comparison_name}
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-[1.4fr_1fr_1fr_0.8fr] gap-4 border-b border-slate-800 px-5 py-3 text-xs uppercase tracking-wider text-slate-500">
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
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-white">
                  Measurement Modes
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Do not compare unlike experiment modes.
                </p>
              </div>

              <Layers3 className="h-5 w-5 text-slate-600" />
            </div>

            <div className="mt-6 space-y-4">
              <div className="rounded-xl border border-violet-500/15 bg-violet-500/5 p-4">
                <div className="flex items-center gap-2 font-medium text-violet-300">
                  <Bot className="h-4 w-4" />
                  Memory
                </div>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Measures model-memory or latent brand
                  knowledge without live web retrieval.
                </p>
              </div>

              <div className="rounded-xl border border-cyan-500/15 bg-cyan-500/5 p-4">
                <div className="flex items-center gap-2 font-medium text-cyan-300">
                  <Globe2 className="h-4 w-4" />
                  Web Search
                </div>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Measures live-web retrieval,
                  first-party evidence exposure and
                  citation behavior.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-white">
                  Web Experiments
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Stored live-web measurement sets.
                </p>
              </div>

              <Activity className="h-5 w-5 text-cyan-400" />
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
                    className="mt-6"
                  >
                    <div className="text-lg font-semibold text-white">
                      {item.name}
                    </div>

                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="text-xs text-slate-500">
                          Web visibility
                        </div>

                        <div className="mt-2 text-xl font-semibold text-white">
                          {metricValue(
                            item
                              .web_visibility_score_v1,
                          )}
                        </div>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="text-xs text-slate-500">
                          Raw coverage
                        </div>

                        <div className="mt-2 text-xl font-semibold text-white">
                          {percent(
                            item
                              .target_response_coverage,
                          )}
                        </div>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="text-xs text-slate-500">
                          Verified coverage
                        </div>

                        <div className="mt-2 text-xl font-semibold text-white">
                          {percent(
                            item
                              .entity_verified_target_mention_rate,
                          )}
                        </div>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="text-xs text-slate-500">
                          Source presence
                        </div>

                        <div className="mt-2 text-xl font-semibold text-white">
                          {percent(
                            item
                              .target_source_presence_rate,
                          )}
                        </div>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="text-xs text-slate-500">
                          Retrieved
                        </div>

                        <div className="mt-2 text-xl font-semibold text-white">
                          {percent(
                            item
                              .grounded_target_mention_rate,
                          )}
                        </div>
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                        <div className="text-xs text-slate-500">
                          Cited
                        </div>

                        <div className="mt-2 text-xl font-semibold text-white">
                          {percent(
                            item
                              .target_cited_response_coverage,
                          )}
                        </div>
                      </div>
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
