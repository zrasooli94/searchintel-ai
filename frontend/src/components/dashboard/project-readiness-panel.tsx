"use client";

import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  CircleSlash2,
  Loader2,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type {
  MeasurementEligibility,
  ProjectReadiness,
  ReadinessSuggestion,
  ReadinessState,
} from "@/lib/types";


const modeLabels = {
  technical_seo: "Technical SEO",
  memory: "Memory",
  web_search: "Web Search",
  site_rag: "Site RAG",
};

const modeDescriptions = {
  technical_seo: "Bounded SearchIntel crawl and technical audit capability.",
  memory: "Latent model knowledge without live-web retrieval.",
  web_search: "Controlled API web-search retrieval and citation evidence.",
  site_rag: "Answerability using only stored first-party crawl evidence.",
};

const stateStyles: Record<ReadinessState, string> = {
  ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
  needs_review: "border-amber-200 bg-amber-50 text-amber-700",
  limited: "border-orange-200 bg-orange-50 text-orange-700",
  blocked: "border-red-200 bg-red-50 text-red-700",
  not_applicable: "border-slate-200 bg-slate-100 text-slate-600",
};


function StatusIcon({ state }: { state: ReadinessState }) {
  if (state === "ready") {
    return <CheckCircle2 className="h-4 w-4" />;
  }
  if (state === "blocked") {
    return <CircleSlash2 className="h-4 w-4" />;
  }
  return <TriangleAlert className="h-4 w-4" />;
}


function ModeCard({ item }: { item: MeasurementEligibility }) {
  return (
    <article className="crystal-subcard rounded-[18px] p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium text-slate-950">
            {modeLabels[item.mode]}
          </h3>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {modeDescriptions[item.mode]}
          </p>
        </div>
        <div className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${stateStyles[item.state]}`}>
          <StatusIcon state={item.state} />
          {item.state.replace("_", " ")}
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-700">
        {item.reason}
      </p>
      {item.has_historical_results && (
        <p className="mt-3 rounded-lg bg-blue-50 px-3 py-2 text-xs leading-5 text-blue-700">
          Historical results remain available even if a future run needs configuration work.
        </p>
      )}
      {(item.blocking_issues.length > 0 || item.warnings.length > 0) && (
        <ul className="mt-4 space-y-2 text-xs leading-5 text-slate-600">
          {[...item.blocking_issues, ...item.warnings].slice(0, 3).map((issue) => (
            <li key={issue.code} className="flex gap-2">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
              {issue.message}
            </li>
          ))}
        </ul>
      )}
      <div className="mt-4 border-t border-slate-200/70 pt-4">
        <div className="flex gap-2 text-xs font-medium text-slate-700">
          <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-violet-500" />
          {item.recommended_action}
        </div>
        {!item.execution_available && item.mode !== "technical_seo" && (
          <p className="mt-2 text-xs leading-5 text-amber-700">
            {item.execution_note}
          </p>
        )}
      </div>
    </article>
  );
}


export default function ProjectReadinessPanel({
  readiness,
  operatorAuthorized,
}: {
  readiness: ProjectReadiness;
  operatorAuthorized: boolean;
}) {
  const router = useRouter();
  const [dismissed, setDismissed] = useState<string[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const visibleSuggestions = readiness.suggestions.filter(
    (item) => !dismissed.includes(item.key),
  );

  async function approve(suggestion: ReadinessSuggestion) {
    if (!operatorAuthorized) {
      setError("Unlock operator controls before approving configuration changes.");
      return;
    }
    if (suggestion.kind === "prompt_category") {
      document.getElementById("prompt-set")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
      setDismissed((items) => [...items, suggestion.key]);
      return;
    }

    setPending(suggestion.key);
    setError(null);
    try {
      let response: Response;
      if (suggestion.kind === "first_party_domain") {
        if (readiness.configuration.target_brand_id === null) {
          throw new Error("Confirm the target brand first.");
        }
        response = await fetch(
          `/api/brands/${readiness.configuration.target_brand_id}/websites`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              base_url: `https://${suggestion.value}`,
              is_primary: false,
            }),
          },
        );
      } else if (suggestion.kind === "competitor") {
        response = await fetch(
          `/api/projects/${readiness.project_id}/competitors`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: suggestion.value,
              website_url: null,
            }),
          },
        );
      } else {
        throw new Error("Unsupported suggestion type.");
      }
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(typeof payload?.detail === "string" ? payload.detail : "Could not approve suggestion.");
      }
      router.refresh();
    } catch (approvalError) {
      setError(approvalError instanceof Error ? approvalError.message : "Could not approve suggestion.");
    } finally {
      setPending(null);
    }
  }

  return (
    <section className="crystal-panel rounded-[22px]">
      <div className="border-b border-slate-200/80 p-6">
        <div className="flex items-start justify-between gap-5">
          <div className="flex gap-4">
            <div className="crystal-step-badge">1</div>
            <div>
              <h2 className="font-semibold text-slate-950">Identity & Measurement Readiness</h2>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
                SearchIntel checks stored configuration and evidence before any crawl, web search, or AI run starts.
              </p>
            </div>
          </div>
          <div className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold uppercase ${stateStyles[readiness.overall_state]}`}>
            <ShieldCheck className="h-4 w-4" />
            {readiness.overall_state.replace("_", " ")}
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid gap-4 md:grid-cols-2">
          {Object.values(readiness.measurements).map((item) => (
            <ModeCard key={item.mode} item={item} />
          ))}
        </div>

        {visibleSuggestions.length > 0 && (
          <div className="mt-6 rounded-[18px] border border-violet-200/70 bg-violet-50/40 p-5">
            <h3 className="font-medium text-slate-950">Suggestions requiring approval</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Suggestions come only from stored project evidence. SearchIntel will not change identity, competitors, or prompts automatically.
            </p>
            <div className="mt-4 space-y-3">
              {visibleSuggestions.slice(0, 8).map((suggestion) => (
                <div key={suggestion.key} className="rounded-xl border border-slate-200/80 bg-white p-4">
                  <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-wide text-violet-600">
                        {suggestion.kind.replaceAll("_", " ")}
                      </div>
                      <div className="mt-1 font-medium text-slate-950">{suggestion.value}</div>
                      <p className="mt-1 text-xs leading-5 text-slate-600">{suggestion.reason}</p>
                      <p className="mt-1 text-xs leading-5 text-slate-400">{suggestion.evidence.join(" ")}</p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <button type="button" onClick={() => setDismissed((items) => [...items, suggestion.key])} className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50">
                        Ignore
                      </button>
                      <button type="button" disabled={pending !== null || !operatorAuthorized} onClick={() => approve(suggestion)} className="crystal-primary-button px-3 py-2 text-xs disabled:cursor-not-allowed disabled:opacity-50">
                        {pending === suggestion.key && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                        {!operatorAuthorized ? "Operator only" : suggestion.kind === "prompt_category" ? "Review" : "Approve"}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <p className="mt-5 text-xs leading-5 text-slate-400">{readiness.provenance_note}</p>
      </div>
    </section>
  );
}
