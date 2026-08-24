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
      title='Prompt Gaps'
      description='Find high-value prompts where competitors appear but the target brand has weak or missing visibility.'
    />
  );
}
