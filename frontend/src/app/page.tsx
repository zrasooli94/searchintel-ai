import OverviewDashboard from "@/components/dashboard/overview-dashboard";

import {
  getLatestCompletedVisibilitySummary,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Home() {
  let summary = null;
  let errorMessage: string | null = null;

  try {
    summary =
      await getLatestCompletedVisibilitySummary();
  } catch (error) {
    errorMessage =
      error instanceof Error
        ? error.message
        : "Unknown dashboard error.";
  }

  if (!summary) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
        <div className="max-w-lg rounded-2xl border border-red-500/20 bg-slate-900 p-8">
          <div className="text-sm font-medium text-red-400">
            SearchIntel API unavailable
          </div>

          <h1 className="mt-3 text-2xl font-semibold text-white">
            Dashboard could not load
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            {errorMessage}
          </p>

          <p className="mt-5 text-xs text-slate-500">
            Make sure the FastAPI backend is running
            on port 8000.
          </p>
        </div>
      </main>
    );
  }

  return (
    <OverviewDashboard
      summary={summary}
    />
  );
}
