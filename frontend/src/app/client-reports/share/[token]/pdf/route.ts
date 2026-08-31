import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";
export async function GET(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/client-reports/share/${encodeURIComponent(token)}/pdf`, { cache: "no-store" });
  return new Response(response.body, { status: response.status, headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/pdf", "Content-Disposition": response.headers.get("Content-Disposition") ?? "attachment; filename=searchintel-report.pdf", "X-Robots-Tag": "noindex, nofollow, noarchive" } });
}
