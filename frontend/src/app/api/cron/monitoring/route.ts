import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";

export const maxDuration = 300;

export async function GET(request: Request) {
  const expected = process.env.CRON_SECRET?.trim();
  if (!expected || request.headers.get("authorization") !== `Bearer ${expected}`) {
    return Response.json({ detail: "Unauthorized." }, { status: 401 });
  }
  const apiToken = process.env.SEARCHINTEL_API_TOKEN?.trim();
  if (!apiToken) return Response.json({ detail: "Server configuration unavailable." }, { status: 503 });
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/monitoring/process-due`, { method: "POST", headers: { "X-SearchIntel-Operator": apiToken }, cache: "no-store" });
  return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
}
