import AIVisibilityDashboard from "@/components/dashboard/ai-visibility-dashboard";

import {
  getLatestCompletedAIVisibilityMetrics,
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
    summary,
    metrics,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(
      projectId,
    ),
    getLatestCompletedAIVisibilityMetrics(
      projectId,
    ),
  ]);

  return (
    <AIVisibilityDashboard
      summary={summary}
      metrics={metrics}
    />
  );
}
