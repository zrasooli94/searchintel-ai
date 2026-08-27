export type ExperimentSelectionCandidate = {
  id: number;
  status: string;
  benchmark_mode: string;
};


export function latestCompletedExperimentForMode<
  T extends ExperimentSelectionCandidate,
>(
  experiments: readonly T[],
  benchmarkMode: string,
): T | null {
  return experiments
    .filter(
      (experiment) =>
        experiment.status === "completed"
        && experiment.benchmark_mode === benchmarkMode,
    )
    .sort(
      (a, b) => b.id - a.id,
    )[0] ?? null;
}
