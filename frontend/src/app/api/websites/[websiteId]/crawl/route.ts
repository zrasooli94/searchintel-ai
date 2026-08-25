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
    process.env
      .SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const incomingUrl =
    new URL(request.url);

  const maxPages =
    incomingUrl.searchParams.get(
      "max_pages",
    ) ?? "25";

  const response = await fetch(
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
