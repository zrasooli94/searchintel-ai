export async function GET(
  _request: Request,
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
    process.env
      .SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const response = await fetch(
    `${apiBase}/projects/${projectId}/prompts`,
    {
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
