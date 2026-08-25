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
    process.env.SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const response = await fetch(
    `${apiBase}/projects/${projectId}/benchmark-jobs`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: await request.text(),
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
