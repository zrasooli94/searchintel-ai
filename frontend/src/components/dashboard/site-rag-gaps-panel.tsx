import {
  BookOpenCheck,
  Database,
  FileSearch,
  Link2,
  ShieldAlert,
  TriangleAlert,
} from "lucide-react";

import type {
  SiteRAGGapSummary,
} from "@/lib/types";


type Props = {
  gaps: SiteRAGGapSummary | null;
};


function percent(
  value: number | null,
) {
  if (value === null) {
    return "—";
  }

  return `${value.toFixed(2).replace(
    /\.00$/,
    "",
  )}%`;
}


function prettyLabel(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}


function priorityClasses(
  priority: string,
) {
  if (priority === "high") {
    return (
      "border border-red-200 "
      + "bg-red-50 text-red-700"
    );
  }

  if (priority === "medium") {
    return (
      "border border-amber-200 "
      + "bg-amber-50 text-amber-700"
    );
  }

  return (
    "border border-slate-200 "
    + "bg-slate-50 text-slate-600"
  );
}


export default function SiteRAGGapsPanel({
  gaps,
}: Props) {
  if (!gaps) {
    return (
      <section className="crystal-panel rounded-[22px] p-6">
        <div className="flex items-start gap-4">
          <div className="crystal-icon h-11 w-11 shrink-0">
            <Database className="h-5 w-5 text-indigo-500" />
          </div>

          <div>
            <div className="crystal-eyebrow">
              First-Party Answerability
            </div>

            <h2 className="mt-2 font-semibold text-slate-950">
              No Site RAG baseline yet
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Run a completed Site RAG benchmark to measure
              which prompts can be supported by the crawled
              first-party website evidence.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-5">
      <div>
        <div className="crystal-eyebrow">
          First-Party Answerability
        </div>

        <div className="mt-2 flex flex-col justify-between gap-3 lg:flex-row lg:items-end">
          <div>
            <h2 className="text-2xl font-medium tracking-[-0.035em] text-slate-950">
              Site RAG Evidence Gaps
            </h2>

            <p className="mt-1.5 text-sm text-slate-500">
              {gaps.target_brand}
              {" · "}
              {gaps.total_prompts}
              {" prompts · "}
              controlled first-party evidence only
            </p>
          </div>

          <div className="rounded-xl border border-indigo-200/80 bg-indigo-50/70 px-3 py-2 text-xs font-medium text-indigo-700">
            site_rag · first_party_answerability
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <div className="crystal-card rounded-[20px] p-5">
          <BookOpenCheck className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {percent(
              gaps.site_answerability_rate_v1,
            )}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Site Answerability V1
          </div>
        </div>

        <div className="crystal-card rounded-[20px] p-5">
          <ShieldAlert className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {gaps.analysis_status === "completed" ? gaps.gap_prompts : "—"}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Evidence Gap Prompts
          </div>
        </div>

        <div className="crystal-card rounded-[20px] p-5">
          <TriangleAlert className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {gaps.analysis_status === "completed" ? gaps.high_priority : "—"}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            High Priority
          </div>
        </div>

        <div className="crystal-card rounded-[20px] p-5">
          <FileSearch className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {percent(
              gaps.evidence_coverage_rate,
            )}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Evidence Coverage
          </div>
        </div>

        <div className="crystal-card rounded-[20px] p-5">
          <Link2 className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {percent(
              gaps.evidence_utilization_rate,
            )}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Evidence Utilization
          </div>
        </div>
      </div>

      <div className="crystal-panel rounded-[22px]">
        <div className="border-b border-slate-200/80 p-5 lg:p-6">
          <h3 className="font-semibold text-slate-950">
            First-Party Evidence Gaps
          </h3>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Prompts where the stored first-party evidence
            was insufficient for a fully grounded answer.
            These are not web-search visibility failures.
          </p>
        </div>

        {gaps.analysis_status === "pending" ? (
          <div className="px-6 py-12 text-center">
            <Database className="mx-auto h-6 w-6 text-indigo-500" />
            <h3 className="mt-4 font-medium text-slate-900">
              Evidence gap analysis pending
            </h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
              The Site RAG measurement is complete, but its deterministic evidence-gap analysis has not completed yet. Zero gaps are not assumed.
            </p>
          </div>
        ) : gaps.gaps.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <BookOpenCheck className="mx-auto h-6 w-6 text-emerald-500" />

            <h3 className="mt-4 font-medium text-slate-900">
              No first-party evidence gaps
            </h3>

            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
              The measured Site RAG prompts were answerable
              from the available crawled website evidence.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-200/70">
            {gaps.gaps.map(
              (item) => {
                const urls =
                  item.evidence.supporting_urls
                  ?? [];

                return (
                  <article
                    key={item.id}
                    className="p-5 lg:p-6"
                  >
                    <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                      <div className="max-w-4xl">
                        <div className="flex flex-wrap items-center gap-2">
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

                          <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs text-slate-700">
                            {prettyLabel(
                              item.gap_type,
                            )}
                          </span>

                          <span className="rounded-lg bg-indigo-50 px-2.5 py-1 text-xs text-indigo-700">
                            {prettyLabel(
                              item.category,
                            )}
                          </span>
                        </div>

                        <h4 className="mt-4 text-lg font-medium leading-7 text-slate-950">
                          {item.prompt_text}
                        </h4>

                        <p className="mt-3 text-sm leading-7 text-slate-600">
                          {item.recommendation}
                        </p>
                      </div>

                      <div className="shrink-0 rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-3">
                        <div className="text-[11px] uppercase tracking-[0.1em] text-slate-500">
                          Gap Score
                        </div>

                        <div className="mt-1 text-2xl font-semibold text-indigo-600">
                          {item.gap_score.toFixed(0)}
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="crystal-subcard rounded-2xl p-3.5">
                        <div className="text-xs text-slate-500">
                          Unsupported
                        </div>

                        <div className="mt-1 font-semibold text-slate-900">
                          {percent(
                            item.unsupported_rate,
                          )}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-3.5">
                        <div className="text-xs text-slate-500">
                          Retrieved passages
                        </div>

                        <div className="mt-1 font-semibold text-slate-900">
                          {item.evidence
                            .retrieved_source_count
                            ?? 0}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-3.5">
                        <div className="text-xs text-slate-500">
                          Referenced passages
                        </div>

                        <div className="mt-1 font-semibold text-slate-900">
                          {item.evidence
                            .referenced_source_count
                            ?? 0}
                        </div>
                      </div>

                      <div className="crystal-subcard rounded-2xl p-3.5">
                        <div className="text-xs text-slate-500">
                          Supporting URLs
                        </div>

                        <div className="mt-1 font-semibold text-slate-900">
                          {urls.length}
                        </div>
                      </div>
                    </div>

                    {urls.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {urls.map(
                          (url) => (
                            <span
                              key={url}
                              className="max-w-full truncate rounded-lg border border-slate-200 bg-white/75 px-2.5 py-1.5 text-xs text-slate-500"
                            >
                              {url}
                            </span>
                          ),
                        )}
                      </div>
                    )}
                  </article>
                );
              },
            )}
          </div>
        )}

        <div className="border-t border-slate-200/70 bg-slate-50/45 px-5 py-4 text-xs leading-5 text-slate-500 lg:px-6">
          Site Answerability V1 is a deterministic benchmark
          heuristic based on the stored Site RAG responses.
          It is not a web ranking, consumer-AI visibility,
          Google AI Overview, or indexing metric.
        </div>
      </div>
    </section>
  );
}
