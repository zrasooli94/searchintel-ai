import assert from "node:assert/strict";
import test from "node:test";

import {
  canStartCompetitorDiscovery,
  competitorDiscoveryConfirmation,
} from "./competitor-discovery-state.ts";


test("confirmation describes bounded onboarding research without benchmark metrics", () => {
  assert.deepEqual(
    competitorDiscoveryConfirmation("Vercel"),
    {
      target: "Vercel",
      method: "AI + Web Research",
      maxCandidates: 5,
      createsBenchmarkMetrics: false,
    },
  );
});


test("viewer and duplicate in-flight submissions cannot start discovery", () => {
  assert.equal(canStartCompetitorDiscovery({ operatorAuthorized: false, generating: false }), false);
  assert.equal(canStartCompetitorDiscovery({ operatorAuthorized: true, generating: true }), false);
  assert.equal(canStartCompetitorDiscovery({ operatorAuthorized: true, generating: false }), true);
});
