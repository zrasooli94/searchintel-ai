import Link from "next/link";

import {
  ArrowRight,
  FolderKanban,
  Globe2,
  Search,
  Users,
} from "lucide-react";

import NewProjectButton from "@/components/dashboard/new-project-button";

import {
  getProjectWorkspaces,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Home() {
  const workspaces =
    await getProjectWorkspaces();

  return (
    <main className="crystal-page min-h-screen">
      <div className="mx-auto max-w-[1240px] px-6 pb-20 pt-10 lg:px-10">
        <header className="flex items-center justify-between border-b border-slate-200/70 pb-8">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 grid-cols-3 gap-[3px]">
              {Array.from({
                length: 9,
              }).map(
                (_, index) => (
                  <span
                    key={index}
                    className={[
                      "rounded-full",
                      index % 2 === 0
                        ? "bg-[#7357ff]"
                        : "bg-[#42a5ff]",
                    ].join(" ")}
                  />
                ),
              )}
            </div>

            <div>
              <div className="text-[17px] font-semibold tracking-[-0.035em] text-slate-950">
                SearchIntel
              </div>

              <div className="mt-0.5 text-[11px] text-slate-400">
                Search Intelligence Platform
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4"><Link href="/agency-inbox" className="text-sm font-medium text-violet-700">Agency Inbox</Link><NewProjectButton /></div>
        </header>

        <section className="pt-14">
          <div className="crystal-eyebrow">
            Workspaces
          </div>

          <div className="mt-3 flex flex-col justify-between gap-5 md:flex-row md:items-end">
            <div>
              <h1 className="text-4xl font-medium tracking-[-0.055em] text-slate-950">
                Choose a project
              </h1>

              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
                Each workspace keeps its own target brand,
                website, competitors, experiments, entity
                knowledge and optimization plan.
              </p>
            </div>

            <div className="hidden text-right md:block">
              <div className="text-sm font-medium text-slate-900">
                {workspaces.length}
              </div>

              <div className="text-xs text-slate-400">
                configured workspaces
              </div>
            </div>
          </div>
        </section>

        {workspaces.length === 0 ? (
          <div className="crystal-panel mt-10 rounded-[24px] p-10">
            <div className="crystal-icon h-11 w-11">
              <FolderKanban className="h-5 w-5 text-[#5f75ff]" />
            </div>

            <h2 className="mt-6 text-xl font-medium text-slate-950">
              No projects yet
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Create a SearchIntel project to begin.
            </p>
          </div>
        ) : (
          <div className="mt-9 grid gap-6 lg:grid-cols-2">
            {workspaces.map(
              (workspace) => (
                <Link
                  key={workspace.id}
                  href={
                    workspace.completed_experiment_count > 0
                      ? `/projects/${workspace.id}`
                      : `/projects/${workspace.id}/setup`
                  }
                  className="crystal-panel group rounded-[24px] p-6 transition duration-300 hover:-translate-y-0.5 hover:border-violet-300/80 hover:shadow-[0_22px_60px_rgba(80,92,145,0.10)]"
                >
                  <div className="flex items-start justify-between gap-6">
                    <div>
                      <div className="crystal-eyebrow">
                        Project #{workspace.id}
                      </div>

                      <h2 className="mt-3 text-xl font-medium tracking-[-0.03em] text-slate-950">
                        {workspace.name}
                      </h2>

                      {workspace.description && (
                        <p className="mt-2 text-sm leading-6 text-slate-500">
                          {workspace.description}
                        </p>
                      )}
                    </div>

                    <div className="crystal-icon h-10 w-10 shrink-0 transition group-hover:translate-x-0.5">
                      <ArrowRight className="h-4 w-4 text-[#5f75ff]" />
                    </div>
                  </div>

                  <div className="mt-7 grid gap-3 sm:grid-cols-2">
                    <div className="crystal-subcard rounded-2xl p-4">
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <Search className="h-3.5 w-3.5" />
                        Target brand
                      </div>

                      <div className="mt-2 text-sm font-medium text-slate-900">
                        {workspace.target_brand ??
                          "Not configured"}
                      </div>
                    </div>

                    <div className="crystal-subcard rounded-2xl p-4">
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <Globe2 className="h-3.5 w-3.5" />
                        Primary domain
                      </div>

                      <div className="mt-2 truncate text-sm font-medium text-slate-900">
                        {workspace.domain ??
                          "Not configured"}
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs text-slate-500">
                      <Users className="h-3.5 w-3.5" />
                      {workspace.competitor_count} competitors
                    </span>

                    <span className="rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs text-slate-500">
                      {workspace.experiment_count} experiments
                    </span>

                    <span className="rounded-full border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs text-emerald-700">
                      {workspace.completed_experiment_count} completed
                    </span>
                  </div>

                  {workspace.latest_completed_experiment_name && (
                    <div className="mt-6 border-t border-slate-200/70 pt-4 text-xs text-slate-400">
                      Latest completed:{" "}
                      <span className="font-medium text-slate-700">
                        {
                          workspace.latest_completed_experiment_name
                        }
                      </span>
                    </div>
                  )}
                </Link>
              ),
            )}
          </div>
        )}
      </div>
    </main>
  );
}
