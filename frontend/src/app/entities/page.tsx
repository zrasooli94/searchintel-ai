import EntitiesDashboard from "@/components/dashboard/entities-dashboard";

import {
  getEntitiesSummary,
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Page() {
  const [
    visibilitySummary,
    entities,
  ] = await Promise.all([
    getLatestCompletedVisibilitySummary(),
    getEntitiesSummary(),
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
