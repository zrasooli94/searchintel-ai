import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";

export async function POST(
  request: Request,
  context: {
    params: Promise<{
      websiteId: string;
    }>;
  },
) {
  const {
    websiteId,
  } = await context.params;

  const apiBase =
    searchIntelApiBaseUrl();

  const incomingUrl =
    new URL(request.url);

  const maxPages =
    incomingUrl.searchParams.get(
      "max_pages",
    ) ?? "25";

  const response = await searchIntelFetch(
    `${apiBase}/websites/${websiteId}/crawl?max_pages=${encodeURIComponent(maxPages)}`,
    {
      method: "POST",
      cache: "no-store",
    },
  );

  const payload =
    await response.text();

  return new Response(
    payload,
    {
      status: response.status,
      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}
