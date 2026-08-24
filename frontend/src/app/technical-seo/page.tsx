import TechnicalSEODashboard from "@/components/dashboard/technical-seo-dashboard";

import {
  getLatestCompletedVisibilitySummary,
  getTechnicalSEOSummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Page() {
  const [
    visibilitySummary,
    seo,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(),
    getTechnicalSEOSummary(),
  ]);

  return (
    <TechnicalSEODashboard
      visibilitySummary={visibilitySummary}
      seo={seo}
    />
  );
}
