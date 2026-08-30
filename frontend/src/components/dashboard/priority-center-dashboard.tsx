"use client";

import { useMemo, useState } from "react";
import { ChevronDown, CircleDot, ListTodo, RefreshCw, ShieldCheck } from "lucide-react";

import DashboardShell, { type DashboardShellSummary } from "@/components/dashboard/dashboard-shell";
import type { ProjectPriority, ProjectPrioritySummary } from "@/lib/types";

const statuses = ["open", "in_progress", "implemented", "ready_to_recheck", "rechecked_improved", "rechecked_unchanged", "rechecked_worsened"];
const pretty = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

function tone(value: string) {
  if (value === "high") return "border-red-200 bg-red-50 text-red-700";
  if (value === "medium") return "border-amber-200 bg-amber-50 text-amber-700";
  if (value === "monitor") return "border-sky-200 bg-sky-50 text-sky-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

export default function PriorityCenterDashboard({ initialSummary, operatorAuthorized, shellSummary }: {
  initialSummary: ProjectPrioritySummary; operatorAuthorized: boolean; shellSummary: DashboardShellSummary;
}) {
  const [summary, setSummary] = useState(initialSummary);
  const [statusFilter, setStatusFilter] = useState("active");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [pending, setPending] = useState<number | "refresh" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sources = useMemo(() => Array.from(new Set(summary.priorities.flatMap((item) => item.source_modes))).sort(), [summary]);
  const visible = summary.priorities.filter((item) =>
    (statusFilter === "all" || (statusFilter === "active" ? !item.is_resolved : item.status === statusFilter))
    && (priorityFilter === "all" || item.priority === priorityFilter)
    && (sourceFilter === "all" || item.source_modes.includes(sourceFilter))
  );

  async function refresh() {
    setPending("refresh"); setError(null);
    const response = await fetch(`/api/projects/${summary.project_id}/priorities/refresh`, { method: "POST" });
    if (response.ok) setSummary(await response.json());
    else setError((await response.json().catch(() => null))?.detail ?? "Priority refresh failed.");
    setPending(null);
  }

  async function setStatus(item: ProjectPriority, status: string) {
    setPending(item.id); setError(null);
    const response = await fetch(`/api/projects/${summary.project_id}/priorities/${item.id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }),
    });
    if (response.ok) {
      const updated = await response.json() as ProjectPriority;
      setSummary((current) => ({ ...current, priorities: current.priorities.map((entry) => entry.id === updated.id ? updated : entry) }));
    } else setError((await response.json().catch(() => null))?.detail ?? "Status update failed.");
    setPending(null);
  }

  const active = summary.priorities.filter((item) => !item.is_resolved);
  const stats = [
    ["Open priorities", active.filter((item) => item.status === "open").length],
    ["High priority", active.filter((item) => item.priority === "high").length],
    ["In progress", active.filter((item) => item.status === "in_progress").length],
    ["Ready to recheck", active.filter((item) => item.status === "ready_to_recheck").length],
  ];

  return <DashboardShell summary={shellSummary} title="Priority Center">
    <div className="crystal-page mx-auto max-w-[1450px] space-y-7 p-5 lg:p-8 xl:px-10">
      <section className="crystal-panel rounded-[22px] p-6 lg:p-8">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div><div className="crystal-eyebrow">What should we work on next?</div>
            <h2 className="mt-3 text-2xl font-medium tracking-[-0.035em] text-slate-950">Evidence-backed agency work queue</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">Ranked from stored technical, Web Search, Site RAG, and readiness evidence. Memory is context only; it does not create SEO tasks.</p>
          </div>
          {operatorAuthorized ? <button disabled={pending !== null} onClick={refresh} className="crystal-primary-button flex items-center gap-2 px-4 py-2.5 text-sm"><RefreshCw className={`h-4 w-4 ${pending === "refresh" ? "animate-spin" : ""}`} />Refresh from evidence</button>
            : <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs text-slate-500"><ShieldCheck className="h-4 w-4" />Viewer mode · read only</div>}
        </div>
        {error && <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{stats.map(([label, value]) => <div key={label} className="crystal-card rounded-[20px] p-5"><div className="crystal-eyebrow">{label}</div><div className="crystal-value mt-4 text-3xl font-medium">{value}</div></div>)}</section>

      <section className="crystal-panel rounded-[22px] p-5">
        <div className="grid gap-3 md:grid-cols-3">
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"><option value="active">Active work</option><option value="all">All including resolved</option>{statuses.map((value) => <option key={value} value={value}>{pretty(value)}</option>)}</select>
          <select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"><option value="all">All priorities</option>{["high", "medium", "low", "monitor"].map((value) => <option key={value} value={value}>{pretty(value)}</option>)}</select>
          <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"><option value="all">All source modes</option>{sources.map((value) => <option key={value} value={value}>{pretty(value)}</option>)}</select>
        </div>
      </section>

      <section className="space-y-4">{visible.map((item) => <article key={item.id} className={`crystal-panel rounded-[22px] p-6 ${item.is_resolved ? "opacity-60" : ""}`}>
        <div className="flex flex-wrap items-start justify-between gap-4"><div className="min-w-0 flex-1">
          <div className="flex flex-wrap gap-2"><span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase ${tone(item.priority)}`}>{item.priority}</span>{item.source_modes.map((mode) => <span key={mode} className="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-[11px] text-violet-700">{pretty(mode)}</span>)}{item.is_resolved && <span className="rounded-full border px-2.5 py-1 text-[11px]">Resolved by newer evidence</span>}</div>
          <h3 className="mt-4 text-xl font-medium tracking-[-0.025em] text-slate-950">{item.title}</h3>
        </div><div className="text-right"><div className="text-3xl font-medium text-slate-950">{item.priority_score}</div><div className="text-[10px] uppercase tracking-wider text-slate-400">Priority score</div></div></div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">{[["Impact", item.impact], ["Effort", item.effort], ["Confidence", item.confidence]].map(([label, value]) => <div key={label} className="rounded-xl bg-slate-50 px-4 py-3"><div className="text-[10px] uppercase tracking-wider text-slate-400">{label}</div><div className="mt-1 text-sm font-medium">{pretty(value)}</div></div>)}</div>
        <div className="mt-5 grid gap-5 lg:grid-cols-3"><div><div className="crystal-eyebrow">Observed evidence</div><ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">{item.observed_evidence.map((evidence) => <li key={evidence} className="flex gap-2"><CircleDot className="mt-1 h-3.5 w-3.5 shrink-0 text-violet-500" />{evidence}</li>)}</ul></div><div><div className="crystal-eyebrow">Interpretation</div><p className="mt-3 text-sm leading-6 text-slate-600">{item.interpretation}</p></div><div><div className="crystal-eyebrow">Recommended action</div><p className="mt-3 text-sm leading-6 text-slate-600">{item.recommended_action}</p></div></div>
        <details className="mt-5 rounded-xl border border-slate-200 bg-white"><summary className="flex cursor-pointer items-center justify-between px-4 py-3 text-sm font-medium">Evidence details & ranking <ChevronDown className="h-4 w-4" /></summary><div className="border-t border-slate-100 p-4 text-xs leading-6 text-slate-500"><p>{String(item.provenance.why_ranked ?? "Deterministic V1 scoring from stored evidence.")}</p>{item.affected_prompts.length > 0 && <p className="mt-2"><b>Prompts:</b> {item.affected_prompts.join(" · ")}</p>}{item.affected_pages.length > 0 && <p className="mt-2"><b>Pages:</b> {item.affected_pages.join(" · ")}</p>}{item.affected_entities.length > 0 && <p className="mt-2"><b>Entities:</b> {item.affected_entities.join(" · ")}</p>}</div></details>
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3"><span className="text-xs text-slate-400">Lifecycle: {pretty(item.status)}</span>{operatorAuthorized && !item.is_resolved && <select disabled={pending === item.id} value={item.status} onChange={(event) => setStatus(item, event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm">{statuses.map((status) => <option key={status} value={status}>{pretty(status)}</option>)}</select>}</div>
      </article>)}{visible.length === 0 && <div className="crystal-panel rounded-[22px] p-12 text-center"><ListTodo className="mx-auto h-8 w-8 text-slate-300" /><h3 className="mt-4 text-lg font-medium">No priorities match these filters</h3><p className="mt-2 text-sm text-slate-500">An operator can refresh this queue explicitly from stored evidence.</p></div>}</section>
      <p className="text-xs leading-5 text-slate-400">{summary.provenance_note}</p>
    </div>
  </DashboardShell>;
}
