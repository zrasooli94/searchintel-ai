import assert from "node:assert/strict";
import test from "node:test";
import { filterInbox, inboxCounts, initialInboxFilters, type InboxEvent } from "./agency-inbox.ts";

const events = [
  { id: 1, project_id: 4, severity: "high", source_mode: "site_rag", event_type: "priority_new_high", status: "unread" },
  { id: 2, project_id: 8, severity: "low", source_mode: "technical_seo", event_type: "score_improved", status: "read" },
  { id: 3, project_id: 4, severity: "high", source_mode: "web_search", event_type: "monitoring_failed", status: "archived" },
] as InboxEvent[];
test("Inbox filters combine and preserve project/mode boundaries", () => {
  assert.deepEqual(filterInbox(events, initialInboxFilters).map(e => e.id), [1, 2]);
  assert.deepEqual(filterInbox(events, { ...initialInboxFilters, project: "4", mode: "site_rag", severity: "high", type: "priority_new_high", status: "unread" }).map(e => e.id), [1]);
  assert.deepEqual(filterInbox(events, { ...initialInboxFilters, status: "archived" }).map(e => e.id), [3]);
  assert.equal(filterInbox(events, { ...initialInboxFilters, project: "8", mode: "site_rag" }).length, 0);
});
test("Archived events remain available but do not inflate active summary", () => {
  assert.deepEqual(inboxCounts(events), { Unread: 1, "High severity": 1, "Failed / Overdue": 0, Improvements: 1 });
});
