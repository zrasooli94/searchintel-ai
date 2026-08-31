import type { ClientReport } from "@/lib/types";

const pretty = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const metric = (value: unknown, suffix = "") => value === null || value === undefined ? "N/A" : `${value}${suffix}`;

export default function ClientReportContent({ report, publicView = false }: { report: ClientReport; publicView?: boolean }) {
  type Priority = { id: number; title: string; status: string; priority: string; recommended_action: string; source_modes: string[] };
  type Recheck = { priority_id: number; title: string; status: string; explanation: string; baseline: { metrics: Record<string, number>; gap_count: number }; recheck: { metrics: Record<string, number>; gap_count: number } };
  type Snapshot = { generated_at: string; project: { name: string }; executive_summary: { note: string }; technical_seo: Record<string, unknown>; measurements: Record<string, { metrics: Record<string, unknown> } | null>; competitor_position: { configured_competitors: string[] }; priorities: Priority[]; compatible_rechecks: Recheck[]; recommended_next_actions: string[]; scope_and_provenance: { snapshot_note: string } };
  const s = report.snapshot as unknown as Snapshot;
  const technical = s.technical_seo;
  const audit = (technical.audit ?? {}) as Record<string, unknown>;
  const web = s.measurements?.web_search?.metrics;
  const memory = s.measurements?.memory?.metrics;
  const rag = s.measurements?.site_rag?.metrics;
  const webTarget = (web?.target ?? {}) as Record<string, unknown>;
  const memoryTarget = (memory?.target ?? {}) as Record<string, unknown>;
  return <main className={publicView ? "min-h-screen bg-[#f7f9fd] px-5 py-10 text-slate-900" : "space-y-6"}>
    <div className={publicView ? "mx-auto max-w-5xl space-y-7" : "space-y-6"}>
      <header className="rounded-[28px] border border-indigo-100 bg-white p-8 shadow-[0_20px_70px_rgba(69,72,122,.08)]">
        <div className="text-xs font-semibold uppercase tracking-[.18em] text-indigo-600">SearchIntel Client Report</div>
        <h1 className="mt-4 text-4xl font-medium tracking-[-.04em]">{report.title}</h1>
        <p className="mt-3 text-slate-500">{s.project.name} · {new Date(s.generated_at).toLocaleDateString()}{report.period_label ? ` · ${report.period_label}` : ""}</p>
      </header>
      <section className="rounded-3xl border border-slate-200 bg-white p-7"><h2 className="text-xl font-medium">Executive Summary</h2><p className="mt-3 leading-7 text-slate-600">{s.executive_summary.note}</p></section>
      <section className="grid gap-4 md:grid-cols-2">
        {[
          ["Technical SEO", `${String(technical.measurement_state ?? "unavailable").toUpperCase()} · ${audit.score !== undefined ? `sample score ${audit.score}/100` : "score N/A"} · ${audit.pages_checked ?? technical.successful_pages ?? 0} pages`],
          ["Web Search / AI Visibility", web ? `Web visibility ${metric(webTarget.web_visibility_score)} · verified coverage ${metric(webTarget.entity_verified_response_coverage, "%")} · cited coverage ${metric(webTarget.cited_response_coverage, "%")}` : "No completed Web Search measurement in this snapshot."],
          ["Memory Context", memory ? `${String(memory.analyzed_prompts ?? 0)} measured prompts · verified response coverage ${metric(memoryTarget.entity_verified_response_coverage, "%")}` : "No completed Memory measurement in this snapshot."],
          ["Site RAG / First-Party Evidence", rag ? `Answerability ${metric(rag.site_answerability_rate_v1, "%")} · evidence coverage ${metric(rag.evidence_coverage_rate, "%")} · source references ${metric(rag.source_reference_rate, "%")}` : "No completed Site RAG measurement in this snapshot."],
        ].map(([title, text]) => <article key={title} className="rounded-3xl border border-slate-200 bg-white p-6"><h2 className="font-medium">{title}</h2><p className="mt-3 text-sm leading-6 text-slate-600">{text}</p></article>)}
      </section>
      <section className="rounded-3xl border border-slate-200 bg-white p-7"><h2 className="text-xl font-medium">Competitor Position</h2><p className="mt-3 text-slate-600">{s.competitor_position.configured_competitors.join(", ") || "No configured competitors."}</p></section>
      <section className="rounded-3xl border border-slate-200 bg-white p-7"><h2 className="text-xl font-medium">Top Recommended Actions</h2><div className="mt-5 space-y-4">{s.priorities.map((p) => <article key={p.id} className="rounded-2xl bg-slate-50 p-5"><div className="flex justify-between gap-4"><h3 className="font-medium">{p.title}</h3><span className="text-xs font-semibold uppercase text-indigo-600">{p.priority}</span></div><p className="mt-2 text-sm leading-6 text-slate-600">{p.recommended_action}</p><p className="mt-2 text-xs text-slate-400">{pretty(p.status)} · {p.source_modes.map(pretty).join(" + ")}</p></article>)}</div></section>
      {s.compatible_rechecks.map((r) => <section key={r.priority_id} className="rounded-3xl border border-emerald-200 bg-emerald-50/60 p-7"><h2 className="text-xl font-medium">Before → After Compatible Recheck</h2><p className="mt-3 font-medium">{r.title} · {pretty(r.status)}</p><p className="mt-3 leading-7 text-slate-600">Baseline: {metric(r.baseline.metrics.site_answerability_rate_v1, "%")}, {r.baseline.metrics.site_rag_analyzed_runs - r.baseline.gap_count}/{r.baseline.metrics.site_rag_analyzed_runs} supported, {r.baseline.gap_count} gaps. Recheck: {metric(r.recheck.metrics.site_answerability_rate_v1, "%")}, {r.recheck.metrics.site_rag_analyzed_runs - r.recheck.gap_count}/{r.recheck.metrics.site_rag_analyzed_runs} supported, {r.recheck.gap_count} gaps. {r.explanation}</p></section>)}
      <section className="rounded-3xl border border-slate-200 bg-white p-7"><h2 className="text-xl font-medium">Outstanding Issues & Next Actions</h2><ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600">{s.recommended_next_actions.map((a: string) => <li key={a}>{a}</li>)}</ul></section>
      <footer className="pb-8 text-xs leading-5 text-slate-400">{s.scope_and_provenance.snapshot_note} Memory, Web Search, Site RAG, and Technical SEO retain separate measurement meanings and are not combined into a synthetic score. Snapshot integrity: {report.content_hash.slice(0, 12)}.</footer>
    </div>
  </main>;
}
