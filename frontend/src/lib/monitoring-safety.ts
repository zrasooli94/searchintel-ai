export function estimatedMonthlyRuns(promptCount: number, cadenceHours: number): number {
  return Math.round((720 / cadenceHours) * promptCount);
}

export function monitoringConfirmation(input: { mode: string; modelId: number; promptCount: number; cadenceHours: number }) {
  return {
    mode: input.mode,
    modelId: input.modelId,
    promptCount: input.promptCount,
    runsPerCheck: input.promptCount,
    cadenceHours: input.cadenceHours,
    estimatedMonthlyRuns: estimatedMonthlyRuns(input.promptCount, input.cadenceHours),
    webSearchEnabled: input.mode === "web_search",
  };
}
