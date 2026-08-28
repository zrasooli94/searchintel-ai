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
import { technicalSEOPageState } from "@/lib/technical-seo-state";


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


export default function TechnicalSEODashboard({
  visibilitySummary,
  seo,
}: Props) {
  if (technicalSEOPageState(seo) === "limited") {
    return (
      <DashboardShell
        summary={visibilitySummary}
        title="Technical SEO"
      >
        <div className="crystal-page mx-auto max-w-[1100px] p-5 lg:p-8 xl:px-10">
          <section className="crystal-panel rounded-[24px] p-6 lg:p-8">
            <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
              <div className="max-w-2xl">
                <div className="crystal-eyebrow">Bounded crawl measurement</div>
                <div className="mt-3 inline-flex rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-amber-700">
                  Limited
                </div>
                <h2 className="mt-5 text-2xl font-medium tracking-[-0.035em] text-slate-950">
                  SearchIntel could not complete a technical audit for {seo.website.domain}
                </h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  {seo.measurement_reason}
                </p>
              </div>
              <div className="crystal-icon h-12 w-12 bg-amber-50 text-amber-600">
                <TriangleAlert className="h-5 w-5" />
              </div>
            </div>

            <div className="mt-7 grid gap-4 md:grid-cols-3">
              <MetricCard label="Measurement Status" value="LIMITED" detail="No complete technical audit is available" icon={Gauge} />
              <MetricCard label="Usable Pages" value="0" detail="No pages were available to score" icon={Globe2} />
              <MetricCard label="Technical Score" value="N/A" detail="SearchIntel does not manufacture a score" icon={SearchCheck} />
            </div>

            <div className="mt-7 rounded-[20px] border border-amber-200/80 bg-amber-50/60 p-5">
              <h3 className="font-medium text-slate-950">What this limitation means</h3>
              <p className="mt-2 text-sm leading-7 text-slate-600">{seo.limitation_note}</p>
            </div>

            <div className="mt-6 rounded-[20px] border border-slate-200 bg-white/70 p-5">
              <h3 className="font-medium text-slate-950">Recommended measurement paths</h3>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                Use Memory to measure latent model knowledge and Web Search to measure controlled live-web retrieval, source exposure, and citations. These remain separate from SearchIntel&apos;s bounded technical crawl.
              </p>
            </div>
          </section>
        </div>
      </DashboardShell>
    );
  }

  const audit = seo.audit;
  if (!audit) return null;

  return (
    <DashboardShell
      summary={visibilitySummary}
      title="Technical SEO"
    >
      <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
        <section>
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <div className="crystal-eyebrow">
                Website health
              </div>

              <h2 className="mt-2 text-2xl font-medium tracking-[-0.035em] text-slate-950">
                {seo.website.domain}
              </h2>
            </div>

            <a
              href={seo.website.base_url}
              target="_blank"
              rel="noreferrer"
              className="crystal-secondary-button px-3.5 py-2 text-sm"
            >
              Open website
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Site Health"
              value={`${audit.score}/100`}
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
              value={`${audit.issue_count}`}
              detail={`${audit.high_issues} high · ${audit.medium_issues} medium · ${audit.low_issues} low`}
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

        <section className="crystal-panel rounded-[22px]">
          <div className="p-5 pb-4 lg:p-6 lg:pb-4">
            <h2 className="font-semibold text-slate-950">
              Crawled Pages
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Latest stored crawl for the target website.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left">
              <thead>
                <tr className="border-y border-slate-200/70 bg-slate-50/55 text-[11px] uppercase tracking-[0.1em] text-slate-500">
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
                    className="border-b border-slate-200/65 transition hover:bg-slate-50/55 last:border-0"
                  >
                    <td className="px-6 py-5">
                      <div className="max-w-xl">
                        <a
                          href={page.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-medium text-slate-900 transition hover:text-violet-700"
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

                    <td className="px-4 py-5 text-sm text-slate-700">
                      {page.word_count}
                    </td>

                    <td className="px-4 py-5 text-sm text-slate-700">
                      {page.internal_link_count}
                    </td>

                    <td className="px-4 py-5 text-sm text-slate-700">
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
          <div className="crystal-panel rounded-[22px] p-6">
            <h2 className="font-semibold text-slate-950">
              Technical Checks
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Results from the latest audit only.
            </p>

            <div className="mt-6 space-y-3">
              {seo.checks.map((check) => (
                <div
                  key={check.key}
                  className="crystal-subcard flex items-center justify-between rounded-2xl px-4 py-3.5"
                >
                  <div className="flex items-center gap-3">
                    {check.status === "passed" ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <CircleAlert className="h-4 w-4 text-amber-400" />
                    )}

                    <span className="text-sm text-slate-700">
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

          <div className="crystal-panel rounded-[22px] p-6">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-slate-950">
                  Recommendations
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Generated from the latest audit.
                </p>
              </div>

              <FileText className="h-5 w-5 text-slate-400" />
            </div>

            {seo.recommendations.length === 0 ? (
              <div className="mt-8 rounded-[20px] border border-emerald-200/80 bg-emerald-50/65 p-6">
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />

                <h3 className="mt-4 font-medium text-slate-950">
                  No active technical recommendations
                </h3>

                <p className="mt-2 text-sm leading-7 text-slate-600">
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
                      className="crystal-subcard rounded-[18px] p-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="font-medium text-slate-950">
                            {recommendation.title}
                          </div>

                          <div className="mt-2 text-sm leading-7 text-slate-600">
                            {
                              recommendation.recommendation
                            }
                          </div>
                        </div>

                        <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">
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
