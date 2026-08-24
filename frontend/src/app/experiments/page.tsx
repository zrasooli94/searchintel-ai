import ExperimentsDashboard from "@/components/dashboard/experiments-dashboard";

import {
  getExperimentComparison,
  getExperimentsSummary,
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Page() {
  const [
    visibilitySummary,
    experiments,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(),
    getExperimentsSummary(),
  ]);

  const pair =
    experiments.comparable_pairs[0];

  const comparison = pair
    ? await getExperimentComparison(
        pair.baseline_id,
        pair.comparison_id,
      )
    : null;

  return (
    <ExperimentsDashboard
      visibilitySummary={
        visibilitySummary
      }
      experiments={experiments}
      comparison={comparison}
    />
  );
}
