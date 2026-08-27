import {
  Database,
  FileText,
  Layers3,
} from "lucide-react";

import type {
  ExperimentsSummary,
} from "@/lib/types";


type Props = {
  experiments: ExperimentsSummary;
};


function percent(
  value: number | null,
) {
  if (value === null) {
    return "N/A";
  }

  return `${value.toFixed(2)}%`;
}


function value(
  metric: number | null,
) {
  if (metric === null) {
    return "N/A";
  }

  return metric.toFixed(2);
}


export default function SiteRAGExperimentsPanel({
  experiments,
}: Props) {
  const siteRagExperiments =
    experiments.experiments.filter(
      (experiment) =>
        experiment.benchmark_mode
        === "site_rag",
    );

  return (
    <section className="crystal-panel rounded-[22px] p-6">
      <div className="flex items-start justify-between gap-5">
        <div>
          <div className="crystal-eyebrow">
            First-party evidence
          </div>

          <h2 className="mt-2 font-semibold text-slate-950">
            Site RAG Experiments
          </h2>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Measures whether crawled target-site
            evidence can support grounded answers
            to the controlled prompt set.
          </p>
        </div>

        <div className="crystal-icon h-10 w-10">
          <Database className="h-[18px] w-[18px] text-[#5f75ff]" />
        </div>
      </div>

      {siteRagExperiments.length === 0 ? (
        <div className="mt-6 crystal-subcard rounded-[18px] p-5">
          <div className="text-sm font-medium text-slate-800">
            No formal Site RAG experiment yet
          </div>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            The engineering execution test remains
            excluded from formal measurement.
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          {siteRagExperiments.map(
            (experiment) => (
              <div
                key={experiment.id}
                className="border-t border-slate-200/70 pt-6 first:border-t-0 first:pt-0"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="text-lg font-semibold text-slate-950">
                      {experiment.name}
                    </div>

                    <div className="mt-1 text-xs text-slate-500">
                      {experiment.site_rag_analyzed_runs}
                      {" analyzed runs · "}
                      {experiment.site_rag_analyzed_prompts}
                      {" prompts"}
                    </div>
                  </div>

                  <div className="rounded-lg bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">
                    site_rag
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <Metric
                    label="Answerability"
                    value={percent(
                      experiment
                        .site_answerability_rate_v1,
                    )}
                    detail="Heuristic supported-answer rate"
                  />

                  <Metric
                    label="Evidence coverage"
                    value={percent(
                      experiment
                        .evidence_coverage_rate,
                    )}
                    detail="Responses with retrieved first-party evidence"
                  />

                  <Metric
                    label="Source references"
                    value={percent(
                      experiment
                        .source_reference_rate,
                    )}
                    detail="Responses referencing valid [Source N]"
                  />

                  <Metric
                    label="Evidence utilization"
                    value={percent(
                      experiment
                        .evidence_utilization_rate,
                    )}
                    detail="Retrieved passages actually referenced"
                  />

                  <Metric
                    label="Supporting pages"
                    value={`${experiment.unique_supporting_pages}`}
                    detail={`${experiment.unique_supporting_urls} unique URLs`}
                  />

                  <Metric
                    label="Avg. sources"
                    value={value(
                      experiment
                        .avg_sources_per_response,
                    )}
                    detail="Retrieved passages per analyzed response"
                  />
                </div>

                <div className="mt-5 crystal-subcard rounded-[18px] p-4">
                  <div className="flex items-center gap-2">
                    <Layers3 className="h-4 w-4 text-[#5f75ff]" />

                    <div className="text-sm font-medium text-slate-800">
                      Top supporting pages
                    </div>
                  </div>

                  {experiment
                    .top_supporting_pages
                    .length === 0 ? (
                    <p className="mt-3 text-sm text-slate-500">
                      No referenced supporting pages yet.
                    </p>
                  ) : (
                    <div className="mt-3 divide-y divide-slate-200/70">
                      {experiment
                        .top_supporting_pages
                        .slice(0, 5)
                        .map(
                          (page) => (
                            <div
                              key={[
                                page.page_id,
                                page.url,
                              ].join("-")}
                              className="flex items-start gap-3 py-3 first:pt-0 last:pb-0"
                            >
                              <FileText className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />

                              <div className="min-w-0 flex-1">
                                <div className="truncate text-sm font-medium text-slate-800">
                                  {page.title
                                    || page.url}
                                </div>

                                <div className="mt-1 truncate text-xs text-slate-500">
                                  {page.url}
                                </div>
                              </div>

                              <div className="shrink-0 text-right">
                                <div className="text-sm font-medium text-slate-800">
                                  {page.reference_count}
                                </div>

                                <div className="text-[11px] text-slate-400">
                                  references
                                </div>
                              </div>
                            </div>
                          ),
                        )}
                    </div>
                  )}
                </div>

                <p className="mt-4 text-xs leading-5 text-slate-500">
                  Site answerability is a deterministic
                  benchmark heuristic for this controlled
                  Site RAG workflow, not a universal
                  search-engine or consumer-AI metric.
                </p>
              </div>
            ),
          )}
        </div>
      )}
    </section>
  );
}


function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="crystal-subcard rounded-2xl p-4">
      <div className="text-xs text-slate-500">
        {label}
      </div>

      <div className="crystal-value mt-2 text-xl font-medium">
        {value}
      </div>

      <div className="mt-2 text-xs leading-5 text-slate-400">
        {detail}
      </div>
    </div>
  );
}
