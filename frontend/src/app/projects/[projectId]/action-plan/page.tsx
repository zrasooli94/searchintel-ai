import ActionPlanDashboard from "@/components/dashboard/action-plan-dashboard";

import {
  getActionPlanSummary,
  getLatestCompletedVisibilitySummary,
  getLatestCompletedWebVisibilitySummary,
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
    webVisibilitySummary,
    plan,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(
      projectId,
    ),
    getLatestCompletedWebVisibilitySummary(
      projectId,
    ),
    getActionPlanSummary(
      projectId,
    ),
  ]);

  return (
    <ActionPlanDashboard
      visibilitySummary={
        visibilitySummary
      }
      webVisibilitySummary={
        webVisibilitySummary
      }
      plan={plan}
    />
  );
}
