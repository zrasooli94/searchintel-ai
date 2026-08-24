import SectionPage from "@/components/dashboard/section-page";
import {
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  const summary =
    await getLatestCompletedVisibilitySummary();

  return (
    <SectionPage
      summary={summary}
      title='AI Visibility'
      description='Analyze brand mentions, retrieval, citations, grounded exposure, and AI search visibility.'
    />
  );
}
