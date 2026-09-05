"use client";

import Link from "next/link";
import { useState } from "react";
import { filterPortfolio, initialPortfolioFilters, type Measurement, type Portfolio, type PortfolioFilters, type Trend } from "@/lib/agency-portfolio";

const pretty = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const date = (value: string | null) => value ? new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(value)) : "Not available";
const statusClass = (status: string) => status === "needs_attention" ? "bg-red-50 text-red-700" : status === "setup_required" ? "bg-amber-50 text-amber-800" : status === "monitoring" ? "bg-blue-50 text-blue-700" : "bg-emerald-50 text-emerald-700";

export default function ClientsDashboard({ initial }: { initial: Portfolio }) {
  const [filters, setFilters] = useState<PortfolioFilters>(initialPortfolioFilters);
  const clients = filterPortfolio(initial.clients, filters);
  const select = (key: keyof PortfolioFilters, label: string, options: [string, string][]) => <label className="text-xs text-slate-500">{label}<select aria-label={label} value={filters[key]} onChange={(event) => setFilters({ ...filters, [key]: event.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800">{options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>;
  const summary = [["Clients", initial.summary.clients], ["Need Attention", initial.summary.needs_attention], ["High Alerts", initial.summary.high_severity_alerts], ["High Priorities", initial.summary.high_priorities], ["Monitoring Problems", initial.summary.monitoring_problems], ["Reports Missing", initial.summary.reports_missing]];

  return <main className="crystal-page min-h-screen"><div className="mx-auto max-w-[1500px] space-y-6 px-5 py-8 lg:px-10">
    <header className="flex flex-wrap items-end justify-between gap-5 border-b border-slate-200 pb-6"><div><Link href="/" className="text-sm font-semibold text-violet-700">SearchIntel</Link><h1 className="mt-3 text-3xl font-medium tracking-tight">Clients</h1><p className="mt-2 text-sm text-slate-500">Which clients need attention, and what is happening across the portfolio?</p></div><Link href="/agency-inbox" className="text-sm font-medium text-violet-700">Open Agency Inbox →</Link></header>
    <section aria-label="Portfolio summary" className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">{summary.map(([label, value]) => <div key={label} className="crystal-panel rounded-2xl p-4"><div className="text-xs text-slate-500">{label}</div><div className="mt-2 text-2xl font-medium">{value}</div></div>)}</section>
    <section aria-label="Client filters" className="crystal-panel grid gap-4 rounded-2xl p-5 sm:grid-cols-2 xl:grid-cols-4">
      {select("status", "Portfolio status", [["", "All statuses"], ["needs_attention", "Needs Attention"], ["healthy", "Healthy"], ["setup_required", "Setup Required"], ["monitoring", "Monitoring"]])}
      {select("monitoring", "Monitoring", [["", "Any monitoring"], ["problem", "Has a problem"], ["monitoring", "Active and healthy"], ["not_configured", "Not configured"]])}
      {select("priorities", "Priorities", [["", "Any priority state"], ["high", "Has high priorities"], ["open", "Has open priorities"]])}
      {select("report", "Latest report", [["", "Any report state"], ["missing", "Missing"], ["draft", "Draft"], ["published", "Published"], ["expired", "Expired"], ["revoked", "Revoked"]])}
    </section>
    <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500"><p>{clients.length} clients · Sorted by attention, urgency, then recency.</p><p>No cross-mode or synthetic portfolio score.</p></div>
    <section aria-label="Client portfolio" className="space-y-3">{clients.map((client) => <article key={client.project_id} className="crystal-panel rounded-[22px] p-5">
      <div className="grid gap-5 xl:grid-cols-[1.45fr_repeat(4,minmax(115px,0.8fr))_1.15fr] xl:items-center">
        <div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><Link href={client.links.project} className="truncate text-lg font-medium text-slate-950 hover:text-violet-700">{client.project_name}</Link><span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${statusClass(client.status)}`}>{pretty(client.status).toUpperCase()}</span></div><p className="mt-1 text-xs text-slate-500">{client.target_brand ?? "Target brand not configured"}</p><p className="mt-2 text-xs leading-5 text-slate-500">{client.status_reason}</p></div>
        <Metric label="Technical SEO" value={client.technical_seo.score} suffix="/100" status={client.technical_seo.status} detail={client.technical_seo.pages_checked === null ? null : `${client.technical_seo.pages_checked} pages`} />
        <MeasurementMetric label="Web visibility" measurement={client.web_search} suffix="" />
        <MeasurementMetric label="Memory" measurement={client.memory} statusOnly />
        <MeasurementMetric label="Site RAG" measurement={client.site_rag} suffix="%" />
        <div className="grid grid-cols-2 gap-3 text-xs xl:block xl:space-y-2"><Fact label="Priorities" value={`${client.priorities.high} high · ${client.priorities.open} open`} /><Fact label="Inbox" value={`${client.inbox.high} high · ${client.inbox.needs_attention} attention`} /><Fact label="Monitoring" value={client.monitoring.problem_count ? `${client.monitoring.problem_count} problem` : client.monitoring.enabled_modes ? `${client.monitoring.enabled_modes} modes active` : "Not configured"} /><Fact label="Next run" value={date(client.monitoring.next_due_at)} /><Fact label="Latest report" value={`${pretty(client.report.status)} · ${date(client.report.created_at)}`} /></div>
      </div>
      <div className="mt-5 flex flex-col gap-3 border-t border-slate-200 pt-4 md:flex-row md:items-center md:justify-between"><div className="min-w-0 text-xs text-slate-500">{client.last_meaningful_change ? <><span className="font-medium text-slate-700">Last meaningful change:</span> {client.last_meaningful_change.title} · {date(client.last_meaningful_change.occurred_at)}</> : "No durable meaningful change recorded."}</div><nav aria-label={`${client.project_name} quick links`} className="flex flex-wrap gap-x-4 gap-y-2 text-xs font-medium text-violet-700"><Link href={client.links.priorities}>Priority Center</Link><Link href={client.links.monitoring}>Monitoring</Link><Link href={client.links.inbox}>Agency Inbox</Link><Link href={client.links.reports}>Client Reports</Link></nav></div>
    </article>)}{clients.length === 0 && <div className="crystal-panel rounded-2xl p-10 text-center text-sm text-slate-500">No clients match these filters.</div>}</section>
    <p className="text-xs leading-5 text-slate-500">{initial.provenance_note} Viewing this page never runs AI, Web Search, crawls, benchmarks, or report generation.</p>
  </div></main>;
}

function TrendLabel({ trend }: { trend: Trend }) {
  if (!trend) return <span>No compatible trend</span>;
  const sign = trend.delta > 0 ? "+" : "";
  return <span className={trend.state === "improved" ? "text-emerald-700" : trend.state === "declined" ? "text-red-700" : "text-slate-500"}>{pretty(trend.state)} · {sign}{trend.delta}</span>;
}
function MeasurementMetric({ label, measurement, suffix = "", statusOnly = false }: { label: string; measurement: Measurement; suffix?: string; statusOnly?: boolean }) {
  if (measurement.status !== "completed") return <Metric label={label} value={null} status="not_measured" />;
  return <div><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{label}</div><div className="mt-1 text-xl font-medium">{statusOnly ? "Measured" : measurement.value === null ? "N/A" : `${measurement.value}${suffix}`}</div><div className="mt-1 text-[11px] text-slate-500">{statusOnly ? `${measurement.prompt_count ?? 0} prompts · ${date(measurement.completed_at)}` : <TrendLabel trend={measurement.trend} />}</div></div>;
}
function Metric({ label, value, suffix = "", status, detail }: { label: string; value: number | null; suffix?: string; status: string; detail?: string | null }) {
  return <div><div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{label}</div><div className="mt-1 text-xl font-medium">{value === null ? "N/A" : `${value}${suffix}`}</div><div className="mt-1 text-[11px] text-slate-500">{pretty(status)}{detail ? ` · ${detail}` : ""}</div></div>;
}
function Fact({ label, value }: { label: string; value: string }) { return <div><span className="text-slate-400">{label}: </span><span className="text-slate-700">{value}</span></div>; }
