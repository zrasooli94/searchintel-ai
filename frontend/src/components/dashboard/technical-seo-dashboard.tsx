import {
  CheckCircle2,
  CircleAlert,
  ExternalLink,
  FileText,
  Gauge,
  Globe2,
  Link2,
  SearchCheck,
  TriangleAlert,
} from "lucide-react";

import DashboardShell from "@/components/dashboard/dashboard-shell";

import type {
  TechnicalSEOSummary,
  VisibilitySummary,
} from "@/lib/types";


type Props = {
  visibilitySummary: VisibilitySummary;
  seo: TechnicalSEOSummary;
};


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


export default function TechnicalSEODashboard({
  visibilitySummary,
  seo,
}: Props) {
  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Technical SEO"
    >
      <div className="mx-auto max-w-7xl space-y-6 p-5 lg:p-8">
        <section>
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <div className="text-sm text-slate-500">
                Website health
              </div>

              <h2 className="mt-1 text-xl font-semibold text-white">
                {seo.website.domain}
              </h2>
            </div>

            <a
              href={seo.website.base_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300"
            >
              Open website
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Site Health"
              value={`${seo.audit.score}/100`}
              detail="SearchIntel Technical Audit V1"
              icon={Gauge}
            />

            <MetricCard
              label="Crawled Pages"
              value={`${seo.crawled_pages}`}
              detail={`${seo.successful_pages} successful · ${seo.failed_pages} failed`}
              icon={Globe2}
            />

            <MetricCard
              label="Current Issues"
              value={`${seo.audit.issue_count}`}
              detail={`${seo.audit.high_issues} high · ${seo.audit.medium_issues} medium · ${seo.audit.low_issues} low`}
              icon={TriangleAlert}
            />

            <MetricCard
              label="Recommendations"
              value={`${seo.recommendation_count}`}
              detail="From latest technical audit"
              icon={SearchCheck}
            />
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/60">
          <div className="border-b border-slate-800 p-5 lg:p-6">
            <h2 className="font-semibold text-white">
              Crawled Pages
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Latest stored crawl for the target website.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-4">
                    Page
                  </th>

                  <th className="px-4 py-4">
                    Status
                  </th>

                  <th className="px-4 py-4">
                    Words
                  </th>

                  <th className="px-4 py-4">
                    Internal
                  </th>

                  <th className="px-4 py-4">
                    External
                  </th>

                  <th className="px-4 py-4">
                    Canonical
                  </th>
                </tr>
              </thead>

              <tbody>
                {seo.pages.map((page) => (
                  <tr
                    key={page.id}
                    className="border-b border-slate-800/70 last:border-0"
                  >
                    <td className="px-6 py-5">
                      <div className="max-w-xl">
                        <a
                          href={page.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-medium text-slate-200 hover:text-cyan-300"
                        >
                          {page.path}
                        </a>

                        <div className="mt-1 truncate text-xs text-slate-500">
                          {page.title ?? "No title"}
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-5">
                      <span
                        className={[
                          "rounded-lg px-2.5 py-1 text-xs font-medium",
                          page.status_code !== null &&
                          page.status_code >= 200 &&
                          page.status_code < 400
                            ? "bg-emerald-500/10 text-emerald-300"
                            : "bg-red-500/10 text-red-300",
                        ].join(" ")}
                      >
                        {page.status_code ?? "N/A"}
                      </span>
                    </td>

                    <td className="px-4 py-5 text-sm text-slate-300">
                      {page.word_count}
                    </td>

                    <td className="px-4 py-5 text-sm text-slate-300">
                      {page.internal_link_count}
                    </td>

                    <td className="px-4 py-5 text-sm text-slate-300">
                      {page.external_link_count}
                    </td>

                    <td className="px-4 py-5">
                      {page.canonical_url ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <CircleAlert className="h-4 w-4 text-amber-400" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1.25fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <h2 className="font-semibold text-white">
              Technical Checks
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Results from the latest audit only.
            </p>

            <div className="mt-6 space-y-3">
              {seo.checks.map((check) => (
                <div
                  key={check.key}
                  className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/50 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    {check.status === "passed" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <CircleAlert className="h-4 w-4 text-amber-400" />
                    )}

                    <span className="text-sm text-slate-300">
                      {check.label}
                    </span>
                  </div>

                  <span
                    className={[
                      "text-xs font-medium",
                      check.status === "passed"
                        ? "text-emerald-400"
                        : "text-amber-400",
                    ].join(" ")}
                  >
                    {check.status === "passed"
                      ? "Passed"
                      : `${check.issue_count} issue${
                          check.issue_count === 1
                            ? ""
                            : "s"
                        }`}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-white">
                  Recommendations
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Generated from the latest audit.
                </p>
              </div>

              <FileText className="h-5 w-5 text-slate-600" />
            </div>

            {seo.recommendations.length === 0 ? (
              <div className="mt-8 rounded-2xl border border-emerald-500/15 bg-emerald-500/5 p-6">
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />

                <h3 className="mt-4 font-medium text-white">
                  No active technical recommendations
                </h3>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                  The latest audit produced no rule-based
                  technical SEO issues.
                </p>
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                {seo.recommendations.map(
                  (recommendation) => (
                    <div
                      key={recommendation.id}
                      className="rounded-xl border border-slate-800 bg-slate-950/50 p-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="font-medium text-white">
                            {recommendation.title}
                          </div>

                          <div className="mt-2 text-sm leading-6 text-slate-400">
                            {
                              recommendation.recommendation
                            }
                          </div>
                        </div>

                        <span className="rounded-lg bg-amber-500/10 px-2.5 py-1 text-xs text-amber-300">
                          {recommendation.priority}
                        </span>
                      </div>
                    </div>
                  ),
                )}
              </div>
            )}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard
            label="Total Content"
            value={seo.total_words.toLocaleString()}
            detail="Words across crawled pages"
            icon={FileText}
          />

          <MetricCard
            label="Average Page Depth"
            value={seo.average_word_count.toFixed(0)}
            detail="Average words per crawled page"
            icon={SearchCheck}
          />

          <MetricCard
            label="Primary Domain"
            value={
              seo.website.is_primary
                ? "Yes"
                : "No"
            }
            detail={seo.website.domain}
            icon={Link2}
          />
        </section>
      </div>
    </DashboardShell>
  );
}
