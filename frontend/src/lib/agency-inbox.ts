export type InboxEvent = {
  id: number; project_id: number; project_name: string; event_type: string;
  severity: string; source_mode: string; title: string; summary: string;
  evidence: { before: Record<string, unknown> | null; after: Record<string, unknown> | null };
  related_ids: Record<string, unknown>; evidence_path: string; occurred_at: string;
  created_at: string; status: "unread" | "read" | "archived";
  origin: "workflow" | "backfill";
  default_visible: boolean; attention_rank: number; attention_reason: string; is_improvement: boolean;
};

export type InboxFilters = { project: string; severity: string; mode: string; type: string; status: string; view: string };
export const initialInboxFilters: InboxFilters = { project: "", severity: "", mode: "", type: "", status: "active", view: "focus" };
const severityRank: Record<string, number> = { high: 3, medium: 2, low: 1 };
export function filterInbox(events: InboxEvent[], filters: InboxFilters) {
  return events.filter((event) => (filters.view === "all" || (filters.view === "historical" ? event.origin === "backfill" : event.default_visible))
    && (!filters.project || String(event.project_id) === filters.project)
    && (!filters.severity || event.severity === filters.severity)
    && (!filters.mode || event.source_mode === filters.mode)
    && (!filters.type || event.event_type === filters.type)
    && (!filters.status || (filters.status === "active" ? event.status !== "archived" : event.status === filters.status)))
    .sort((a, b) => b.attention_rank - a.attention_rank || severityRank[b.severity] - severityRank[a.severity]
      || Date.parse(b.occurred_at) - Date.parse(a.occurred_at) || b.id - a.id);
}

export function groupInbox(events: InboxEvent[]) {
  const groups = new Map<string, InboxEvent[]>();
  for (const event of events) {
    // Legacy import records remain independently addressable. Group only the
    // same project/mode/source/import transaction and saved lifecycle status.
    const source = ["technical_audit_id", "web_experiment_id", "site_rag_experiment_id", "readiness_state"].map(k => event.related_ids[k] ?? null);
    const key = event.origin === "backfill" && event.event_type === "priority_new_high"
      ? JSON.stringify([event.project_id, event.source_mode, source, event.created_at, event.status]) : String(event.id);
    const group = groups.get(key) ?? [];
    group.push(event); groups.set(key, group);
  }
  return [...groups.entries()].map(([key, members]) => ({ key, members, event: members[0] }));
}
export function inboxCounts(events: InboxEvent[]) {
  const active = groupInbox(filterInbox(events, initialInboxFilters)).map(group => group.event);
  return { "Needs Attention": active.filter((e) => e.attention_rank >= 2).length,
    Unread: active.filter((e) => e.origin !== "backfill" && e.status === "unread").length,
    "Failed / Overdue": active.filter((e) => ["monitoring_failed", "monitoring_overdue"].includes(e.event_type)).length,
    Improvements: active.filter((e) => e.is_improvement).length };
}
