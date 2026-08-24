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

import type {
  GeoOpportunitySummary,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  visibilitySummary: VisibilitySummary;
  gaps: GeoOpportunitySummary;
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
    return "bg-red-500/10 text-red-300";
  }

  if (priority === "medium") {
    return "bg-amber-500/10 text-amber-300";
  }

  return "bg-slate-800 text-slate-300";
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


export default function PromptGapsDashboard({
  visibilitySummary,
  gaps,
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

  const measurementBasis =
    gaps.opportunities.find(
      (item) =>
        item.evidence
          ?.measurement_basis,
    )?.evidence
      ?.measurement_basis ??
    "unknown";

  const benchmarkMode =
    gaps.opportunities.find(
      (item) =>
        item.evidence
          ?.benchmark_mode,
    )?.evidence
      ?.benchmark_mode ??
    visibilitySummary.benchmark_mode;

  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Prompt Gaps"
    >
      <div className="mx-auto max-w-7xl space-y-6 p-5 lg:p-8">
        <section>
          <div>
            <div className="text-sm text-slate-500">
              Prompt opportunity intelligence
            </div>

            <h2 className="mt-1 text-xl font-semibold text-white">
              {gaps.target_brand}
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              {gaps.total_prompts} measured prompts ·{" "}
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
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="font-semibold text-white">
              Gap Distribution
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Current prompt visibility state.
            </p>

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
                              "#f43f5e",
                              "#f59e0b",
                              "#34d399",
                            ][index]
                          }
                        />
                      ),
                    )}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      background: "#020617",
                      border:
                        "1px solid #1e293b",
                      borderRadius: "12px",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {gapDistribution.map(
                (item) => (
                  <div
                    key={item.name}
                    className="rounded-xl border border-slate-800 bg-slate-950/50 p-3"
                  >
                    <div className="text-lg font-semibold text-white">
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

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="font-semibold text-white">
              Prompt Categories
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Opportunity distribution by prompt category.
            </p>

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
                    stroke="#1e293b"
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

                  <Bar
                    dataKey="value"
                    fill="#22d3ee"
                    radius={[0, 5, 5, 0]}
                    name="Prompts"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 p-5 lg:p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-white">
                  Priority Opportunities
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Grounded prompt-level visibility gaps
                  ordered by opportunity score.
                </p>
              </div>

              <Radar className="h-5 w-5 text-slate-600" />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[1100px] text-left">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
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
                      className="border-b border-slate-800/70 align-top last:border-0"
                    >
                      <td className="max-w-md px-6 py-5">
                        <div className="font-medium leading-6 text-slate-200">
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
                        <span className="whitespace-nowrap rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-300">
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

                      <td className="px-4 py-5 text-sm font-medium text-slate-300">
                        {item.target_mention_rate.toFixed(
                          0,
                        )}
                        %
                      </td>

                      <td className="px-4 py-5 text-sm text-slate-300">
                        {item.top_competitor_name ??
                          "—"}
                      </td>

                      <td className="px-4 py-5 text-sm text-slate-300">
                        {item.top_competitor_run_coverage.toFixed(
                          0,
                        )}
                        %
                      </td>

                      <td className="px-4 py-5">
                        <span className="text-lg font-semibold text-cyan-300">
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
        </section>

        <section className="rounded-2xl border border-cyan-500/15 bg-cyan-500/5 p-6">
          <div className="flex gap-4">
            <div className="mt-0.5 rounded-xl bg-cyan-400/10 p-2.5">
              {gaps.covered_prompts ===
              gaps.total_prompts ? (
                <CircleCheck className="h-5 w-5 text-emerald-400" />
              ) : (
                <SearchX className="h-5 w-5 text-cyan-400" />
              )}
            </div>

            <div>
              <h2 className="font-semibold text-white">
                Measurement basis
              </h2>

              <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
                For this web-search experiment, target
                and competitor presence require both a
                resolved textual brand mention and
                same-brand first-party source retrieval
                in the same response.
              </p>

              <p className="mt-2 text-xs text-slate-500">
                Competitor pressure depends on the
                completeness of registered first-party
                domain mappings.
              </p>
            </div>
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}
