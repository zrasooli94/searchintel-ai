import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";

export async function POST() {
  const denied = await operatorMutationGuard(); if (denied) return denied;
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/agency-inbox/reconcile`, {
    method: "POST", headers: await operatorBackendHeaders(), cache: "no-store",
  });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
