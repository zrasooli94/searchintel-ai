import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";
export async function GET(_request: Request, { params }: { params: Promise<{ projectId: string; reportId: string }> }) {
  const denied = await operatorMutationGuard(); if (denied) return denied;
  const { projectId, reportId } = await params;
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/projects/${projectId}/client-reports/${reportId}/pdf`, { headers: await operatorBackendHeaders(), cache: "no-store" });
  return new Response(response.body, { status: response.status, headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/pdf", "Content-Disposition": response.headers.get("Content-Disposition") ?? "attachment; filename=searchintel-report.pdf" } });
}
