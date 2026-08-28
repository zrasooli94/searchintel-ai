import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";
import { operatorMutationGuard } from "@/lib/operator-session";

export async function POST(
  _request: Request,
  context: {
    params: Promise<{
      websiteId: string;
    }>;
  },
) {
  const denied = await operatorMutationGuard();
  if (denied) return denied;
  const {
    websiteId,
  } = await context.params;

  const apiBase =
    searchIntelApiBaseUrl();

  const response = await searchIntelFetch(
    `${apiBase}/websites/${websiteId}/technical-audit`,
    {
      method: "POST",
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
