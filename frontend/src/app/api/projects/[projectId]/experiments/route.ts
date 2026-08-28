import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";
import { operatorMutationGuard } from "@/lib/operator-session";

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
    searchIntelApiBaseUrl();

  const response = await searchIntelFetch(
    `${apiBase}/projects/${projectId}/geo-experiments`,
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


export async function POST(
  request: Request,
  context: {
    params: Promise<{
      projectId: string;
    }>;
  },
) {
  const denied = await operatorMutationGuard();
  if (denied) return denied;
  const {
    projectId,
  } = await context.params;

  const apiBase =
    searchIntelApiBaseUrl();

  const response = await searchIntelFetch(
    `${apiBase}/projects/${projectId}/geo-experiments`,
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
