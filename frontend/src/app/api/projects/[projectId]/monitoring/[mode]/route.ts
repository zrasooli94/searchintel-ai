import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";

export async function PUT(request: Request, { params }: { params: Promise<{ projectId: string; mode: string }> }) {
  const denied = await operatorMutationGuard(); if (denied) return denied;
  const { projectId, mode } = await params;
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/projects/${projectId}/monitoring/${mode}`, { method: "PUT", headers: { "Content-Type": "application/json", ...await operatorBackendHeaders() }, body: await request.text(), cache: "no-store" });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
