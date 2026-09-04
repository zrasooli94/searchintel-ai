import AgencyInbox from "@/components/dashboard/agency-inbox";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";
import { isOperatorSession } from "@/lib/operator-session";

export const dynamic = "force-dynamic";

export default async function Page() {
  const [response, operator] = await Promise.all([
    searchIntelFetch(`${searchIntelApiBaseUrl()}/agency-inbox`, { cache: "no-store" }), isOperatorSession(),
  ]);
  if (!response.ok) throw new Error("Agency Inbox is temporarily unavailable.");
  return <AgencyInbox initial={await response.json()} operator={operator}/>;
}
