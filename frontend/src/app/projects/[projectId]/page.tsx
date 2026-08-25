import {
  redirect,
} from "next/navigation";

import OverviewDashboard from "@/components/dashboard/overview-dashboard";

import {
  getLatestCompletedVisibilitySummary,
  getProjectWorkspace,
} from "@/lib/api";


export const dynamic =
  "force-dynamic";


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

  const projectId =
    Number(rawProjectId);

  const workspace =
    await getProjectWorkspace(
      projectId
    );

  if (
    workspace
      .completed_experiment_count
    === 0
  ) {
    redirect(
      `/projects/${projectId}/setup`
    );
  }

  const summary =
    await getLatestCompletedVisibilitySummary(
      projectId
    );

  return (
    <OverviewDashboard
      summary={summary}
    />
  );
}
