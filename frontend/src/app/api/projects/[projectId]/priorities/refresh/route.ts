import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";

export async function POST(_request: Request, context: { params: Promise<{ projectId: string }> }) {
  const denied = await operatorMutationGuard();
  if (denied) return denied;
  const { projectId } = await context.params;
  const response = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/priorities/refresh`,
    { method: "POST", headers: await operatorBackendHeaders(), cache: "no-store" },
  );
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
