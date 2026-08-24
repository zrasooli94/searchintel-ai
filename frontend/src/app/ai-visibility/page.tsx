import AIVisibilityDashboard from "@/components/dashboard/ai-visibility-dashboard";

import {
  getLatestCompletedAIVisibilityMetrics,
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Page() {
  const [
    summary,
    metrics,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(),
    getLatestCompletedAIVisibilityMetrics(),
  ]);

  return (
    <AIVisibilityDashboard
      summary={summary}
      metrics={metrics}
    />
  );
}
