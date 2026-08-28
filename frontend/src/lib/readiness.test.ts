import assert from "node:assert/strict";
import test from "node:test";

import type {
  MeasurementEligibility,
} from "./types";
import {
  canRunMeasurement,
  keepsHistoricalResultsVisible,
} from "./readiness.ts";


function eligibility(
  overrides: Partial<MeasurementEligibility>,
): MeasurementEligibility {
  return {
    mode: "site_rag",
    state: "ready",
    reason: "Ready.",
    evidence: [],
    blocking_issues: [],
    warnings: [],
    recommended_action: "Run.",
    execution_available: true,
    execution_note: "Available.",
    has_historical_results: false,
    ...overrides,
  };
}


test("blocked measurements cannot start", () => {
  assert.equal(
    canRunMeasurement(eligibility({ state: "blocked" })),
    false,
  );
});


test("execution availability is separate from configuration readiness", () => {
  assert.equal(
    canRunMeasurement(eligibility({ execution_available: false })),
    false,
  );
});


test("historical visibility survives a blocked future run", () => {
  const item = eligibility({
    state: "blocked",
    execution_available: false,
    has_historical_results: true,
  });

  assert.equal(canRunMeasurement(item), false);
  assert.equal(keepsHistoricalResultsVisible(item), true);
});
