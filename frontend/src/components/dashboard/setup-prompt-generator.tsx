"use client";

import { Bot, CheckCircle2, Loader2, Sparkles, TriangleAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import type { StarterPromptGenerationResult } from "@/lib/types";
import { canGeneratePromptProposal } from "@/lib/prompt-proposal";

type Props = {
  projectId: number;
  targetBrand: string;
  activePromptCount: number;
  initialProposal: StarterPromptGenerationResult | null;
  operatorAuthorized: boolean;
  initialScope: "brand_wide" | "focused";
  initialFocus: string | null;
  websitePageCount: number;
  competitorCount: number;
};

const pretty = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function SetupPromptGenerator(props: Props) {
  const router = useRouter();
  const [result, setResult] = useState(props.initialProposal);
  const [scope, setScope] = useState(props.initialScope);
  const [focus, setFocus] = useState(props.initialFocus ?? "");
  const [confirming, setConfirming] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const proposal = result?.status === "proposed" ? result : null;
  const topicEntries = useMemo(() => Object.entries(proposal?.coverage_blueprint.topic_distribution ?? {}), [proposal]);

  async function generate() {
    setGenerating(true); setError(null); setSuccess(null);
    try {
      const response = await fetch(`/api/projects/${props.projectId}/prompts/starter-generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count: 19, measurement_scope: scope, focus_label: scope === "focused" ? focus : null }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Prompt generation failed.");
      setResult(data); setConfirming(false);
      router.refresh();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Prompt generation failed."); }
    finally { setGenerating(false); }
  }

  async function applyProposal() {
    if (!proposal) return;
    setApplying(true); setError(null);
    try {
      const response = await fetch(`/api/projects/${props.projectId}/prompts/starter-proposals/${proposal.id}/apply`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompts: proposal.prompts }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Proposal approval failed.");
      setSuccess(`${data.active_prompt_count} prompts are now the active measurement set.`);
      setResult({ ...proposal, status: "approved" });
      router.refresh();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Proposal approval failed."); }
    finally { setApplying(false); }
  }

  function editPrompt(index: number, field: "text" | "category", value: string) {
    if (!proposal) return;
    const prompts = proposal.prompts.map((prompt, promptIndex) => (
      promptIndex === index ? { ...prompt, [field]: value } : prompt
    ));
    setResult({ ...proposal, prompts });
  }

  return (
    <div className="mb-6 rounded-xl border border-violet-200/80 bg-violet-50/60">
      <div className="border-b border-violet-100 p-5">
        <div className="flex items-start gap-3"><div className="rounded-xl bg-white p-2.5"><Bot className="h-5 w-5 text-[#5f75ff]" /></div>
          <div><div className="font-medium text-slate-950">AI Starter Prompt Generator</div>
            <p className="mt-1 text-xs leading-5 text-slate-500">Builds a reviewable coverage blueprint and prompt proposal from stored first-party crawl evidence. Generation does not run a benchmark.</p></div>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          <label className="text-xs font-medium text-slate-600">Measurement scope
            <select value={scope} onChange={(event) => setScope(event.target.value as typeof scope)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm">
              <option value="brand_wide">Brand-wide</option><option value="focused">Focused</option>
            </select>
          </label>
          {scope === "focused" && <label className="text-xs font-medium text-slate-600">Approved focus
            <input value={focus} onChange={(event) => setFocus(event.target.value)} placeholder="Product, service, or use case" className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm" />
          </label>}
        </div>
        <p className="mt-3 text-xs text-slate-500">Brand-wide balances major first-party topics. Focused intentionally concentrates on the approved focus while retaining intent variety.</p>
        <button type="button" disabled={!canGeneratePromptProposal({ operatorAuthorized: props.operatorAuthorized, generating, scope, focus })} onClick={() => setConfirming(true)} className="crystal-primary-button mt-4 px-4 py-2.5 text-sm">
          <Sparkles className="h-4 w-4" />{proposal ? "Regenerate Proposal" : "Generate Starter Set"}
        </button>
        {!props.operatorAuthorized && <p className="mt-2 text-xs text-amber-700">Unlock operator access to generate or apply prompt proposals.</p>}
      </div>

      {confirming && <div className="m-5 rounded-xl border border-violet-200 bg-white p-4 text-sm text-slate-600">
        <div className="font-medium text-slate-950">Generate Starter Prompt Set</div>
        <dl className="mt-3 grid grid-cols-2 gap-2 text-xs"><dt>Target</dt><dd>{props.targetBrand}</dd><dt>Scope</dt><dd>{pretty(scope)}</dd><dt>Source</dt><dd>{props.websitePageCount} crawled first-party pages</dd><dt>Approved competitors</dt><dd>{props.competitorCount}</dd><dt>Target size</dt><dd>19 prompts</dd></dl>
        <p className="mt-3 text-xs">This creates a proposal only. It will not run a benchmark.</p>
        <div className="mt-4 flex gap-2"><button onClick={() => setConfirming(false)} className="rounded-lg border px-3 py-2 text-xs">Cancel</button><button onClick={generate} disabled={generating} className="crystal-primary-button px-3 py-2 text-xs">{generating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}Generate</button></div>
      </div>}
      {error && <div className="m-5 flex gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-700"><TriangleAlert className="h-4 w-4" />{error}</div>}
      {success && <div className="m-5 flex gap-2 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="h-4 w-4" />{success}</div>}

      {proposal && <div className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><div className="text-xs uppercase tracking-wide text-violet-600">Proposed starter set · awaiting approval</div><div className="mt-1 text-sm text-slate-600">{proposal.generated_count} proposed · {pretty(proposal.measurement_scope)} · active set remains {props.activePromptCount}</div></div>
          <span className="rounded-full bg-white px-3 py-1 text-xs text-slate-600">{pretty(proposal.coverage_blueprint.concentration_status)}</span></div>
        <div className="mt-4 grid gap-3 lg:grid-cols-2"><div className="rounded-xl bg-white p-4"><div className="text-xs font-medium text-slate-500">Topic coverage</div>{topicEntries.map(([name, count]) => <div key={name} className="mt-2 flex justify-between text-sm"><span>{name}</span><span>{count}</span></div>)}</div>
          <div className="rounded-xl bg-white p-4"><div className="text-xs font-medium text-slate-500">Intent coverage</div>{Object.entries(proposal.coverage_blueprint.intent_distribution).map(([name, count]) => <div key={name} className="mt-2 flex justify-between text-sm"><span>{pretty(name)}</span><span>{count}</span></div>)}</div></div>
        <p className="mt-3 text-xs text-slate-500">Largest topic share: {(proposal.coverage_blueprint.largest_topic_share * 100).toFixed(1)}%. The 35% brand-wide guard is a SearchIntel benchmark-design constraint, not an industry standard.</p>
        {proposal.warnings.map((warning) => <div key={warning} className="mt-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-800">{warning}</div>)}
        <div className="mt-4 space-y-2">{proposal.prompts.map((prompt, index) => <div key={`${proposal.id}-${index}`} className="rounded-xl border border-slate-200 bg-white p-4">
          <label className="text-xs text-slate-500">Prompt {index + 1}<textarea value={prompt.text} onChange={(event) => editPrompt(index, "text", event.target.value)} rows={2} className="mt-1 w-full resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm leading-6 text-slate-800" /></label>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs"><span className="rounded bg-violet-50 px-2 py-1 text-violet-700">{prompt.topic_cluster}</span><select value={prompt.category} onChange={(event) => editPrompt(index, "category", event.target.value)} className="rounded border border-slate-200 bg-slate-100 px-2 py-1">{["brand", "informational", "problem_solution", "recommendation", "comparison", "commercial", "navigational", "transactional"].map((category) => <option key={category} value={category}>{pretty(category)}</option>)}</select></div>
        </div>)}</div>
        <button type="button" disabled={!props.operatorAuthorized || applying} onClick={applyProposal} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-4 py-3 text-sm font-medium text-slate-950 disabled:opacity-50">{applying && <Loader2 className="h-4 w-4 animate-spin" />}Replace Active Set</button>
        <p className="mt-2 text-center text-xs text-slate-500">Explicit operator approval is required. Historical frozen benchmark snapshots are not changed.</p>
      </div>}
    </div>
  );
}
