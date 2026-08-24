import ExperimentsDashboard from "@/components/dashboard/experiments-dashboard";

import {
  getExperimentComparison,
  getExperimentsSummary,
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


type Props = {
  params: Promise<{
    projectId: string;
  }>;
};


export default async function Page({
  params,
}: Props) {
  const {
    projectId: rawProjectId,
  } = await params;

  const projectId = Number(
    rawProjectId,
  );

  const [
    visibilitySummary,
    experiments,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(
      projectId,
    ),
    getExperimentsSummary(
      projectId,
    ),
  ]);

  const pair =
    experiments.comparable_pairs[0];

  const comparison = pair
    ? await getExperimentComparison(
        projectId,
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
