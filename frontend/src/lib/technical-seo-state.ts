import type { TechnicalSEOSummary } from "@/lib/types";


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
