"use client";

import { Bot, CheckCircle2, Loader2, Sparkles, TriangleAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useRef, useState } from "react";
import type { StarterPromptGenerationResult, StarterPromptSuggestion } from "@/lib/types";
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
  const [reevaluating, setReevaluating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [semanticConfirming, setSemanticConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const saveQueue = useRef<Promise<void>>(Promise.resolve());
  const editRevision = useRef(0);
  const proposal = result?.status === "proposed" ? result : null;
  const topicEntries = useMemo(() => Object.entries(proposal?.coverage_blueprint.topic_distribution ?? {}), [proposal]);
  const familyEntries = useMemo(() => Object.entries(proposal?.coverage_blueprint.topic_family_distribution ?? {}), [proposal]);
  const superThemeEntries = useMemo(() => Object.entries(proposal?.coverage_blueprint.super_theme_distribution ?? {}), [proposal]);

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

  async function reevaluateProposal() {
    if (!proposal) return;
    setReevaluating(true); setError(null);
    try {
      const response = await fetch(`/api/projects/${props.projectId}/prompts/starter-proposals/${proposal.id}/semantic-reevaluate`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Semantic re-evaluation failed.");
      setResult(data); setSemanticConfirming(false); router.refresh();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Semantic re-evaluation failed."); }
    finally { setReevaluating(false); }
  }

  function editedPrompts(index: number, field: "text" | "category", value: string) {
    if (!proposal) return null;
    const prompts = proposal.prompts.map((prompt, promptIndex) => (
      promptIndex === index ? { ...prompt, [field]: value } : prompt
    ));
    editRevision.current += 1;
    setResult({ ...proposal, prompts });
    return prompts;
  }

  function saveProposal(prompts: StarterPromptSuggestion[]) {
    if (!proposal) return;
    const proposalId = proposal.id;
    const savedRevision = editRevision.current;
    const snapshot = prompts.map((prompt) => ({ ...prompt }));
    setSaving(true); setError(null); setSuccess(null);
    const queued = saveQueue.current.then(async () => {
      try {
        const response = await fetch(`/api/projects/${props.projectId}/prompts/starter-proposals/${proposalId}`, {
          method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompts: snapshot }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data?.detail === "string" ? data.detail : "Proposal edit failed.");
        if (editRevision.current === savedRevision) setResult(data);
        setSuccess("Proposal saved. Semantic coverage and readiness were recalculated.");
        router.refresh();
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Proposal edit failed.");
      }
    });
    saveQueue.current = queued;
    void queued.finally(() => {
      if (saveQueue.current === queued) setSaving(false);
    });
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
        <p className="mt-3 text-xs">Initial generation uses 1 AI call. If brand-wide coverage fails, SearchIntel may use 1 automatic rebalancing call. Maximum: 2 generation calls. This creates a proposal only and will not run a benchmark.</p>
        <div className="mt-4 flex gap-2"><button onClick={() => setConfirming(false)} className="rounded-lg border px-3 py-2 text-xs">Cancel</button><button onClick={generate} disabled={generating} className="crystal-primary-button px-3 py-2 text-xs">{generating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}Generate</button></div>
      </div>}
      {error && <div className="m-5 flex gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-700"><TriangleAlert className="h-4 w-4" />{error}</div>}
      {success && <div className="m-5 flex gap-2 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="h-4 w-4" />{success}</div>}

      {proposal && <div className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3"><div><div className="text-xs uppercase tracking-wide text-violet-600">Proposed starter set · awaiting approval</div><div className="mt-1 text-sm text-slate-600">{proposal.generated_count} proposed · {pretty(proposal.measurement_scope)} · active set remains {props.activePromptCount}</div></div>
          <span className="rounded-full bg-white px-3 py-1 text-xs text-slate-600">{pretty(proposal.coverage_blueprint.concentration_status)}</span></div>
        {proposal.coverage_blueprint.automatic_rebalance && !proposal.coverage_blueprint.manual_revalidation && <div className="mt-4 rounded-xl border border-violet-100 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-2"><div className="text-xs font-medium uppercase tracking-wide text-violet-600">Automatic rebalance</div><span className="rounded-full bg-violet-50 px-3 py-1 text-xs text-violet-700">{pretty(proposal.coverage_blueprint.automatic_rebalance.status)}</span></div>
          <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2"><div>Initial coverage: <span className="font-medium text-slate-900">{pretty(proposal.coverage_blueprint.automatic_rebalance.initial_validation.coverage_status)}</span></div><div>Final coverage: <span className="font-medium text-slate-900">{pretty(proposal.coverage_blueprint.automatic_rebalance.final_validation.coverage_status)}</span></div><div>{proposal.coverage_blueprint.automatic_rebalance.status === "completed" ? "Retained" : "Protected prompts"}: <span className="font-medium text-slate-900">{proposal.coverage_blueprint.automatic_rebalance.retained_count} prompts</span></div><div>{proposal.coverage_blueprint.automatic_rebalance.status === "completed" ? "Replaced" : "Repair candidates"}: <span className="font-medium text-slate-900">{proposal.coverage_blueprint.automatic_rebalance.replaced_count} prompts</span></div></div>
          {proposal.coverage_blueprint.automatic_rebalance.triggered && <p className="mt-3 text-xs leading-5 text-slate-500">{proposal.coverage_blueprint.automatic_rebalance.status === "completed" ? "SearchIntel repaired the detected coverage imbalance once, then reran the existing coverage validation." : "SearchIntel attempted one bounded repair, but the proposal still needs human review after revalidation."} No benchmark was created.</p>}
        </div>}
        {props.operatorAuthorized && proposal.generator_version !== "semantic-classification-v6" && <><button type="button" disabled={reevaluating} onClick={() => setSemanticConfirming(true)} className="mt-4 rounded-xl border border-violet-200 bg-white px-4 py-2.5 text-sm font-medium text-violet-700 disabled:opacity-50">Re-evaluate Semantic Coverage</button>{semanticConfirming && <div className="mt-3 rounded-xl border border-violet-200 bg-white p-4 text-xs leading-5 text-slate-600"><div className="font-medium text-slate-950">Re-evaluate this stored proposal?</div><p className="mt-2">Semantic reclassification is deterministic. If it detects a correctable imbalance, SearchIntel may use at most 1 AI repair call. This will not create a benchmark or activate prompts.</p><div className="mt-3 flex gap-2"><button type="button" onClick={() => setSemanticConfirming(false)} className="rounded-lg border px-3 py-2">Cancel</button><button type="button" onClick={reevaluateProposal} disabled={reevaluating} className="crystal-primary-button px-3 py-2">{reevaluating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}Re-evaluate</button></div></div>}</>}
        <div className="mt-4 grid gap-3 lg:grid-cols-2"><div className="rounded-xl bg-white p-4"><div className="text-xs font-medium text-slate-500">Topic coverage</div>{topicEntries.map(([name, count]) => <div key={name} className="mt-2 flex justify-between text-sm"><span>{name}</span><span>{count}</span></div>)}</div>
          <div className="rounded-xl bg-white p-4"><div className="text-xs font-medium text-slate-500">Intent coverage</div>{Object.entries(proposal.coverage_blueprint.intent_distribution).map(([name, count]) => <div key={name} className="mt-2 flex justify-between text-sm"><span>{pretty(name)}</span><span>{count}</span></div>)}</div></div>
        {proposal.measurement_scope === "brand_wide" && <div className="mt-3 rounded-xl border border-violet-100 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-2"><div><div className="text-xs font-medium uppercase tracking-wide text-violet-600">Brand-wide coverage</div><div className="mt-1 text-sm font-medium text-slate-950">{proposal.coverage_blueprint.core_category?.core_brand_market?.name ?? proposal.coverage_blueprint.core_category?.name ?? "Core market needs review"}</div><div className="mt-1 text-xs text-slate-500">Core brand market</div>{proposal.coverage_blueprint.core_category?.strategic_emphasis?.name && <><div className="mt-3 text-sm font-medium text-slate-950">{proposal.coverage_blueprint.core_category.strategic_emphasis.name}</div><div className="mt-1 text-xs text-slate-500">Current strategic emphasis</div></>}</div><span className="rounded-full bg-violet-50 px-3 py-1 text-xs text-violet-700">{pretty(proposal.coverage_blueprint.concentration_status)}</span></div>
          {proposal.coverage_blueprint.core_category?.weighting_note && <p className="mt-3 text-xs leading-5 text-slate-500">{proposal.coverage_blueprint.core_category.weighting_note}</p>}
          <div className="mt-4 grid gap-4 lg:grid-cols-2"><div><div className="text-xs font-medium text-slate-500">Topic families</div>{familyEntries.map(([name, count]) => <div key={name} className="mt-2 flex justify-between text-sm"><span>{name}</span><span>{count}</span></div>)}</div>
            <div><div className="text-xs font-medium text-slate-500">Coverage checklist</div>{Object.entries(proposal.coverage_blueprint.brand_wide_checklist).map(([name, passed]) => <div key={name} className="mt-2 flex items-center gap-2 text-sm"><span className={passed ? "text-emerald-600" : "text-amber-600"}>{passed ? "✓" : "!"}</span><span>{pretty(name)}</span></div>)}</div></div>
          <div className="mt-4 border-t border-slate-100 pt-4"><div className="text-xs font-medium text-slate-500">Effective super-theme coverage</div>{superThemeEntries.map(([name, count]) => <div key={name} className="mt-2 flex justify-between gap-4 text-sm"><span>{name}</span><span className="whitespace-nowrap">{count} · {((count / proposal.generated_count) * 100).toFixed(1)}%</span></div>)}<p className="mt-3 text-xs text-slate-500">Coverage is calculated from prompt meaning, not generator labels alone.</p></div>
          {proposal.coverage_blueprint.crawl_sample_bias.detected && <div className="mt-4 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-800"><span className="font-medium">Crawl sample bias detected.</span> {proposal.coverage_blueprint.crawl_sample_bias.reason}</div>}
        </div>}
        <p className="mt-3 text-xs text-slate-500">Largest topic share: {(proposal.coverage_blueprint.largest_topic_share * 100).toFixed(1)}%. Largest topic-family share: {(proposal.coverage_blueprint.largest_topic_family_share * 100).toFixed(1)}%. Largest super-theme share: {(proposal.coverage_blueprint.largest_super_theme_share * 100).toFixed(1)}%. The 35% cluster, 40% family, and 45% super-theme guards are SearchIntel benchmark-design constraints, not industry standards.</p>
        {proposal.warnings.map((warning) => <div key={warning} className="mt-2 rounded-lg bg-amber-50 p-3 text-xs text-amber-800">{warning}</div>)}
        <div className="mt-4 space-y-2">{proposal.prompts.map((prompt, index) => <div key={`${proposal.id}-${index}`} className="rounded-xl border border-slate-200 bg-white p-4">
          <label className="text-xs text-slate-500">Prompt {index + 1}<textarea value={prompt.text} onChange={(event) => editedPrompts(index, "text", event.target.value)} onBlur={() => saveProposal(proposal.prompts)} rows={2} className="mt-1 w-full resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm leading-6 text-slate-800" /></label>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs"><span className="rounded bg-violet-50 px-2 py-1 text-violet-700">{prompt.topic_cluster}</span><select value={prompt.category} onChange={(event) => { const prompts = editedPrompts(index, "category", event.target.value); if (prompts) saveProposal(prompts); }} className="rounded border border-slate-200 bg-slate-100 px-2 py-1">{["brand", "informational", "problem_solution", "recommendation", "comparison", "commercial", "navigational", "transactional"].map((category) => <option key={category} value={category}>{pretty(category)}</option>)}</select></div>
        </div>)}</div>
        {saving && <p className="mt-3 flex items-center gap-2 text-xs text-violet-700"><Loader2 className="h-3.5 w-3.5 animate-spin" />Saving edit and recalculating semantic coverage…</p>}
        <button type="button" disabled={!props.operatorAuthorized || applying || saving} onClick={applyProposal} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-4 py-3 text-sm font-medium text-slate-950 disabled:opacity-50">{applying && <Loader2 className="h-4 w-4 animate-spin" />}Replace Active Set</button>
        <p className="mt-2 text-center text-xs text-slate-500">Explicit operator approval is required. Historical frozen benchmark snapshots are not changed.</p>
      </div>}
    </div>
  );
}
