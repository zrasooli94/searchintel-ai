"use client";

import Link from "next/link";
import OperatorAccessPanel from "@/components/dashboard/operator-access-panel";
import { useRef, useState } from "react";
import { filterInbox, inboxCounts, initialInboxFilters, type InboxEvent, type InboxFilters } from "@/lib/agency-inbox";

const pretty = (text: string) => text.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const date = (text: string) => new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }).format(new Date(text)) + " UTC";

export default function AgencyInbox({ initial, operator }: { initial: InboxEvent[]; operator: boolean }) {
  const [events, setEvents] = useState(initial);
  const [filters, setFilters] = useState<InboxFilters>(initialInboxFilters);
  const [pending, setPending] = useState<number | null>(null);
  const busy = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const visible = filterInbox(events, filters);
  const projects = [...new Map(events.map((e) => [String(e.project_id), e.project_name])).entries()];
  async function update(event: InboxEvent, status: InboxEvent["status"]) {
    if (busy.current) return;
    busy.current = true; setPending(event.id); setError(null);
    try {
      const response = await fetch(`/api/agency-inbox/${event.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) });
      if (!response.ok) throw new Error("Could not save Inbox status. Check operator access and retry.");
      const saved = await response.json();
      setEvents((current) => current.map((e) => e.id === event.id ? { ...e, status: saved.status } : e));
    } catch (err) { setError(err instanceof Error ? err.message : "Could not save Inbox status."); }
    finally { busy.current = false; setPending(null); }
  }
  const select = (key: keyof InboxFilters, label: string, options: [string, string][]) => <label className="text-xs text-slate-500">{label}<select aria-label={label} value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800">{options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>;
  return <main className="crystal-page min-h-screen"><div className="mx-auto max-w-[1240px] space-y-6 px-5 py-8 lg:px-10">
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6"><div><Link href="/" className="text-sm font-semibold text-violet-700">SearchIntel</Link><h1 className="mt-3 text-3xl font-medium tracking-tight">Agency Inbox</h1><p className="mt-2 text-sm text-slate-500">What across all clients needs your attention?</p></div><Link href="/" className="text-sm">All projects</Link></header>
    <OperatorAccessPanel initialAuthorized={operator}/>
    <section aria-label="Inbox summary" className="grid gap-4 sm:grid-cols-4">{Object.entries(inboxCounts(events)).map(([label, count]) => <div key={label} className="crystal-panel rounded-2xl p-5"><div className="text-xs text-slate-500">{label}</div><div className="mt-2 text-3xl font-medium">{count}</div></div>)}</section>
    <section aria-label="Inbox filters" className="crystal-panel grid gap-4 rounded-2xl p-5 sm:grid-cols-2 lg:grid-cols-5">
      {select("project", "Project", [["", "All projects"], ...projects])}
      {select("severity", "Severity", [["", "All severities"], ...["high", "medium", "low"].map((s): [string, string] => [s, pretty(s)])])}
      {select("mode", "Source mode", [["", "All modes"], ...[...new Set(events.map((e) => e.source_mode))].sort().map((s): [string, string] => [s, pretty(s)])])}
      {select("type", "Event type", [["", "All event types"], ...[...new Set(events.map((e) => e.event_type))].sort().map((s): [string, string] => [s, pretty(s)])])}
      {select("status", "Status", [["active", "Unread and read"], ["unread", "Unread"], ["read", "Read"], ["archived", "Archived"], ["", "All statuses"]])}
    </section>
    <p className="text-xs text-slate-500">{visible.length} matching events. Severity uses deterministic internal V1 rules, not industry-standard thresholds. Viewing never runs measurements.</p>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}
    <section aria-label="Inbox events" className="space-y-4">{visible.map((event) => <article key={event.id} className="crystal-panel rounded-[22px] p-6">
      <div className="flex flex-wrap items-center gap-3 text-xs"><Link className="font-semibold text-violet-700" href={`/projects/${event.project_id}`}>{event.project_name}</Link><span className={`rounded-full px-3 py-1 ${event.severity === "high" ? "bg-red-50 text-red-700" : event.severity === "medium" ? "bg-amber-50 text-amber-800" : "bg-emerald-50 text-emerald-700"}`}>{event.severity.toUpperCase()}</span><span>{pretty(event.source_mode)}</span><span>{event.status.toUpperCase()}</span><time className="text-slate-400" dateTime={event.occurred_at}>{date(event.occurred_at)}</time></div>
      <h2 className="mt-4 text-lg font-medium">{event.title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{event.summary}</p>
      <div className="mt-4 grid gap-4 md:grid-cols-2"><Evidence label="Before" value={event.evidence.before}/><Evidence label="After" value={event.evidence.after}/></div>
      <div className="mt-5 flex flex-wrap items-center gap-3 text-sm"><Link href={event.evidence_path} className="font-medium text-violet-700">View Evidence →</Link>{operator && (["read", "unread", "archived"] as const).filter((s) => s !== event.status).map((status) => <button key={status} disabled={pending !== null} onClick={() => update(event, status)} className="rounded-xl border border-slate-200 px-3 py-2 disabled:opacity-50">{status === "archived" ? "Archive" : `Mark ${status}`}</button>)}</div>
    </article>)}{visible.length === 0 && <div className="crystal-panel rounded-2xl p-8 text-slate-500">No meaningful events match these filters. Stable measurements do not create alerts.</div>}</section>
  </div></main>;
}

function Evidence({ label, value }: { label: string; value: Record<string, unknown> | null }) {
  return <div className="min-w-0 rounded-xl bg-slate-50/80 p-4"><h3 className="text-xs font-semibold uppercase text-slate-500">{label}</h3>{value ? <dl className="mt-2 space-y-2 text-xs text-slate-700">{Object.entries(value).map(([key, data]) => <div key={key} className="break-words"><dt className="font-medium">{pretty(key)}</dt><dd>{data === null ? "Not available" : typeof data === "object" ? JSON.stringify(data) : String(data)}</dd></div>)}</dl> : <p className="mt-2 text-xs text-slate-500">No earlier observation claimed.</p>}</div>;
}
