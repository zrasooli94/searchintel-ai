export function canGeneratePromptProposal(input: {
  operatorAuthorized: boolean;
  generating: boolean;
  scope: "brand_wide" | "focused";
  focus: string;
}): boolean {
  return input.operatorAuthorized
    && !input.generating
    && (input.scope === "brand_wide" || input.focus.trim().length > 0);
}

export function proposalConfirmation(input: {
  target: string;
  scope: "brand_wide" | "focused";
  pageCount: number;
  competitorCount: number;
  promptCount: number;
}) {
  return {
    ...input,
    createsProposalOnly: true,
    createsBenchmark: false,
  };
}

export function brandWideCoverageSummary(input: {
  status: "balanced" | "needs_review" | "focused";
  largestTopicFamilyShare: number;
  checklist: Record<string, boolean>;
}) {
  return {
    status: input.status,
    largestTopicFamilyPercent: Math.round(input.largestTopicFamilyShare * 1000) / 10,
    represented: Object.values(input.checklist).filter(Boolean).length,
    total: Object.keys(input.checklist).length,
    isBalanced: input.status === "balanced" && Object.values(input.checklist).every(Boolean),
    constraintNote: "SearchIntel measurement-quality constraint; not an industry standard.",
  };
}
