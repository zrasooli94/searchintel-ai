import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";

export async function POST(
  _request: Request,
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

  const response = await searchIntelFetch(
    `${apiBase}/websites/${websiteId}/technical-audit`,
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
