"use client";

import type {
  LucideIcon,
} from "lucide-react";

import {
  Activity,
  Bot,
  CircleAlert,
  CircleCheck,
  ChevronRight,
  Database,
  FileCheck2,
  Gauge,
  Globe2,
  Radar,
  Search,
  ShieldCheck,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import DashboardShell from "@/components/dashboard/dashboard-shell";

import type {
  AIVisibilityMetrics,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  summary: VisibilitySummary;
  metrics: AIVisibilityMetrics;
};


function formatPercent(
  value: number | null,
) {
  if (value === null) {
    return "N/A";
  }

  return `${value.toFixed(2)}%`;
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
  icon: LucideIcon;
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


function FunnelStage({
  label,
  count,
  total,
  icon: Icon,
}: {
  label: string;
  count: number;
  total: number;
  icon: LucideIcon;
}) {
  const coverage =
    total > 0
      ? (count / total) * 100
      : 0;

  return (
    <div className="flex-1 rounded-2xl border border-slate-800 bg-slate-950/50 p-5">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-slate-800 p-2.5">
          <Icon className="h-4 w-4 text-cyan-400" />
        </div>

        <div className="text-sm font-medium text-slate-300">
          {label}
        </div>
      </div>

      <div className="mt-5 text-2xl font-semibold text-white">
        {count}
        <span className="ml-1 text-sm font-normal text-slate-500">
          / {total}
        </span>
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-cyan-400"
          style={{
            width: `${Math.min(
              coverage,
              100,
            )}%`,
          }}
        />
      </div>

      <div className="mt-2 text-xs text-slate-500">
        {coverage.toFixed(2)}% coverage
      </div>
    </div>
  );
}


export default function AIVisibilityDashboard({
  summary,
  metrics,
}: Props) {
  const retrievalByBrand =
    new Map(
      metrics
        .grounded_response_share_of_voice
        .map(
          (item) => [
            item.brand_id,
            item.grounded_response_coverage,
          ],
        ),
    );

  const citedByBrand =
    new Map(
      metrics
        .cited_response_share_of_voice
        .map(
          (item) => [
            item.brand_id,
            item.cited_response_coverage,
          ],
        ),
    );

  const competitorStageData =
    metrics.response_share_of_voice
      .filter(
        (item) =>
          item.brand_id !==
          metrics.target_brand_id,
      )
      .slice(0, 6)
      .map(
        (item) => ({
          name: item.name,
          Mentioned:
            item.response_coverage,
          Retrieved:
            retrievalByBrand.get(
              item.brand_id,
            ) ?? 0,
          Cited:
            citedByBrand.get(
              item.brand_id,
            ) ?? 0,
        }),
      );

  const total =
    metrics.web_search_analyzed_runs ||
    metrics.analyzed_runs;

  const targetMentioned =
    metrics.response_share_of_voice.find(
      (item) =>
        item.brand_id ===
        metrics.target_brand_id,
    )?.response_exposures ?? 0;

  const targetRetrieved =
    metrics
      .grounded_response_share_of_voice
      .find(
        (item) =>
          item.brand_id ===
          metrics.target_brand_id,
      )
      ?.grounded_response_exposures ?? 0;

  const targetCited =
    metrics
      .cited_response_share_of_voice
      .find(
        (item) =>
          item.brand_id ===
          metrics.target_brand_id,
      )
      ?.cited_response_exposures ?? 0;

  return (
    <DashboardShell
      summary={summary}
      title="AI Visibility"
    >
      <div className="mx-auto max-w-7xl space-y-6 p-5 lg:p-8">
        <section>
          <div>
            <div className="text-sm text-slate-500">
              AI search visibility
            </div>

            <h2 className="mt-1 text-xl font-semibold text-white">
              {metrics.target_brand}
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              {metrics.analyzed_prompts} prompts ·{" "}
              {metrics.analyzed_runs} analyzed runs ·{" "}
              {metrics.benchmark_mode}
            </p>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <MetricCard
              label="Web Visibility"
              value={
                metrics.web_visibility_score_v1
                  ?.toFixed(2) ?? "N/A"
              }
              detail="SearchIntel Web Visibility V1"
              icon={Gauge}
            />

            <MetricCard
              label="Raw Coverage"
              value={formatPercent(
                metrics.target_response_coverage,
              )}
              detail="Responses mentioning target"
              icon={Activity}
            />

            <MetricCard
              label="Verified Coverage"
              value={formatPercent(
                metrics
                  .entity_verified_target_mention_rate,
              )}
              detail="Alias + registered-brand evidence"
              icon={CircleCheck}
            />

            <MetricCard
              label="Retrieved Coverage"
              value={formatPercent(
                metrics
                  .grounded_target_mention_rate,
              )}
              detail="Mention + first-party retrieval"
              icon={Globe2}
            />

            <MetricCard
              label="Cited Coverage"
              value={formatPercent(
                metrics
                  .target_cited_response_coverage,
              )}
              detail="Mention + first-party citation"
              icon={ShieldCheck}
            />
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <div>
            <h2 className="font-semibold text-white">
              Target Visibility Funnel
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Separates raw appearance from verified identity,
              retrieved evidence and citations.
            </p>
          </div>

          <div className="mt-6 flex flex-col items-stretch gap-3 lg:flex-row lg:items-center">
            <FunnelStage
              label="Mentioned"
              count={targetMentioned}
              total={total}
              icon={Activity}
            />

            <ChevronRight className="mx-auto h-5 w-5 rotate-90 shrink-0 text-slate-700 lg:rotate-0" />

            <FunnelStage
              label="Verified"
              count={
                summary.funnel
                  .entity_verified_responses
              }
              total={total}
              icon={CircleCheck}
            />

            <ChevronRight className="mx-auto h-5 w-5 rotate-90 shrink-0 text-slate-700 lg:rotate-0" />

            <FunnelStage
              label="Retrieved"
              count={targetRetrieved}
              total={total}
              icon={Search}
            />

            <ChevronRight className="mx-auto h-5 w-5 rotate-90 shrink-0 text-slate-700 lg:rotate-0" />

            <FunnelStage
              label="Cited"
              count={targetCited}
              total={total}
              icon={FileCheck2}
            />
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.55fr_0.85fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="font-semibold text-white">
              Competitor Visibility by Stage
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Response coverage versus retrieval-associated
              and cited response coverage.
            </p>

            <div className="mt-6 h-96">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <BarChart
                  data={competitorStageData}
                  layout="vertical"
                  margin={{
                    top: 10,
                    right: 20,
                    left: 20,
                    bottom: 10,
                  }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    horizontal={false}
                    stroke="#1e293b"
                  />

                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    tick={{
                      fill: "#64748b",
                      fontSize: 11,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <YAxis
                    type="category"
                    dataKey="name"
                    width={110}
                    tick={{
                      fill: "#cbd5e1",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#020617",
                      border:
                        "1px solid #1e293b",
                      borderRadius: "12px",
                    }}
                  />

                  <Legend />

                  <Bar
                    dataKey="Mentioned"
                    fill="#22d3ee"
                    radius={[0, 4, 4, 0]}
                  />

                  <Bar
                    dataKey="Retrieved"
                    fill="#818cf8"
                    radius={[0, 4, 4, 0]}
                  />

                  <Bar
                    dataKey="Cited"
                    fill="#34d399"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm text-slate-500">
                  Primary bottleneck
                </div>

                <div className="mt-2 text-2xl font-semibold capitalize text-white">
                  {
                    summary.diagnosis
                      .primary_bottleneck
                  }
                </div>
              </div>

              <div className="rounded-xl bg-amber-500/10 p-3">
                <CircleAlert className="h-5 w-5 text-amber-400" />
              </div>
            </div>

            <p className="mt-5 text-sm leading-6 text-slate-400">
              {summary.diagnosis.message}
            </p>

            <div className="mt-6 space-y-3">
              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <div className="text-xs text-slate-500">
                  Source presence
                </div>

                <div className="mt-2 text-lg font-medium text-white">
                  {formatPercent(
                    metrics
                      .target_source_presence_rate,
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <div className="text-xs text-slate-500">
                  Source exposure SOV
                </div>

                <div className="mt-2 text-lg font-medium text-white">
                  {formatPercent(
                    metrics
                      .target_source_exposure_share_of_voice,
                  )}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <div className="text-xs text-slate-500">
                  Citation conversion
                </div>

                <div className="mt-2 text-lg font-medium text-white">
                  {formatPercent(
                    metrics
                      .target_citation_exposure_conversion,
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60">
            <div className="border-b border-slate-800 p-5">
              <h2 className="font-semibold text-white">
                First-Party Source Exposure
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Repeated first-party discovery across
                measured responses.
              </p>
            </div>

            <div className="divide-y divide-slate-800">
              {metrics
                .source_exposure_share_of_voice
                .slice(0, 8)
                .map(
                  (item, index) => (
                    <div
                      key={item.brand_id}
                      className="flex items-center gap-4 px-5 py-4"
                    >
                      <div className="w-6 text-xs text-slate-600">
                        {index + 1}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium text-slate-200">
                          {item.name}
                        </div>

                        <div className="mt-1 text-xs text-slate-500">
                          {
                            item.source_exposures
                          }{" "}
                          source exposures
                        </div>
                      </div>

                      <div className="text-sm font-medium text-cyan-300">
                        {formatPercent(
                          item
                            .source_exposure_share_of_voice,
                        )}
                      </div>
                    </div>
                  ),
                )}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60">
            <div className="border-b border-slate-800 p-5">
              <h2 className="font-semibold text-white">
                Source → Citation Conversion
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                How often retrieved first-party source
                exposures become citation exposures.
              </p>
            </div>

            <div className="divide-y divide-slate-800">
              {metrics.brand_citation_conversion
                .slice(0, 8)
                .map(
                  (item) => (
                    <div
                      key={item.brand_id}
                      className="flex items-center gap-4 px-5 py-4"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-medium text-slate-200">
                            {item.name}
                          </span>

                          {item.source_exposures <
                            5 && (
                            <span className="rounded-md bg-amber-500/10 px-2 py-0.5 text-[10px] text-amber-300">
                              small sample
                            </span>
                          )}
                        </div>

                        <div className="mt-1 text-xs text-slate-500">
                          {
                            item.citation_exposures
                          }{" "}
                          cited /{" "}
                          {
                            item.source_exposures
                          }{" "}
                          retrieved
                        </div>
                      </div>

                      <div className="text-sm font-medium text-emerald-300">
                        {formatPercent(
                          item
                            .citation_exposure_conversion,
                        )}
                      </div>
                    </div>
                  ),
                )}
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard
            label="Search Sources"
            value={
              metrics.unique_search_source_urls.toLocaleString()
            }
            detail={`${metrics.unique_search_domains} unique domains`}
            icon={Database}
          />

          <MetricCard
            label="Overall Source → Citation"
            value={formatPercent(
              metrics
                .source_to_citation_conversion,
            )}
            detail="All unique retrieved source URLs"
            icon={Radar}
          />

          <MetricCard
            label="Resolved First-Party Sources"
            value={formatPercent(
              metrics
                .resolved_first_party_source_rate,
            )}
            detail="Sources mapped to registered brands"
            icon={Bot}
          />
        </section>
      </div>
    </DashboardShell>
  );
}
