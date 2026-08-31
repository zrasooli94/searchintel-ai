import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";
export async function POST(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const denied = await operatorMutationGuard(); if (denied) return denied;
  const { projectId } = await params;
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/projects/${projectId}/client-reports`, { method: "POST", headers: await operatorBackendHeaders(), body: await request.text() });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
