import { notFound } from "next/navigation";
import ClientReportContent from "@/components/client-report-content";
import { getSharedClientReport } from "@/lib/api";

export const dynamic = "force-dynamic";
export const metadata = { title: "SearchIntel Client Report", robots: { index: false, follow: false } };

export default async function Page({ params }: { params: Promise<{ token: string }> }) {
  const token = (await params).token;
  let report;
  try { report = await getSharedClientReport(token); }
  catch { notFound(); }
  return <ClientReportContent report={report} publicView />;
}
