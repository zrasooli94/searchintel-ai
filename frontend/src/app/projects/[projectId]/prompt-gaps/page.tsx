import PromptGapsDashboard from "@/components/dashboard/prompt-gaps-dashboard";

import {
  getLatestCompletedPromptGapContext,
  getLatestCompletedSiteRAGGaps,
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
    webContext,
    siteRagGaps,
  ] = await Promise.all([
    getLatestCompletedPromptGapContext(
      projectId,
    ),
    getLatestCompletedSiteRAGGaps(
      projectId,
    ),
  ]);

  const {
    visibilitySummary,
    gaps,
  } = webContext;

  return (
    <PromptGapsDashboard
      visibilitySummary={visibilitySummary}
      gaps={gaps}
      siteRagGaps={siteRagGaps}
    />
  );
}
