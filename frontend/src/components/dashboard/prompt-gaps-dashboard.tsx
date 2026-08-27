"use client";

import {
  AlertTriangle,
  CircleCheck,
  Crosshair,
  Gauge,
  Radar,
  SearchX,
  Target,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import DashboardShell from "@/components/dashboard/dashboard-shell";
import SiteRAGGapsPanel from "@/components/dashboard/site-rag-gaps-panel";

import type {
  GeoOpportunitySummary,
  SiteRAGGapSummary,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  visibilitySummary: VisibilitySummary;
  gaps: GeoOpportunitySummary;
  siteRagGaps: SiteRAGGapSummary | null;
};


function prettyLabel(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}


function priorityClasses(
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


export default function PromptGapsDashboard({
  visibilitySummary,
  gaps,
  siteRagGaps,
}: Props) {
  const topScore =
    gaps.opportunities.length > 0
      ? Math.max(
          ...gaps.opportunities.map(
            (item) =>
              item.opportunity_score,
          ),
        )
      : 0;

  const gapDistribution = [
    {
      name: "Competitor dominance",
      value:
        gaps.competitor_dominance_prompts,
    },
    {
      name: "Target absent",
      value:
        gaps.target_absent_prompts,
    },
    {
      name: "Unmeasured",
      value:
        gaps.unmeasured_prompts,
    },
    {
      name: "Covered",
      value:
        gaps.covered_prompts,
    },
  ];

  const categoryMap =
    new Map<string, number>();

  for (const opportunity of gaps.opportunities) {
    categoryMap.set(
      opportunity.category,
      (categoryMap.get(
        opportunity.category,
      ) ?? 0) + 1,
    );
  }

  const categoryData =
    Array.from(
      categoryMap.entries(),
    )
      .map(
        ([name, value]) => ({
          name: prettyLabel(name),
          value,
        }),
      )
      .sort(
        (a, b) =>
          b.value - a.value,
      );

  const benchmarkMode =
    gaps.opportunities.find(
      (item) =>
        item.evidence
          ?.benchmark_mode,
    )?.evidence
      ?.benchmark_mode ??
    visibilitySummary.benchmark_mode;

  const measurementBasis =
    gaps.opportunities.find(
      (item) =>
        item.evidence
          ?.measurement_basis,
    )?.evidence
      ?.measurement_basis ??
    (
      benchmarkMode === "web_search"
        ? "grounded_response_presence"
        : "not_available"
    );


  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Prompt Gaps"
    >
      <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
        <section>
          <div>
            <div className="crystal-eyebrow">
              Prompt opportunity intelligence
            </div>

            <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
              {gaps.target_brand}
            </h2>

            <p className="mt-1.5 text-sm text-slate-500">
              {gaps.total_prompts} analyzed prompts ·{" "}
              {benchmarkMode} ·{" "}
              {prettyLabel(
                measurementBasis,
              )}
            </p>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="High Priority"
              value={`${gaps.high_priority}`}
              detail="Highest-value visibility gaps"
              icon={AlertTriangle}
            />

            <MetricCard
              label="Medium Priority"
              value={`${gaps.medium_priority}`}
              detail="Secondary opportunities"
              icon={Target}
            />

            <MetricCard
              label="Competitor Dominance"
              value={`${gaps.competitor_dominance_prompts}`}
              detail="Competitor grounded, target absent"
              icon={Crosshair}
            />

            <MetricCard
              label="Top Opportunity"
              value={topScore.toFixed(0)}
              detail="SearchIntel Opportunity Score V1"
              icon={Gauge}
            />
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <div className="crystal-panel rounded-[22px] p-6">
            <h2 className="font-semibold text-slate-950">
              Gap Distribution
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Current prompt visibility state.
            </p>

            {gaps.total_prompts === 0 ? (
              <div className="mt-6 flex min-h-[260px] items-center justify-center rounded-[20px] border border-dashed border-slate-200 bg-slate-50/40 p-8 text-center">
                <div>
                  <div className="crystal-icon mx-auto h-11 w-11">
                    <SearchX className="h-5 w-5 text-[#5f75ff]" />
                  </div>

                  <h3 className="mt-4 font-medium text-slate-900">
                    No measured prompt gaps yet
                  </h3>

                  <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">
                    Run or select a compatible web-search experiment to generate opportunity data.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-4 h-72">
                <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <PieChart>
                  <Pie
                    data={gapDistribution}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={65}
                    outerRadius={100}
                    paddingAngle={3}
                  >
                    {gapDistribution.map(
                      (entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={
                            [
                              "#7c6cff",
                              "#f59e0b",
                              "#34c98f",
                            ][index]
                          }
                        />
                      ),
                    )}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      background: "rgba(255,255,255,0.98)",
                      border:
                        "1px solid #e2e8f0",
                      borderRadius: "14px",
                      boxShadow:
                        "0 12px 35px rgba(51,65,85,0.10)",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              </div>
            )}

            <div className="grid grid-cols-3 gap-3">
              {gapDistribution.map(
                (item) => (
                  <div
                    key={item.name}
                    className="crystal-subcard rounded-2xl p-3.5"
                  >
                    <div className="text-lg font-semibold text-slate-950">
                      {item.value}
                    </div>

                    <div className="mt-1 text-xs text-slate-500">
                      {item.name}
                    </div>
                  </div>
                ),
              )}
            </div>
          </div>

          <div className="crystal-panel rounded-[22px] p-6">
            <h2 className="font-semibold text-slate-950">
              Prompt Categories
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Opportunity distribution by prompt category.
            </p>

            {categoryData.length === 0 ? (
              <div className="mt-6 flex min-h-[320px] items-center justify-center rounded-[20px] border border-dashed border-slate-200 bg-slate-50/40 p-8 text-center">
                <div>
                  <div className="crystal-icon mx-auto h-11 w-11">
                    <Radar className="h-5 w-5 text-[#5f75ff]" />
                  </div>

                  <h3 className="mt-4 font-medium text-slate-900">
                    No opportunity categories yet
                  </h3>

                  <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-slate-500">
                    Categories will appear after grounded prompt opportunities are available.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-6 h-80">
                <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <BarChart
                  data={categoryData}
                  layout="vertical"
                  margin={{
                    left: 20,
                    right: 20,
                  }}
                >
                  <CartesianGrid
                    horizontal={false}
                    stroke="#e2e8f0"
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    type="number"
                    allowDecimals={false}
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
                    width={130}
                    tick={{
                      fill: "#64748b",
                      fontSize: 12,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "rgba(255,255,255,0.98)",
                      border:
                        "1px solid #e2e8f0",
                      borderRadius: "14px",
                      boxShadow:
                        "0 12px 35px rgba(51,65,85,0.10)",
                    }}
                  />

                  <Bar
                    dataKey="value"
                    fill="#5f75ff"
                    radius={[0, 5, 5, 0]}
                    name="Prompts"
                  />
                </BarChart>
              </ResponsiveContainer>
              </div>
            )}
          </div>
        </section>

        <section className="crystal-panel rounded-[22px]">
          <div className="border-b border-slate-200/80 p-5 lg:p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-slate-950">
                  Priority Opportunities
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Grounded prompt-level visibility gaps
                  ordered by opportunity score.
                </p>
              </div>

              <Radar className="h-5 w-5 text-slate-400" />
            </div>
          </div>

          {gaps.opportunities.length === 0 ? (
            <div className="border-t border-slate-200/70 px-6 py-12 text-center">
              <div className="crystal-icon mx-auto h-11 w-11">
                <Target className="h-5 w-5 text-[#5f75ff]" />
              </div>

              <h3 className="mt-4 font-medium text-slate-900">
                No priority opportunities yet
              </h3>

              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
                Opportunity rows will appear when the selected measurement contains grounded prompt gaps.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1100px] text-left">
              <thead>
                <tr className="border-y border-slate-200/70 bg-slate-50/55 text-[11px] uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-6 py-4">
                    Prompt
                  </th>

                  <th className="px-4 py-4">
                    Category
                  </th>

                  <th className="px-4 py-4">
                    Gap
                  </th>

                  <th className="px-4 py-4">
                    Priority
                  </th>

                  <th className="px-4 py-4">
                    Target
                  </th>

                  <th className="px-4 py-4">
                    Top competitor
                  </th>

                  <th className="px-4 py-4">
                    Pressure
                  </th>

                  <th className="px-4 py-4">
                    Score
                  </th>
                </tr>
              </thead>

              <tbody>
                {gaps.opportunities.map(
                  (item) => (
                    <tr
                      key={item.id}
                      className="border-b border-slate-200/65 align-top transition hover:bg-slate-50/55 last:border-0"
                    >
                      <td className="max-w-md px-6 py-5">
                        <div className="font-medium leading-6 text-slate-800">
                          {item.prompt_text}
                        </div>

                        <div className="mt-2 text-xs leading-5 text-slate-500">
                          {item.recommendation}
                        </div>
                      </td>

                      <td className="px-4 py-5 text-sm text-slate-400">
                        {prettyLabel(
                          item.category,
                        )}
                      </td>

                      <td className="px-4 py-5">
                        <span className="whitespace-nowrap rounded-lg bg-slate-100 px-2.5 py-1 text-xs text-slate-700">
                          {prettyLabel(
                            item.gap_type,
                          )}
                        </span>
                      </td>

                      <td className="px-4 py-5">
                        <span
                          className={[
                            "rounded-lg px-2.5 py-1 text-xs font-medium capitalize",
                            priorityClasses(
                              item.priority,
                            ),
                          ].join(" ")}
                        >
                          {item.priority}
                        </span>
                      </td>

                      <td className="px-4 py-5 text-sm font-medium text-slate-700">
                        {item.gap_type ===
                        "unmeasured_web_search"
                          ? "N/A"
                          : `${item.target_mention_rate.toFixed(0)}%`}
                      </td>

                      <td className="px-4 py-5 text-sm text-slate-700">
                        {item.top_competitor_name ??
                          "—"}
                      </td>

                      <td className="px-4 py-5 text-sm text-slate-700">
                        {item.gap_type ===
                        "unmeasured_web_search"
                          ? "N/A"
                          : `${item.top_competitor_run_coverage.toFixed(0)}%`}
                      </td>

                      <td className="px-4 py-5">
                        <span className="text-lg font-semibold text-violet-600">
                          {item.opportunity_score.toFixed(
                            0,
                          )}
                        </span>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
              </table>
            </div>
          )}
        </section>

        <SiteRAGGapsPanel
          gaps={siteRagGaps}
        />

        <section className="rounded-[22px] border border-blue-200/70 bg-blue-50/65 p-6">
          <div className="flex gap-4">
            <div className="crystal-icon mt-0.5 h-10 w-10 shrink-0">
              {gaps.covered_prompts ===
              gaps.total_prompts ? (
                <CircleCheck className="h-5 w-5 text-emerald-400" />
              ) : (
                <SearchX className="h-5 w-5 text-[#5f75ff]" />
              )}
            </div>

            <div>
              <h2 className="font-semibold text-slate-950">
                Measurement basis
              </h2>

              <p className="mt-2 max-w-4xl text-sm leading-7 text-slate-600">
                For this web-search experiment, target
                and competitor presence require both a
                resolved textual brand mention and
                same-brand first-party source retrieval
                in the same response.
              </p>

              <p className="mt-2 text-xs text-slate-500">
                Competitor pressure depends on the
                completeness of registered first-party
                domain mappings. Prompts with no live-web
                sources are reported as unmeasured rather
                than content or competitor gaps.
              </p>
            </div>
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
