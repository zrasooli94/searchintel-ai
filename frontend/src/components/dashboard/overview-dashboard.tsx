"use client";

import {
  Activity,
  BarChart3,
  ChevronRight,
  CircleAlert,
  CircleCheck,
  FileSearch,
  Gauge,
  Globe2,
  ShieldCheck,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  VisibilitySummary,
} from "@/lib/types";

import DashboardShell from "@/components/dashboard/dashboard-shell";

type Props = {
  summary: VisibilitySummary;
};



function formatPercent(
  value: number | null,
): string {
  if (value === null) {
    return "N/A";
  }

  return `${value.toFixed(2)}%`;
}

function StatCard({
  title,
  value,
  detail,
  icon: Icon,
}: {
  title: string;
  value: string;
  detail: string;
  icon: typeof Gauge;
}) {
  return (
    <div className="crystal-card rounded-[20px] p-5">
      <div className="mb-5 flex items-start justify-between gap-4">
        <span className="crystal-eyebrow">
          {title}
        </span>

        <div className="crystal-icon h-10 w-10">
          <Icon className="h-[18px] w-[18px] text-[#5f75ff]" />
        </div>
      </div>

      <div className="crystal-value text-3xl font-medium">
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
  icon: typeof Activity;
}) {
  const percentage =
    total > 0
      ? (count / total) * 100
      : 0;

  return (
    <div className="crystal-subcard min-w-0 flex-1 rounded-[18px] p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="crystal-icon h-10 w-10">
          <Icon className="h-4 w-4 text-[#5f75ff]" />
        </div>

        <span className="text-sm font-medium text-slate-700">
          {label}
        </span>
      </div>

      <div className="crystal-value text-2xl font-medium">
        {count}
        <span className="ml-1 text-base font-normal text-slate-500">
          / {total}
        </span>
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          className="crystal-accent h-full rounded-full"
          style={{
            width: `${Math.min(
              percentage,
              100,
            )}%`,
          }}
        />
      </div>

      <div className="mt-2 text-xs text-slate-500">
        {percentage.toFixed(2)}% coverage
      </div>
    </div>
  );
}

