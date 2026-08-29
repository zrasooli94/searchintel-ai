import type { TechnicalSEOSummary } from "@/lib/types";
import type { DashboardShellSummary } from "@/components/dashboard/dashboard-shell";


export function technicalSEOPageState(
  summary: TechnicalSEOSummary | null,
): "setup" | "limited" | "audit" {
  if (summary === null) return "setup";
  if (
    summary.measurement_state === "limited"
    || summary.audit === null
  ) {
    return "limited";
  }
  return "audit";
}


export function technicalSEOCoveragePresentation(
  summary: TechnicalSEOSummary,
) {
  const limitedSample =
    summary.coverage_state === "limited_sample";

  return {
    scoreLabel: limitedSample
      ? "Sample Score"
      : "Site Health",
    coverageLabel: summary.coverage_label,
    coverageReason: summary.coverage_reason,
    showLimitedWarning: limitedSample,
  };
}


export function technicalSEOShellSummary(
  summary: TechnicalSEOSummary,
  visibility: DashboardShellSummary | null,
): DashboardShellSummary {
  return visibility ?? {
    project_id: summary.project_id,
    target: {
      brand: summary.website.brand,
    },
    experiment_name: "Technical Audit V1",
    experiment_status: summary.audit
      ? "completed"
      : summary.measurement_state,
  };
}
