import assert from "node:assert/strict";
import test from "node:test";

import {
  benchmarkConfirmation,
} from "./benchmark-confirmation.ts";


test("confirmation exposes run size and web-search use", () => {
  assert.deepEqual(
    benchmarkConfirmation("web_search", "gpt-test", 3),
    {
      measurementMode: "Web Search",
      model: "gpt-test",
      promptCount: 3,
      expectedAiRuns: 3,
      webSearchEnabled: true,
    },
  );
});


test("memory confirmation keeps web search disabled", () => {
  const metadata = benchmarkConfirmation("memory", "gpt-test", 1);
  assert.equal(metadata.expectedAiRuns, 1);
  assert.equal(metadata.webSearchEnabled, false);
});
