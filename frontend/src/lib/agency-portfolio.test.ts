import assert from "node:assert/strict";
import test from "node:test";
import { filterPortfolio, initialPortfolioFilters, type PortfolioClient } from "./agency-portfolio.ts";

const client = (values: Partial<PortfolioClient>): PortfolioClient => ({
  project_id: 1, project_name: "Client", target_brand: "Client", status: "healthy", status_reason: "No signal.",
  technical_seo: { status: "not_measured", score: null, pages_checked: null, audit_id: null },
  web_search: { status: "not_measured", value: null, trend: null, completed_at: null, benchmark_job_id: null, model: null },
  memory: { status: "not_measured", value: null, trend: null, completed_at: null, benchmark_job_id: null, model: null },
  site_rag: { status: "not_measured", value: null, trend: null, completed_at: null, benchmark_job_id: null, model: null },
  priorities: { open: 0, high: 0 }, inbox: { needs_attention: 0, high: 0 },
  monitoring: { state: "not_configured", enabled_modes: 0, problem_count: 0, next_due_at: null },
  report: { status: "missing", created_at: null, title: null }, last_meaningful_change: null,
  links: { project: "/projects/1", priorities: "/projects/1/priorities", monitoring: "/projects/1/monitoring", inbox: "/agency-inbox?project=1", reports: "/projects/1/client-reports" },
  ...values,
});

test("portfolio sorts attention, urgency, then recency without a synthetic score", () => {
  const rows = [client({ project_id: 1, project_name: "Stable", status: "monitoring" }),
    client({ project_id: 2, project_name: "Follow-up", status: "needs_attention", priorities: { open: 1, high: 1 } }),
    client({ project_id: 3, project_name: "Setup", status: "setup_required" })];
  assert.deepEqual(filterPortfolio(rows, initialPortfolioFilters).map((item) => item.project_id), [2, 3, 1]);
  assert.equal("score" in rows[0], false);
});

test("portfolio filters monitoring problems, high priorities, report and missing state independently", () => {
  const rows = [client({ project_id: 1, monitoring: { state: "problem", enabled_modes: 1, problem_count: 1, next_due_at: null } }),
    client({ project_id: 2, priorities: { open: 1, high: 1 }, report: { status: "published", created_at: "2026-09-01", title: "Report" } })];
  assert.deepEqual(filterPortfolio(rows, { ...initialPortfolioFilters, monitoring: "problem" }).map((item) => item.project_id), [1]);
  assert.deepEqual(filterPortfolio(rows, { ...initialPortfolioFilters, priorities: "high", report: "published" }).map((item) => item.project_id), [2]);
});

test("stable monitoring is not promoted to needs attention", () => {
  const stable = client({ status: "monitoring", monitoring: { state: "monitoring", enabled_modes: 1, problem_count: 0, next_due_at: "2026-09-10" } });
  assert.equal(filterPortfolio([stable], { ...initialPortfolioFilters, status: "needs_attention" }).length, 0);
});
