import assert from "node:assert/strict";
import test from "node:test";

import { technicalSEOPageState } from "./technical-seo-state.ts";
import type { TechnicalSEOSummary } from "./types.ts";


test("robots-limited summary remains on the technical page", () => {
  const summary = {
    measurement_state: "limited",
    audit: null,
  } as TechnicalSEOSummary;

  assert.equal(technicalSEOPageState(summary), "limited");
});


test("missing technical summary still routes to setup", () => {
  assert.equal(technicalSEOPageState(null), "setup");
});
