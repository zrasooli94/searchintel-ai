import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";

export async function PATCH(request: Request, context: { params: Promise<{ projectId: string; priorityId: string }> }) {
  const denied = await operatorMutationGuard();
  if (denied) return denied;
  const { projectId, priorityId } = await context.params;
  const response = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/priorities/${priorityId}`,
    { method: "PATCH", headers: await operatorBackendHeaders(), body: await request.text(), cache: "no-store" },
  );
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
