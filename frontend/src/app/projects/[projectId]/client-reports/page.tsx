import ClientReportsDashboard from "@/components/dashboard/client-reports-dashboard";
import { getClientReports, getProjectWorkspace } from "@/lib/api";
import { isOperatorSession } from "@/lib/operator-session";

export const dynamic = "force-dynamic";

export default async function Page({ params }: { params: Promise<{ projectId: string }> }) {
  const projectId = Number((await params).projectId);
  const operator = await isOperatorSession();
  const workspace = await getProjectWorkspace(projectId);
  if (!operator) return <div className="mx-auto mt-24 max-w-xl rounded-3xl border border-slate-200 bg-white p-10 text-center"><h1 className="text-2xl font-medium">Client Reports</h1><p className="mt-3 text-slate-500">Authorized operator access is required to create, list, publish, revoke, or export private client reports.</p></div>;
  const reports = await getClientReports(projectId);
  return <ClientReportsDashboard initialReports={reports} shellSummary={{ project_id: projectId, target: { brand: workspace.target_brand ?? workspace.name }, experiment_name: workspace.latest_completed_experiment_name ?? "No completed measurement", experiment_status: workspace.latest_completed_experiment_id ? "Completed" : "Setup" }} />;
}
