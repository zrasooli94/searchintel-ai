import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";

export async function PATCH(request: Request, { params }: { params: Promise<{ eventId: string }> }) {
  const denied = await operatorMutationGuard(); if (denied) return denied;
  const { eventId } = await params;
  if (!/^\d+$/.test(eventId)) return Response.json({ detail: "Invalid event." }, { status: 400 });
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/agency-inbox/${eventId}`, {
    method: "PATCH", headers: { "Content-Type": "application/json", ...await operatorBackendHeaders() },
    body: await request.text(), cache: "no-store",
  });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
