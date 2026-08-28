import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";
import { operatorBackendHeaders, operatorMutationGuard } from "@/lib/operator-session";

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
    `${apiBase}/projects/${projectId}/benchmark-jobs`,
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
    `${apiBase}/projects/${projectId}/benchmark-jobs`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
        ...await operatorBackendHeaders(),
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
