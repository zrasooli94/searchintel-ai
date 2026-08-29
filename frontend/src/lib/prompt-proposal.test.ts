import assert from "node:assert/strict";
import test from "node:test";

import { canGeneratePromptProposal, proposalConfirmation } from "./prompt-proposal.ts";

test("viewer cannot generate and focused scope requires a focus label", () => {
  assert.equal(canGeneratePromptProposal({ operatorAuthorized: false, generating: false, scope: "brand_wide", focus: "" }), false);
  assert.equal(canGeneratePromptProposal({ operatorAuthorized: true, generating: false, scope: "focused", focus: "" }), false);
  assert.equal(canGeneratePromptProposal({ operatorAuthorized: true, generating: false, scope: "focused", focus: "AI Gateway" }), true);
});

test("generation confirmation is configuration-only and exposes source size", () => {
  const result = proposalConfirmation({ target: "Example", scope: "brand_wide", pageCount: 25, competitorCount: 3, promptCount: 19 });
  assert.equal(result.createsProposalOnly, true);
  assert.equal(result.createsBenchmark, false);
  assert.equal(result.pageCount, 25);
  assert.equal(result.promptCount, 19);
});
