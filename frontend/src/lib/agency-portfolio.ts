export type Trend = { state: "improved" | "declined" | "stable"; delta: number; previous: number; compatible: true } | null;
export type Measurement = { status: string; value: number | null; trend: Trend; completed_at: string | null; benchmark_job_id: number | null; model: string | null; prompt_count?: number };
export type PortfolioClient = {
  project_id: number; project_name: string; target_brand: string | null;
  status: "needs_attention" | "monitoring" | "healthy" | "setup_required"; status_reason: string;
  technical_seo: { status: string; score: number | null; pages_checked: number | null; audit_id: number | null };
  web_search: Measurement; memory: Measurement; site_rag: Measurement;
  priorities: { open: number; high: number }; inbox: { needs_attention: number; high: number };
  monitoring: { state: string; enabled_modes: number; problem_count: number; next_due_at: string | null };
  report: { status: string; created_at: string | null; title: string | null };
  last_meaningful_change: { title: string; summary: string; source_mode: string; occurred_at: string; path: string } | null;
  links: { project: string; priorities: string; monitoring: string; inbox: string; reports: string };
};
export type Portfolio = {
  summary: { clients: number; needs_attention: number; high_severity_alerts: number; high_priorities: number; monitoring_problems: number; reports_missing: number };
  clients: PortfolioClient[]; generated_at: string; provenance_note: string;
};
export type PortfolioFilters = { status: string; monitoring: string; priorities: string; report: string };
export const initialPortfolioFilters: PortfolioFilters = { status: "", monitoring: "", priorities: "", report: "" };
const statusRank = { needs_attention: 0, setup_required: 1, monitoring: 2, healthy: 3 };

export function filterPortfolio(clients: PortfolioClient[], filters: PortfolioFilters) {
  return clients.filter((client) => (!filters.status || client.status === filters.status)
    && (!filters.monitoring || (filters.monitoring === "problem" ? client.monitoring.problem_count > 0 : client.monitoring.state === filters.monitoring))
    && (!filters.priorities || (filters.priorities === "high" ? client.priorities.high > 0 : client.priorities.open > 0))
    && (!filters.report || client.report.status === filters.report))
    .sort((a, b) => statusRank[a.status] - statusRank[b.status]
      || b.monitoring.problem_count - a.monitoring.problem_count
      || b.inbox.high - a.inbox.high || b.priorities.high - a.priorities.high
      || Date.parse(b.last_meaningful_change?.occurred_at ?? "1970-01-01") - Date.parse(a.last_meaningful_change?.occurred_at ?? "1970-01-01")
      || a.project_name.localeCompare(b.project_name));
}
