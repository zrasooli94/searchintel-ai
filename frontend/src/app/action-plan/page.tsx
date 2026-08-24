import ActionPlanDashboard from "@/components/dashboard/action-plan-dashboard";

import {
  getActionPlanSummary,
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Page() {
  const [
    visibilitySummary,
    plan,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(),
    getActionPlanSummary(),
  ]);

  return (
    <ActionPlanDashboard
      visibilitySummary={
        visibilitySummary
      }
      plan={plan}
    />
  );
}
