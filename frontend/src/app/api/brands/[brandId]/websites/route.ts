import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";
import { operatorMutationGuard } from "@/lib/operator-session";


export async function POST(
  request: Request,
  context: {
    params: Promise<{
      brandId: string;
    }>;
  },
) {
  const denied = await operatorMutationGuard();
  if (denied) return denied;
  const { brandId } = await context.params;
  const body = await request.text();
  const response = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/brands/${brandId}/websites`,
    {
      method: "POST",
      body,
      cache: "no-store",
    },
  );
  return new Response(
    await response.text(),
    {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
      },
    },
  );
}
