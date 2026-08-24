import Link from "next/link";

import {
  ArrowRight,
  FolderKanban,
  Globe2,
  Search,
  Sparkles,
  Users,
} from "lucide-react";

import {
  getProjectWorkspaces,
} from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function Home() {
  const workspaces =
    await getProjectWorkspaces();

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-14">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-cyan-400/10 p-3">
            <Sparkles className="h-6 w-6 text-cyan-400" />
          </div>

          <div>
            <h1 className="text-2xl font-semibold text-white">
              SearchIntel
            </h1>

            <p className="text-sm text-slate-500">
              Search Intelligence Platform
            </p>
          </div>
        </div>

        <div className="mt-14">
          <div className="text-sm text-slate-500">
            Workspaces
          </div>

          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">
            Choose a project
          </h2>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Each project contains its own target brand,
            website, competitors, experiments, entity
            knowledge and optimization plan.
          </p>
        </div>

        {workspaces.length === 0 ? (
          <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/60 p-8">
            <FolderKanban className="h-6 w-6 text-slate-500" />

            <h3 className="mt-4 font-medium text-white">
              No projects yet
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Create a SearchIntel project to begin.
            </p>
          </div>
        ) : (
          <div className="mt-8 grid gap-5 lg:grid-cols-2">
            {workspaces.map(
              (workspace) => (
                <Link
                  key={workspace.id}
                  href={`/projects/${workspace.id}`}
                  className="group rounded-2xl border border-slate-800 bg-slate-900/60 p-6 transition hover:border-cyan-500/30 hover:bg-slate-900"
                >
                  <div className="flex items-start justify-between gap-6">
                    <div>
                      <div className="text-xs uppercase tracking-wider text-slate-500">
                        Project #{workspace.id}
                      </div>

                      <h3 className="mt-2 text-xl font-semibold text-white">
                        {workspace.name}
                      </h3>

                      {workspace.description && (
                        <p className="mt-2 text-sm leading-6 text-slate-400">
                          {workspace.description}
                        </p>
                      )}
                    </div>

                    <div className="rounded-xl bg-slate-800 p-2.5 transition group-hover:bg-cyan-400/10">
                      <ArrowRight className="h-5 w-5 text-slate-500 transition group-hover:text-cyan-400" />
                    </div>
                  </div>

                  <div className="mt-6 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <Search className="h-3.5 w-3.5" />
                        Target brand
                      </div>

                      <div className="mt-2 text-sm font-medium text-slate-200">
                        {workspace.target_brand ??
                          "Not configured"}
                      </div>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <Globe2 className="h-3.5 w-3.5" />
                        Primary domain
                      </div>

                      <div className="mt-2 truncate text-sm font-medium text-slate-200">
                        {workspace.domain ??
                          "Not configured"}
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-2">
                    <span className="flex items-center gap-1.5 rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                      <Users className="h-3.5 w-3.5" />
                      {workspace.competitor_count} competitors
                    </span>

                    <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                      {workspace.experiment_count} experiments
                    </span>

                    <span className="rounded-lg bg-slate-800 px-2.5 py-1 text-xs text-slate-400">
                      {workspace.completed_experiment_count} completed
                    </span>
                  </div>

                  {workspace.latest_completed_experiment_name && (
                    <div className="mt-5 border-t border-slate-800 pt-4 text-xs text-slate-500">
                      Latest completed:{" "}
                      <span className="text-slate-300">
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
