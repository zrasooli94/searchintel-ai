import TechnicalSEODashboard from "@/components/dashboard/technical-seo-dashboard";

import {
  getLatestCompletedVisibilitySummary,
  getTechnicalSEOSummary,
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
    seo,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(
      projectId,
    ),
    getTechnicalSEOSummary(
      projectId,
    ),
  ]);

  return (
    <TechnicalSEODashboard
      visibilitySummary={visibilitySummary}
      seo={seo}
    />
  );
}
