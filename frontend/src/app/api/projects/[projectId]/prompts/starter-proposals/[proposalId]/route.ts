import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";
import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";

export async function PUT(request: Request, context: { params: Promise<{ projectId: string; proposalId: string }> }) {
  const denied = await operatorMutationGuard();
  if (denied) return denied;
  const { projectId, proposalId } = await context.params;
  const response = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/prompts/starter-proposals/${proposalId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...await operatorBackendHeaders() },
      body: await request.text(),
      cache: "no-store",
    },
  );
  return new Response(await response.text(), {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
