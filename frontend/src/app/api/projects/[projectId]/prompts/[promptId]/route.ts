import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";

export async function PUT(
  request: Request,
  context: {
    params: Promise<{
      projectId: string;
      promptId: string;
    }>;
  },
) {
  const {
    projectId,
    promptId,
  } = await context.params;

  const apiBase =
    searchIntelApiBaseUrl();

  const body =
    await request.text();

  const response = await searchIntelFetch(
    `${apiBase}/projects/${projectId}/prompts/${promptId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type":
          "application/json",
      },
      body,
      cache: "no-store",
    },
  );

  return new Response(
    await response.text(),
    {
      status: response.status,
      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}
