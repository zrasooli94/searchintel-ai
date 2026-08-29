export function competitorDiscoveryConfirmation(targetBrand: string) {
  return {
    target: targetBrand,
    method: "AI + Web Research",
    maxCandidates: 5,
    createsBenchmarkMetrics: false,
  };
}


export function canStartCompetitorDiscovery({
  operatorAuthorized,
  generating,
}: {
  operatorAuthorized: boolean;
  generating: boolean;
}) {
  return operatorAuthorized && !generating;
}
