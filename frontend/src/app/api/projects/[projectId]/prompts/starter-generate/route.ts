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
    process.env
      .SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const body =
    await request.text();

  const response = await fetch(
    `${apiBase}/projects/${projectId}/prompts/starter-generate`,
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
