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
