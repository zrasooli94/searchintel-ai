import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";

export async function GET() {
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/agency-inbox`, { cache: "no-store" });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
}
