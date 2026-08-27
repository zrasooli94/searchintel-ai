import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";

export async function POST(
  _request: Request,
  context: {
    params: Promise<{
      projectId: string;
      experimentId: string;
    }>;
  },
) {
  const {
    projectId,
    experimentId,
  } = await context.params;

  const apiBase =
    searchIntelApiBaseUrl();

  const response = await searchIntelFetch(
    `${apiBase}/projects/${projectId}/experiments/${experimentId}/reanalyze-visibility?force=true`,
    {
      method: "POST",
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
