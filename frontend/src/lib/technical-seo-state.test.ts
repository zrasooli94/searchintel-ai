import assert from "node:assert/strict";
import test from "node:test";

import {
  technicalSEOCoveragePresentation,
  technicalSEOPageState,
  technicalSEOShellSummary,
} from "./technical-seo-state.ts";
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


test("single-page audit is explicitly presented as a limited sample", () => {
  const summary = {
    coverage_state: "limited_sample",
    coverage_label: "LIMITED SAMPLE",
    coverage_reason: "Findings apply to the crawled sample.",
  } as TechnicalSEOSummary;

  const presentation = technicalSEOCoveragePresentation(summary);

  assert.equal(presentation.scoreLabel, "Sample Score");
  assert.equal(presentation.showLimitedWarning, true);
  assert.match(presentation.coverageReason, /crawled sample/i);
  assert.doesNotMatch(presentation.coverageReason, /site-wide|entire site/i);
});


test("healthy multi-page audit preserves normal score presentation", () => {
  const summary = {
    coverage_state: "bounded_sample",
    coverage_label: "BOUNDED SAMPLE",
    coverage_reason: "Findings reflect 10 analyzed pages.",
  } as TechnicalSEOSummary;

  const presentation = technicalSEOCoveragePresentation(summary);

  assert.equal(presentation.scoreLabel, "Site Health");
  assert.equal(presentation.showLimitedWarning, false);
});


test("completed technical audit renders without a web-search experiment", () => {
  const summary = {
    project_id: 8,
    measurement_state: "ready",
    website: { brand: "Vercel" },
    audit: { id: 7 },
  } as TechnicalSEOSummary;

  const shell = technicalSEOShellSummary(summary);

  assert.equal(shell.project_id, 8);
  assert.equal(shell.target.brand, "Vercel");
  assert.equal(shell.experiment_name, "Technical Audit V1");
  assert.equal(shell.experiment_status, "completed");
});
