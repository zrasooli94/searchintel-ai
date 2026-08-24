"use client";

import {
  Activity,
  BarChart3,
  Bot,
  ChevronRight,
  CircleAlert,
  CircleCheck,
  Database,
  FileSearch,
  FlaskConical,
  Gauge,
  Globe2,
  LayoutDashboard,
  ListChecks,
  Radar,
  Search,
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
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <span className="text-sm font-medium text-slate-400">
          {title}
        </span>

        <div className="rounded-xl bg-slate-800 p-2.5">
          <Icon className="h-4 w-4 text-cyan-400" />
        </div>
      </div>

      <div className="text-3xl font-semibold tracking-tight text-white">
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
  icon: typeof Activity;
}) {
  const percentage =
    total > 0
      ? (count / total) * 100
      : 0;

  return (
    <div className="min-w-0 flex-1 rounded-2xl border border-slate-800 bg-slate-950/50 p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="rounded-xl bg-slate-800 p-2.5">
          <Icon className="h-4 w-4 text-cyan-400" />
        </div>

        <span className="text-sm font-medium text-slate-300">
          {label}
        </span>
      </div>

      <div className="text-2xl font-semibold text-white">
        {count}
        <span className="ml-1 text-base font-normal text-slate-500">
          / {total}
        </span>
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-cyan-400"
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
        <div className="mx-auto max-w-7xl space-y-6 p-5 lg:p-8">
          <section>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white">
                {target.brand}
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {summary.analyzed_prompts} prompts ·{" "}
                {summary.analyzed_runs} analyzed runs ·{" "}
                {summary.benchmark_mode}
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
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

          <section className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 lg:p-6">
            <div className="mb-5">
              <h2 className="font-semibold text-white">
                Visibility Funnel
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                From brand appearance to retrieved and
                cited first-party evidence.
              </p>
            </div>

            <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center">
              <FunnelStage
                label="Mentioned"
                count={funnel.mentioned_responses}
                total={funnel.total_responses}
                icon={Activity}
              />

              <ChevronRight className="mx-auto h-5 w-5 rotate-90 text-slate-700 md:rotate-0" />

              <FunnelStage
                label="Retrieved"
                count={
                  funnel.retrieval_associated_responses
                }
                total={funnel.total_responses}
                icon={Globe2}
              />

              <ChevronRight className="mx-auto h-5 w-5 rotate-90 text-slate-700 md:rotate-0" />

              <FunnelStage
                label="Cited"
                count={funnel.cited_responses}
                total={funnel.total_responses}
                icon={ShieldCheck}
              />
            </div>
          </section>

          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.6fr]">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-5 flex items-start justify-between">
                <div>
                  <div className="text-sm text-slate-500">
                    Primary bottleneck
                  </div>

                  <div className="mt-2 text-2xl font-semibold capitalize text-white">
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

              <p className="text-sm leading-6 text-slate-400">
                {summary.diagnosis.message}
              </p>

              <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <div className="text-xs uppercase tracking-wider text-slate-500">
                  Diagnostic rule
                </div>

                <div className="mt-2 text-sm text-slate-300">
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

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
              <div className="mb-5">
                <h2 className="font-semibold text-white">
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
                      cursor={{
                        fill: "#0f172a",
                      }}
                      contentStyle={{
                        background: "#020617",
                        border: "1px solid #1e293b",
                        borderRadius: "12px",
                      }}
                      labelStyle={{
                        color: "#f8fafc",
                      }}
                    />

                    <Bar
                      dataKey="coverage"
                      fill="#22d3ee"
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
