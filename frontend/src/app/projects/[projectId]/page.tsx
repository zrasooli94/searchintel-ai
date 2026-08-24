import OverviewDashboard from "@/components/dashboard/overview-dashboard";

import {
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

  const summary =
    await getLatestCompletedVisibilitySummary(
      projectId,
    );

  return (
    <OverviewDashboard
      summary={summary}
    />
  );
}
