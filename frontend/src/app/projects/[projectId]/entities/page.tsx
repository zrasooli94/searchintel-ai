import EntitiesDashboard from "@/components/dashboard/entities-dashboard";

import {
  getEntitiesSummary,
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
    entities,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(
      projectId,
    ),
    getEntitiesSummary(
      projectId,
    ),
  ]);

  return (
    <EntitiesDashboard
      visibilitySummary={
        visibilitySummary
      }
      entities={entities}
    />
  );
}
