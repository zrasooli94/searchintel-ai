import TechnicalSEODashboard from "@/components/dashboard/technical-seo-dashboard";

import {
  redirect,
} from "next/navigation";

import {
  getLatestCompletedVisibilitySummary,
  getTechnicalSEOSummary,
} from "@/lib/api";
import { technicalSEOPageState } from "@/lib/technical-seo-state";


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

  const seo = await getTechnicalSEOSummary(
    projectId,
  );

  if (technicalSEOPageState(seo) === "setup") {
    redirect(
      `/projects/${projectId}/setup`,
    );
  }

  if (!seo) return null;

  const visibilitySummary =
    await getLatestCompletedVisibilitySummary(
      projectId,
    );

  return (
    <TechnicalSEODashboard
      visibilitySummary={visibilitySummary}
      seo={seo}
    />
  );
}
