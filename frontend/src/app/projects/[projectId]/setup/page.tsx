import Link from "next/link";

import {
  ArrowLeft,
  CheckCircle2,
  FlaskConical,
  Globe2,
  Search,
  Sparkles,
  Users,
} from "lucide-react";

import {
  getProjectWorkspace,
} from "@/lib/api";


export const dynamic =
  "force-dynamic";


type Props = {
  params: Promise<{
    projectId: string;
  }>;
};


export default async function Page({
  params,
}: Props) {
  const {
    projectId: rawProjectId,
  } = await params;

  const projectId =
    Number(rawProjectId);

  const workspace =
    await getProjectWorkspace(
      projectId
    );

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Workspaces
        </Link>

        <div className="mt-10 flex items-start gap-4">
          <div className="rounded-2xl bg-cyan-400/10 p-3">
            <Sparkles className="h-6 w-6 text-cyan-400" />
          </div>

          <div>
            <div className="text-sm text-slate-500">
              Project setup
            </div>

            <h1 className="mt-1 text-3xl font-semibold text-white">
              {workspace.name}
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              The workspace and canonical target
              identity are ready. Complete the
              measurement setup before opening the
              visibility dashboard.
            </p>
          </div>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />

            <div className="mt-5 text-sm text-slate-500">
              Target brand
            </div>

            <div className="mt-1 text-lg font-medium text-white">
              {workspace.target_brand}
            </div>
          </div>

          <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
            <Globe2 className="h-5 w-5 text-emerald-400" />

            <div className="mt-5 text-sm text-slate-500">
              Primary website
            </div>

            <div className="mt-1 text-lg font-medium text-white">
              {workspace.domain}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <Users className="h-5 w-5 text-slate-500" />

            <div className="mt-5 text-2xl font-semibold text-white">
              {workspace.competitor_count}
            </div>

            <div className="mt-1 text-sm text-slate-500">
              Competitors configured
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <FlaskConical className="h-5 w-5 text-slate-500" />

            <div className="mt-5 text-2xl font-semibold text-white">
              {workspace.experiment_count}
            </div>

            <div className="mt-1 text-sm text-slate-500">
              Experiments created
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-2xl border border-cyan-500/15 bg-cyan-500/5 p-6">
          <div className="flex gap-4">
            <Search className="mt-1 h-5 w-5 shrink-0 text-cyan-400" />

            <div>
              <h2 className="font-medium text-white">
                Next: establish the first baseline
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                We will crawl the website, configure
                competitors and prompts, then create
                the first controlled SearchIntel
                experiment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
