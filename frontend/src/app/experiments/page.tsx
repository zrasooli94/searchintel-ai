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
      title='Experiments'
      description='Compare controlled SEO and GEO measurement runs across baseline and optimization experiments.'
    />
  );
}
