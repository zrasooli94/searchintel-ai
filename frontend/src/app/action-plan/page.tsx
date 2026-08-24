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
      title='Action Plan'
      description='Turn technical, content, prompt, and visibility evidence into prioritized optimization actions.'
    />
  );
}
