import assert from "node:assert/strict";
import test from "node:test";
import { monitoringConfirmation } from "./monitoring-safety.ts";

test("paid monitoring confirmation exposes frozen run size and cadence", () => {
  const result = monitoringConfirmation({ mode: "web_search", modelId: 3, promptCount: 19, cadenceHours: 168 });
  assert.deepEqual(result, { mode: "web_search", modelId: 3, promptCount: 19, runsPerCheck: 19, cadenceHours: 168, estimatedMonthlyRuns: 81, webSearchEnabled: true });
});

test("memory monitoring never presents web search as enabled", () => {
  assert.equal(monitoringConfirmation({ mode: "memory", modelId: 3, promptCount: 20, cadenceHours: 720 }).webSearchEnabled, false);
});
