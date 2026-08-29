"use client";

import {
  Bot,
  Check,
  ExternalLink,
  Loader2,
  Search,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type {
  CompetitorDiscoveryResult,
  CompetitorDiscoverySuggestion,
} from "@/lib/types";
import {
  canStartCompetitorDiscovery,
  competitorDiscoveryConfirmation,
} from "@/lib/competitor-discovery-state";


export default function SetupCompetitorDiscovery({
  projectId,
  targetBrand,
  operatorAuthorized,
  initialSuggestions,
}: {
  projectId: number;
  targetBrand: string;
  operatorAuthorized: boolean;
  initialSuggestions: CompetitorDiscoverySuggestion[];
}) {
  const router = useRouter();
  const [suggestions, setSuggestions] = useState(initialSuggestions);
  const [confirming, setConfirming] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [pending, setPending] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const visible = suggestions.filter((item) => item.status === "pending");
  const confirmation = competitorDiscoveryConfirmation(targetBrand);
  const canGenerate = canStartCompetitorDiscovery({ operatorAuthorized, generating });

  async function generate() {
    setGenerating(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/projects/${projectId}/competitor-discovery/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ max_candidates: 5 }),
        },
      );
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(typeof payload?.detail === "string" ? payload.detail : "Competitor discovery failed.");
      }
      const result = payload as CompetitorDiscoveryResult;
      setSuggestions((current) => {
        const retained = current.filter((item) => !result.suggestions.some((next) => next.id === item.id));
        return [...retained, ...result.suggestions];
      });
      setConfirming(false);
      router.refresh();
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "Competitor discovery failed.");
    } finally {
      setGenerating(false);
    }
  }

  async function decide(suggestion: CompetitorDiscoverySuggestion, action: "approve" | "ignore") {
    setPending(suggestion.id);
    setError(null);
    try {
      const response = await fetch(
        `/api/projects/${projectId}/competitor-discovery/${suggestion.id}/${action}`,
        { method: "POST" },
      );
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(typeof payload?.detail === "string" ? payload.detail : `Could not ${action} suggestion.`);
      }
      setSuggestions((items) => items.map((item) => item.id === suggestion.id ? payload.suggestion : item));
      router.refresh();
    } catch (decisionError) {
      setError(decisionError instanceof Error ? decisionError.message : `Could not ${action} suggestion.`);
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="rounded-[20px] border border-violet-200/80 bg-gradient-to-br from-violet-50/80 to-blue-50/60 p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 font-medium text-slate-950">
            <Bot className="h-4 w-4 text-violet-600" />
            AI Competitor Discovery
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Analyze the target brand, stored first-party evidence and controlled public research to suggest likely comparison brands.
          </p>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            Suggestions require human approval and do not create benchmark metrics.
          </p>
        </div>
        <button
          type="button"
          disabled={!canGenerate}
          onClick={() => setConfirming(true)}
          className="crystal-primary-button shrink-0 px-4 py-2.5 text-sm"
        >
          {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Generate Competitor Set
        </button>
      </div>

      {!operatorAuthorized && (
        <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          Unlock operator controls to run paid AI and web research or change project configuration.
        </p>
      )}

      {error && (
        <div className="mt-4 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {confirming && (
        <div className="mt-5 rounded-[18px] border border-violet-200 bg-white p-5 shadow-sm">
          <div className="font-medium text-slate-950">Generate Competitor Set</div>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <div><dt className="text-xs text-slate-400">Target</dt><dd className="mt-1 text-slate-800">{confirmation.target}</dd></div>
            <div><dt className="text-xs text-slate-400">Method</dt><dd className="mt-1 text-slate-800">{confirmation.method}</dd></div>
            <div><dt className="text-xs text-slate-400">Maximum candidates</dt><dd className="mt-1 text-slate-800">{confirmation.maxCandidates}</dd></div>
            <div><dt className="text-xs text-slate-400">Measurement impact</dt><dd className="mt-1 text-slate-800">{confirmation.createsBenchmarkMetrics ? "Creates benchmark metrics" : "No benchmark metrics"}</dd></div>
          </dl>
          <div className="mt-5 flex justify-end gap-3">
            <button type="button" onClick={() => setConfirming(false)} className="crystal-secondary-button px-4 py-2 text-sm">Cancel</button>
            <button type="button" disabled={generating} onClick={generate} className="crystal-primary-button px-4 py-2 text-sm">
              {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Generate
            </button>
          </div>
        </div>
      )}

      <div className="mt-6 flex items-center justify-between border-t border-violet-200/70 pt-5">
        <div className="font-medium text-slate-950">Suggested Competitors</div>
        <span className="rounded-full border border-violet-200 bg-white px-3 py-1 text-xs text-violet-700">
          {visible.length} awaiting review
        </span>
      </div>

      {visible.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No pending discovery suggestions.</p>
      ) : (
        <div className="mt-4 space-y-4">
          {visible.map((suggestion) => (
            <article key={suggestion.id} className="rounded-[18px] border border-slate-200 bg-white/90 p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="font-semibold text-slate-950">{suggestion.brand_name}</h3>
                  <a href={suggestion.website_url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs text-violet-700 hover:underline">
                    {suggestion.domain}<ExternalLink className="h-3 w-3" />
                  </a>
                </div>
                <div className="flex gap-2 text-[11px] font-semibold uppercase tracking-wide">
                  <span className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-blue-700">{suggestion.competitor_type}</span>
                  <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-emerald-700">{suggestion.confidence}</span>
                </div>
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-700">{suggestion.reason}</p>
              <div className="mt-4 space-y-2">
                {suggestion.evidence.map((evidence) => (
                  <div key={`${evidence.url}:${evidence.support}`} className="rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                    {evidence.support}
                    <a href={evidence.url} target="_blank" rel="noreferrer" className="mt-1 block break-all text-violet-700 hover:underline">{evidence.url}</a>
                  </div>
                ))}
              </div>
              <div className="mt-5 flex justify-end gap-3">
                <button type="button" disabled={pending !== null || !operatorAuthorized} onClick={() => decide(suggestion, "ignore")} className="crystal-secondary-button px-3.5 py-2 text-sm">
                  <X className="h-4 w-4" />Ignore
                </button>
                <button type="button" disabled={pending !== null || !operatorAuthorized} onClick={() => decide(suggestion, "approve")} className="crystal-primary-button px-3.5 py-2 text-sm">
                  {pending === suggestion.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}Approve
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
