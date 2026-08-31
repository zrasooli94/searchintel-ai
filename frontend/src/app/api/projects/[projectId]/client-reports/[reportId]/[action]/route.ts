import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";
export async function POST(request: Request, { params }: { params: Promise<{ projectId: string; reportId: string; action: string }> }) {
  const denied = await operatorMutationGuard(); if (denied) return denied;
  const { projectId, reportId, action } = await params;
  if (!["publish", "unpublish", "revoke"].includes(action)) return Response.json({ detail: "Unknown action." }, { status: 404 });
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/projects/${projectId}/client-reports/${reportId}/${action}`, { method: "POST", headers: await operatorBackendHeaders(), body: await request.text() || "{}" });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}
