import MonitoringDashboard from "@/components/dashboard/monitoring-dashboard";
import { getProjectMonitoring, getProjectWorkspace } from "@/lib/api";
import { isOperatorSession } from "@/lib/operator-session";

export const dynamic = "force-dynamic";

export default async function Page({ params }: { params: Promise<{ projectId: string }> }) {
  const projectId = Number((await params).projectId);
  const [initial, workspace, operatorAuthorized] = await Promise.all([getProjectMonitoring(projectId), getProjectWorkspace(projectId), isOperatorSession()]);
  return <MonitoringDashboard initial={initial} operatorAuthorized={operatorAuthorized} shellSummary={{ project_id: projectId, target: { brand: workspace.target_brand ?? workspace.name }, experiment_name: workspace.latest_completed_experiment_name ?? "No completed measurement", experiment_status: workspace.latest_completed_experiment_id ? "Completed" : "Setup" }}/>;
}
