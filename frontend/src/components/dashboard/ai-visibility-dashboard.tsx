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
    <div className="crystal-subcard min-w-0 flex-1 rounded-[18px] p-5">
      <div className="flex items-center gap-3">
        <div className="crystal-icon h-10 w-10">
          <Icon className="h-4 w-4 text-[#5f75ff]" />
        </div>

        <div className="text-sm font-medium text-slate-700">
          {label}
        </div>
      </div>

      <div className="crystal-value mt-5 text-2xl font-medium">
        {count}
        <span className="ml-1 text-sm font-normal text-slate-500">
          / {total}
        </span>
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          className="crystal-accent h-full rounded-full"
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
      <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
        <section>
          <div>
            <div className="crystal-eyebrow">
              AI search visibility
            </div>

            <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
              {metrics.target_brand}
            </h2>

            <p className="mt-1.5 text-sm text-slate-500">
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

        <section className="crystal-panel rounded-[22px] p-6">
          <div>
            <h2 className="font-semibold text-slate-950">
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

            <ChevronRight className="mx-auto h-5 w-5 rotate-90 shrink-0 text-slate-300 lg:rotate-0" />

            <FunnelStage
              label="Verified"
              count={
                summary.funnel
                  .entity_verified_responses
              }
              total={total}
              icon={CircleCheck}
            />

            <ChevronRight className="mx-auto h-5 w-5 rotate-90 shrink-0 text-slate-300 lg:rotate-0" />

            <FunnelStage
              label="Retrieved"
              count={targetRetrieved}
              total={total}
              icon={Search}
            />

            <ChevronRight className="mx-auto h-5 w-5 rotate-90 shrink-0 text-slate-300 lg:rotate-0" />

            <FunnelStage
              label="Cited"
              count={targetCited}
              total={total}
              icon={FileCheck2}
            />
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.55fr_0.85fr]">
          <div className="crystal-panel rounded-[22px] p-6">
            <h2 className="font-semibold text-slate-950">
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
                    stroke="#e2e8f0"
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
                      fill: "#64748b",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <Tooltip
                    cursor={{
                      fill: "rgba(241,245,249,0.72)",
                    }}
                    contentStyle={{
                      background:
                        "rgba(255,255,255,0.98)",
                      border:
                        "1px solid #e2e8f0",
                      borderRadius: "14px",
                      padding: "12px 14px",
                      boxShadow:
                        "0 14px 40px rgba(51,65,85,0.12)",
                    }}
                    labelStyle={{
                      color: "#0f172a",
                      fontWeight: 600,
                      marginBottom: "6px",
                    }}
                    itemStyle={{
                      fontSize: "13px",
                      padding: "2px 0",
                    }}
                  />

                  <Legend />

                  <Bar
                    dataKey="Mentioned"
                    fill="#5f75ff"
                    radius={[0, 6, 6, 0]}
                  />

                  <Bar
                    dataKey="Retrieved"
                    fill="#8b7cff"
                    radius={[0, 6, 6, 0]}
                  />

                  <Bar
                    dataKey="Cited"
                    fill="#34c98f"
                    radius={[0, 6, 6, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="crystal-panel rounded-[22px] p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="crystal-eyebrow">
                  Primary bottleneck
                </div>

                <div className="mt-2 text-2xl font-semibold capitalize text-slate-950">
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

            <p className="mt-5 text-sm leading-7 text-slate-600">
              {summary.diagnosis.message}
            </p>

            <div className="mt-6 space-y-3">
              <div className="crystal-subcard rounded-2xl p-4">
                <div className="text-xs text-slate-500">
                  Source presence
                </div>

                <div className="mt-2 text-lg font-medium text-slate-950">
                  {formatPercent(
                    metrics
                      .target_source_presence_rate,
                  )}
                </div>
              </div>

              <div className="crystal-subcard rounded-2xl p-4">
                <div className="text-xs text-slate-500">
                  Source exposure SOV
                </div>

                <div className="mt-2 text-lg font-medium text-slate-950">
                  {formatPercent(
                    metrics
                      .target_source_exposure_share_of_voice,
                  )}
                </div>
              </div>

              <div className="crystal-subcard rounded-2xl p-4">
                <div className="text-xs text-slate-500">
                  Citation conversion
                </div>

                <div className="mt-2 text-lg font-medium text-slate-950">
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
          <div className="crystal-panel rounded-[22px]">
            <div className="p-5 pb-3">
              <h2 className="font-semibold text-slate-950">
                First-Party Source Exposure
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Repeated first-party discovery across
                measured responses.
              </p>
            </div>

            <div className="divide-y divide-slate-200/70">
              {metrics
                .source_exposure_share_of_voice
                .slice(0, 8)
                .map(
                  (item, index) => (
                    <div
                      key={item.brand_id}
                      className="flex items-center gap-4 px-5 py-4"
                    >
                      <div className="w-6 text-xs text-slate-400">
                        {index + 1}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium text-slate-800">
                          {item.name}
                        </div>

                        <div className="mt-1 text-xs text-slate-500">
                          {
                            item.source_exposures
                          }{" "}
                          source exposures
                        </div>
                      </div>

                      <div className="text-sm font-semibold text-violet-600">
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

          <div className="crystal-panel rounded-[22px]">
            <div className="p-5 pb-3">
              <h2 className="font-semibold text-slate-950">
                Source → Citation Conversion
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                How often retrieved first-party source
                exposures become citation exposures.
              </p>
            </div>

            <div className="divide-y divide-slate-200/70">
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
                          <span className="truncate text-sm font-medium text-slate-800">
                            {item.name}
                          </span>

                          {item.source_exposures <
                            5 && (
                            <span className="rounded-md bg-amber-500/10 px-2 py-0.5 text-[10px] text-amber-700">
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

                      <div className="text-sm font-semibold text-emerald-600">
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
