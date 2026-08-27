import {
  BookOpenCheck,
  FileSearch,
  Layers3,
  ShieldCheck,
} from "lucide-react";

import type {
  SiteRAGActionBridgeSummary,
} from "@/lib/types";


type Props = {
  data: SiteRAGActionBridgeSummary | null;
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


function pretty(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


export default function SiteRAGActionPlanPanel({
  data,
}: Props) {
  if (!data) {
    return null;
  }

  return (
    <section className="space-y-5">
      <div>
        <div className="crystal-eyebrow">
          Current first-party evidence actions
        </div>

        <h2 className="mt-2 text-xl font-medium tracking-[-0.025em] text-slate-950">
          Site RAG Action Bridge
        </h2>

        <p className="mt-1.5 text-sm leading-6 text-slate-500">
          Deterministic actions derived from the latest
          persisted Site RAG evidence gaps. They are kept
          separate from the historical GEO strategy.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="crystal-card rounded-[20px] p-5">
          <BookOpenCheck className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {percent(
              data.answerability_rate,
            )}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Site Answerability V1
          </div>
        </div>

        <div className="crystal-card rounded-[20px] p-5">
          <FileSearch className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {data.gap_prompts}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Evidence Gap Prompts
          </div>
        </div>

        <div className="crystal-card rounded-[20px] p-5">
          <ShieldCheck className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {data.covered_prompts}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Covered Prompts
          </div>
        </div>

        <div className="crystal-card rounded-[20px] p-5">
          <Layers3 className="h-5 w-5 text-indigo-500" />

          <div className="crystal-value mt-5 text-3xl font-medium">
            {data.actions.length}
          </div>

          <div className="mt-2 text-xs text-slate-500">
            Consolidated Actions
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {data.actions.map(
          (action, index) => (
            <details
              key={action.gap_type}
              open={index === 0}
              className="group crystal-card overflow-hidden rounded-[22px]"
            >
              <summary className="cursor-pointer list-none p-5 lg:p-6">
                <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
                  <div className="flex min-w-0 gap-4">
                    <div className="crystal-step-badge">
                      {index + 1}
                    </div>

                    <div className="min-w-0">
                      <h3 className="text-[15px] font-medium leading-6 text-slate-950">
                        {action.title}
                      </h3>

                      <div className="mt-2 flex flex-wrap gap-2">
                        <span className="rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-medium capitalize text-red-700">
                          {action.priority}
                        </span>

                        <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-xs text-indigo-700">
                          {pretty(
                            action.gap_type,
                          )}
                        </span>

                        <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-500">
                          {action.gap_count}
                          {" "}
                          gaps
                        </span>

                        <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-500">
                          {action.impacted_prompt_ids.length}
                          {" "}
                          prompts
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="shrink-0 rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-3">
                    <div className="text-[11px] uppercase tracking-[0.1em] text-slate-500">
                      Gap Score
                    </div>

                    <div className="mt-1 text-xl font-semibold text-indigo-600">
                      {action.gap_score.toFixed(0)}
                    </div>
                  </div>
                </div>
              </summary>

              <div className="border-t border-slate-200/70 bg-slate-50/25 px-5 pb-6 pt-5 lg:px-6">
                <div className="grid gap-6 xl:grid-cols-2">
                  <div>
                    <div className="crystal-eyebrow">
                      Why this action
                    </div>

                    <p className="mt-3 text-sm leading-7 text-slate-700">
                      {action.rationale}
                    </p>

                    <div className="mt-5 text-xs text-slate-500">
                      Prompt IDs:{" "}
                      {action.impacted_prompt_ids.join(
                        ", ",
                      )}
                    </div>

                    <div className="mt-1 text-xs text-slate-500">
                      Gap IDs:{" "}
                      {action.impacted_gap_ids.join(
                        ", ",
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="crystal-eyebrow">
                      Implementation
                    </div>

                    <ol className="mt-3 space-y-2">
                      {action.implementation_steps.map(
                        (step, stepIndex) => (
                          <li
                            key={stepIndex}
                            className="flex gap-3 text-sm leading-6 text-slate-700"
                          >
                            <span className="font-medium text-indigo-600">
                              {stepIndex + 1}.
                            </span>

                            <span>
                              {step}
                            </span>
                          </li>
                        ),
                      )}
                    </ol>
                  </div>
                </div>

                <div className="mt-6 grid gap-5 lg:grid-cols-3">
                  <div className="crystal-subcard rounded-[18px] p-4">
                    <div className="font-medium text-slate-900">
                      Evidence
                    </div>

                    <ul className="mt-3 space-y-2">
                      {action.evidence.map(
                        (item, itemIndex) => (
                          <li
                            key={itemIndex}
                            className="text-xs leading-5 text-slate-600"
                          >
                            • {item}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>

                  <div className="crystal-subcard rounded-[18px] p-4">
                    <div className="font-medium text-slate-900">
                      Success Metrics
                    </div>

                    <ul className="mt-3 space-y-2">
                      {action.success_metrics.map(
                        (item, itemIndex) => (
                          <li
                            key={itemIndex}
                            className="text-xs leading-5 text-slate-600"
                          >
                            • {item}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>

                  <div className="crystal-subcard rounded-[18px] p-4">
                    <div className="font-medium text-slate-900">
                      Dependencies
                    </div>

                    <ul className="mt-3 space-y-2">
                      {action.dependencies.map(
                        (item, itemIndex) => (
                          <li
                            key={itemIndex}
                            className="text-xs leading-5 text-slate-600"
                          >
                            • {item}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            </details>
          ),
        )}
      </div>

      <div className="rounded-[20px] border border-indigo-200/70 bg-indigo-50/55 p-5 text-xs leading-6 text-slate-600">
        {data.provenance_note}
      </div>
    </section>
  );
}
