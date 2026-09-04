import assert from "node:assert/strict";
import test from "node:test";
import { filterInbox, groupInbox, inboxCounts, initialInboxFilters, type InboxEvent } from "./agency-inbox.ts";

const events = [
  { id: 1, project_id: 4, severity: "high", source_mode: "site_rag", event_type: "priority_new_high", status: "unread" },
  { id: 2, project_id: 8, severity: "low", source_mode: "technical_seo", event_type: "score_improved", status: "read" },
  { id: 3, project_id: 4, severity: "high", source_mode: "web_search", event_type: "monitoring_failed", status: "archived" },
].map((e) => ({ ...e, origin: "workflow", default_visible: true, attention_rank: e.severity === "high" ? 3 : 1,
  is_improvement: e.event_type === "score_improved", related_ids: {}, occurred_at: "2026-09-04T00:00:00Z" })) as InboxEvent[];
test("Inbox filters combine and preserve project/mode boundaries", () => {
  assert.deepEqual(filterInbox(events, initialInboxFilters).map(e => e.id), [1, 2]);
  assert.deepEqual(filterInbox(events, { ...initialInboxFilters, project: "4", mode: "site_rag", severity: "high", type: "priority_new_high", status: "unread" }).map(e => e.id), [1]);
  assert.deepEqual(filterInbox(events, { ...initialInboxFilters, status: "archived" }).map(e => e.id), [3]);
  assert.equal(filterInbox(events, { ...initialInboxFilters, project: "8", mode: "site_rag" }).length, 0);
});
test("Archived events remain available but do not inflate active summary", () => {
  assert.deepEqual(inboxCounts(events), { "Needs Attention": 1, Unread: 1, "Failed / Overdue": 0, Improvements: 1 });
});
test("Historical import stays queryable without fresh-unread counts; verified follow-up remains", () => {
  const history = events.map(e => ({ ...e, origin: "backfill" as const, default_visible: false }));
  const followup = { ...history[0], id: 4, event_type: "priority_rechecked_unchanged", default_visible: true, attention_rank: 2 };
  const rows = [...history, followup];
  assert.deepEqual(filterInbox(rows, initialInboxFilters).map(e => e.id), [4]);
  assert.equal(filterInbox(rows, { ...initialInboxFilters, view: "historical", status: "" }).length, 4);
  assert.equal(filterInbox(rows, { ...initialInboxFilters, view: "all", status: "" }).length, 4);
  assert.equal(inboxCounts(rows).Unread, 0);
  assert.equal(inboxCounts(rows)["Needs Attention"], 1);
  assert.equal(inboxCounts(rows.map(e => ({ ...e, status: "archived" as const })))["Needs Attention"], 0);
});
test("Actionability then severity then recency; stable history never dominates", () => {
  const rows = [
    { ...events[1], id: 1, attention_rank: 1, occurred_at: "2026-09-05T00:00:00Z" },
    { ...events[0], id: 2, attention_rank: 4, severity: "medium" },
    { ...events[0], id: 3, attention_rank: 4, severity: "high", occurred_at: "2026-09-03T00:00:00Z" },
    { ...events[0], id: 4, attention_rank: 4, severity: "high" },
  ];
  assert.deepEqual(filterInbox(rows, initialInboxFilters).map(e => e.id), [4, 3, 2, 1]);
});
test("Historical work packages group only within identical source, project and saved state", () => {
  const first = { ...events[0], origin: "backfill" as const, related_ids: { technical_audit_id: 10, priority_id: 1 }, created_at: "2026-09-04T00:00:00Z" };
  const rows = [first, { ...first, id: 2, related_ids: { technical_audit_id: 10, priority_id: 2 } },
    { ...first, id: 3, project_id: 8 }, { ...first, id: 4, status: "archived" as const },
    { ...first, id: 5, related_ids: { technical_audit_id: 11, priority_id: 5 } }];
  const groups = groupInbox(rows);
  assert.equal(groups.length, 4);
  assert.deepEqual(groups[0].members.map(e => e.id), [1, 2]);
  assert.equal(rows.length, 5);
});
