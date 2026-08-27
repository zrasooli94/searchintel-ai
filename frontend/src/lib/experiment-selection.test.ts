import assert from "node:assert/strict";
import test from "node:test";

import {
  latestCompletedExperimentForMode,
} from "./experiment-selection.ts";


test("selects completed experiments independently by measurement mode", () => {
  const experiments = [
    {
      id: 7,
      status: "completed",
      benchmark_mode: "web_search",
      competitor_names: ["Competitor A", "Competitor B"],
    },
    {
      id: 8,
      status: "completed",
      benchmark_mode: "site_rag",
      competitor_names: [],
    },
  ];

  const webExperiment = latestCompletedExperimentForMode(
    experiments,
    "web_search",
  );
  const siteRAGExperiment = latestCompletedExperimentForMode(
    experiments,
    "site_rag",
  );

  assert.equal(webExperiment?.id, 7);
  assert.deepEqual(
    webExperiment?.competitor_names,
    ["Competitor A", "Competitor B"],
  );
  assert.equal(siteRAGExperiment?.id, 8);
});


test("ignores newer draft experiments in the requested mode", () => {
  const selected = latestCompletedExperimentForMode(
    [
      {
        id: 7,
        status: "completed",
        benchmark_mode: "web_search",
      },
      {
        id: 11,
        status: "draft",
        benchmark_mode: "web_search",
      },
    ],
    "web_search",
  );

  assert.equal(selected?.id, 7);
});


test("returns null when the requested mode has no completed experiment", () => {
  const selected = latestCompletedExperimentForMode(
    [
      {
        id: 8,
        status: "completed",
        benchmark_mode: "site_rag",
      },
    ],
    "web_search",
  );

  assert.equal(selected, null);
});
