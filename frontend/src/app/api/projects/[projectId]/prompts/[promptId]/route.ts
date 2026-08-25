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
    process.env.SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const body =
    await request.text();

  const response = await fetch(
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
