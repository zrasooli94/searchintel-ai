import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";
import { operatorMutationGuard } from "@/lib/operator-session";

export async function POST(
  request: Request,
) {
  const denied = await operatorMutationGuard();
  if (denied) return denied;
  const apiBase =
    searchIntelApiBaseUrl();

  const body = await request.text();

  const response = await searchIntelFetch(
    `${apiBase}/projects/onboard`,
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
