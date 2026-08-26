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
    process.env.SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const response = await fetch(
    `${apiBase}/projects/${projectId}/experiments/${experimentId}/reanalyze-visibility`,
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
