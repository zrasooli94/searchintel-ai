import ActionPlanDashboard from "@/components/dashboard/action-plan-dashboard";

import {
  getActionPlanSummary,
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
    plan,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(
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
      plan={plan}
    />
  );
}
