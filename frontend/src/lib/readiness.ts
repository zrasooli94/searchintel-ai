import type {
  MeasurementEligibility,
} from "@/lib/types";


export function canRunMeasurement(
  eligibility: MeasurementEligibility,
): boolean {
  return (
    eligibility.state !== "blocked"
    && eligibility.state !== "not_applicable"
    && eligibility.execution_available
  );
}


export function keepsHistoricalResultsVisible(
  eligibility: MeasurementEligibility,
): boolean {
  return eligibility.has_historical_results;
}
