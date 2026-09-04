export type InboxEvent = {
  id: number; project_id: number; project_name: string; event_type: string;
  severity: string; source_mode: string; title: string; summary: string;
  evidence: { before: Record<string, unknown> | null; after: Record<string, unknown> | null };
  related_ids: Record<string, unknown>; evidence_path: string; occurred_at: string;
  created_at: string; status: "unread" | "read" | "archived";
};

export type InboxFilters = { project: string; severity: string; mode: string; type: string; status: string };
export const initialInboxFilters: InboxFilters = { project: "", severity: "", mode: "", type: "", status: "active" };
export function filterInbox(events: InboxEvent[], filters: InboxFilters) {
  return events.filter((event) => (!filters.project || String(event.project_id) === filters.project)
    && (!filters.severity || event.severity === filters.severity)
    && (!filters.mode || event.source_mode === filters.mode)
    && (!filters.type || event.event_type === filters.type)
    && (!filters.status || (filters.status === "active" ? event.status !== "archived" : event.status === filters.status)));
}
export function inboxCounts(events: InboxEvent[]) {
  const active = events.filter((event) => event.status !== "archived");
  return { Unread: active.filter((e) => e.status === "unread").length,
    "High severity": active.filter((e) => e.severity === "high").length,
    "Failed / Overdue": active.filter((e) => ["monitoring_failed", "monitoring_overdue"].includes(e.event_type)).length,
    Improvements: active.filter((e) => e.event_type.includes("improved") || e.event_type.includes("resolved") || e.event_type === "target_coverage_gained").length };
}
