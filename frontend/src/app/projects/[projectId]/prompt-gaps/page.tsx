import PromptGapsDashboard from "@/components/dashboard/prompt-gaps-dashboard";

import {
  getLatestCompletedPromptOpportunities,
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
    gaps,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(
      projectId,
    ),
    getLatestCompletedPromptOpportunities(
      projectId,
    ),
  ]);

  return (
    <PromptGapsDashboard
      visibilitySummary={visibilitySummary}
      gaps={gaps}
    />
  );
}
