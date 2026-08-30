import assert from "node:assert/strict";
import test from "node:test";

import { activePromptSet, brandWideCoverageSummary, canGeneratePromptProposal, proposalConfirmation } from "./prompt-proposal.ts";

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

test("brand-wide coverage exposes macro-family review without claiming an industry standard", () => {
  const result = brandWideCoverageSummary({
    status: "needs_review",
    largestTopicFamilyShare: 0.526,
    largestSuperThemeShare: 0.632,
    checklist: { core_category: true, unbranded_recommendation: false },
  });
  assert.equal(result.largestTopicFamilyPercent, 52.6);
  assert.equal(result.largestSuperThemePercent, 63.2);
  assert.equal(result.isBalanced, false);
  assert.match(result.constraintNote, /not an industry standard/i);
});

test("current prompt set excludes inactive history after replacement", () => {
  const prompts = Array.from({ length: 38 }, (_, index) => ({
    id: index + 1,
    project_id: 8,
    text: `Prompt ${index + 1}`,
    category: index % 2 === 0 ? "comparison" : "recommendation",
    intent: null,
    is_active: index >= 19,
    created_at: "2026-08-30T00:00:00Z",
    updated_at: "2026-08-30T00:00:00Z",
  }));

  const active = activePromptSet(prompts);
  assert.equal(active.length, 19);
  assert.deepEqual(active.map((prompt) => prompt.id), Array.from({ length: 19 }, (_, index) => index + 20));
});
