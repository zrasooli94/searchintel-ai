import PromptGapsDashboard from "@/components/dashboard/prompt-gaps-dashboard";

import {
  getLatestCompletedPromptOpportunities,
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Page() {
  const [
    visibilitySummary,
    gaps,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(),
    getLatestCompletedPromptOpportunities(),
  ]);

  return (
    <PromptGapsDashboard
      visibilitySummary={visibilitySummary}
      gaps={gaps}
    />
  );
}
