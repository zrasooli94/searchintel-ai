import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";

export async function POST(
  request: Request,
  context: {
    params: Promise<{
      projectId: string;
    }>;
  },
) {
  const {
    projectId,
  } = await context.params;

  const apiBase =
    searchIntelApiBaseUrl();

  const body =
    await request.text();

  const response = await searchIntelFetch(
    `${apiBase}/projects/${projectId}/prompts/bulk`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body,
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
