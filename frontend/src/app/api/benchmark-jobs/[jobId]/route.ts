export async function GET(
  _request: Request,
  context: {
    params: Promise<{
      jobId: string;
    }>;
  },
) {
  const {
    jobId,
  } = await context.params;

  const apiBase =
    process.env.SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1";

  const response = await fetch(
    `${apiBase}/benchmark-jobs/${jobId}`,
    {
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
