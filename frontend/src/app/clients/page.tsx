import ClientsDashboard from "@/components/dashboard/clients-dashboard";
import { searchIntelApiBaseUrl, searchIntelFetch } from "@/lib/server-api";
import type { Portfolio } from "@/lib/agency-portfolio";

export const dynamic = "force-dynamic";

export default async function ClientsPage() {
  const response = await searchIntelFetch(`${searchIntelApiBaseUrl()}/clients`, { cache: "no-store" });
  if (!response.ok) throw new Error("The client portfolio is temporarily unavailable.");
  return <ClientsDashboard initial={await response.json() as Portfolio} />;
}