export default function OverviewDashboard({
  summary,
}: Props) {
  const target = summary.target;
  const funnel = summary.funnel;

  const competitors =
    summary.leaders.response_visibility;

  const bottleneck =
    summary.diagnosis.primary_bottleneck;

  return (
    <DashboardShell
      summary={summary}
      title="Overview"
    >
        <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
          <section>
            <div className="mb-5">
              <div className="crystal-eyebrow">
                Current measurement
              </div>

              <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
                {target.brand}
              </h2>

              <p className="mt-1.5 text-sm text-slate-500">
                {summary.analyzed_prompts} prompts ·{" "}
                {summary.analyzed_runs} analyzed runs ·{" "}
                {summary.benchmark_mode}
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              <StatCard
                title="Web Visibility"
                value={
                  target.web_visibility_score?.toFixed(
                    2,
                  ) ?? "N/A"
                }
                detail="SearchIntel Web Visibility V1"
                icon={Gauge}
              />

              <StatCard
                title="Raw Coverage"
                value={formatPercent(
                  target.raw_response_coverage,
                )}
                detail="Responses mentioning target"
                icon={Activity}
              />

              <StatCard
                title="Verified Coverage"
                value={formatPercent(
                  target.entity_verified_response_coverage,
                )}
                detail="Alias + registered-brand evidence"
                icon={CircleCheck}
              />

              <StatCard
                title="Retrieved Coverage"
                value={formatPercent(
                  target.retrieval_associated_response_coverage,
                )}
                detail="Mention + first-party retrieval"
                icon={FileSearch}
              />

              <StatCard
                title="Cited Coverage"
                value={formatPercent(
                  target.cited_response_coverage,
                )}
                detail="Mention + first-party citation"
                icon={ShieldCheck}
              />
            </div>
          </section>

          <section className="crystal-panel rounded-[22px] p-5 lg:p-6">
            <div className="mb-5">
              <h2 className="font-semibold text-slate-950">
                Visibility Funnel
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                From raw brand appearance to verified identity,
                retrieval and citation evidence.
              </p>
            </div>

            <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center">
              <FunnelStage
                label="Mentioned"
                count={funnel.mentioned_responses}
                total={funnel.total_responses}
                icon={Activity}
              />

              <ChevronRight className="mx-auto h-5 w-5 rotate-90 text-slate-300 md:rotate-0" />

              <FunnelStage
                label="Verified"
                count={funnel.entity_verified_responses}
                total={funnel.total_responses}
                icon={CircleCheck}
              />

              <ChevronRight className="mx-auto h-5 w-5 rotate-90 text-slate-300 md:rotate-0" />

              <FunnelStage
                label="Retrieved"
                count={
                  funnel.retrieval_associated_responses
                }
                total={funnel.total_responses}
                icon={Globe2}
              />

              <ChevronRight className="mx-auto h-5 w-5 rotate-90 text-slate-300 md:rotate-0" />

              <FunnelStage
                label="Cited"
                count={funnel.cited_responses}
                total={funnel.total_responses}
                icon={ShieldCheck}
              />
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.6fr]">
            <div className="crystal-panel rounded-[22px] p-6">
              <div className="mb-5 flex items-start justify-between">
                <div>
                  <div className="crystal-eyebrow">
                    Primary bottleneck
                  </div>

                  <div className="mt-2 text-2xl font-semibold capitalize text-slate-950">
                    {bottleneck.replaceAll(
                      "_",
                      " ",
                    )}
                  </div>
                </div>

                <div className="rounded-xl bg-amber-500/10 p-3">
                  {bottleneck === "none" ? (
                    <CircleCheck className="h-5 w-5 text-emerald-400" />
                  ) : (
                    <CircleAlert className="h-5 w-5 text-amber-400" />
                  )}
                </div>
              </div>

              <p className="text-sm leading-7 text-slate-600">
                {summary.diagnosis.message}
              </p>

              <div className="crystal-subcard mt-6 rounded-2xl p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500">
                  Diagnostic rule
                </div>

                <div className="mt-2 text-sm text-slate-700">
                  {summary.diagnosis.rule_version}
                </div>

                <div className="mt-1 text-xs text-slate-500">
                  Coverage threshold:{" "}
                  {
                    summary.diagnosis
                      .coverage_threshold
                  }
                  %
                </div>
              </div>
            </div>

            <div className="crystal-panel rounded-[22px] p-6">
              <div className="mb-5">
                <h2 className="font-semibold text-slate-950">
                  Competitor Response Visibility
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Share and response coverage for the
                  leading resolved brands.
                </p>
              </div>

              <div className="h-72">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <BarChart
                    data={competitors}
                    layout="vertical"
                    margin={{
                      top: 5,
                      right: 15,
                      left: 15,
                      bottom: 5,
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

                    <Bar
                      dataKey="coverage"
                      fill="#5f75ff"
                      radius={[0, 6, 6, 0]}
                      name="Coverage %"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            <StatCard
              title="Response SOV"
              value={formatPercent(
                target.response_share_of_voice,
              )}
              detail="Hierarchy-safe raw brand exposure"
              icon={BarChart3}
            />

            <StatCard
              title="Source Exposure SOV"
              value={formatPercent(
                target.source_exposure_share_of_voice,
              )}
              detail="First-party retrieval exposure"
              icon={Globe2}
            />

            <StatCard
              title="Citation Exposure SOV"
              value={formatPercent(
                target.citation_exposure_share_of_voice,
              )}
              detail="First-party citation exposure"
              icon={FileSearch}
            />
          </section>
        </div>
    </DashboardShell>
  );
}
