import Link from "next/link";

import {
  ArrowLeft,
  CheckCircle2,
  FlaskConical,
  Globe2,
  Search,
  Users,
} from "lucide-react";

import SetupBaselineStep from "@/components/dashboard/setup-baseline-step";
import SetupOptimizationStep from "@/components/dashboard/setup-optimization-step";
import SetupCompetitorsStep from "@/components/dashboard/setup-competitors-step";
import SetupPromptsStep from "@/components/dashboard/setup-prompts-step";
import SetupTechnicalStep from "@/components/dashboard/setup-technical-step";
import ProjectReadinessPanel from "@/components/dashboard/project-readiness-panel";

import {
  getProjectCompetitors,
  getProjectPrompts,
  getProjectReadiness,
  getProjectWorkspace,
  getWebsiteSetupState,
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
      projectId,
    );

  const [
    readiness,
    competitors,
    prompts,
  ] = await Promise.all([
    getProjectReadiness(projectId),
    getProjectCompetitors(
      projectId,
    ),
    getProjectPrompts(
      projectId,
    ),
  ]);

  const setupState =
    workspace.website_id === null
      ? null
      : await getWebsiteSetupState(
          workspace.website_id,
        );

  return (
    <main className="crystal-page min-h-screen">
      <div className="mx-auto max-w-[1180px] px-6 pb-20 pt-10 lg:px-10">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-violet-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Workspaces
        </Link>

        <section className="mt-10">
          <div className="crystal-eyebrow">
            Project setup
          </div>

          <h1 className="mt-3 text-4xl font-medium tracking-[-0.055em] text-slate-950">
            {workspace.name}
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
            Configure the measurement foundation for this
            workspace before using the visibility dashboards.
          </p>
        </section>

        <section className="mt-9 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="crystal-card rounded-[20px] p-5">
            <div className="flex items-center justify-between">
              <div className="crystal-eyebrow">
                Target brand
              </div>

              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50">
                {workspace.target_brand ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Globe2 className="h-4 w-4 text-amber-500" />
                )}
              </div>
            </div>

            <div className="mt-5 text-lg font-medium text-slate-950">
              {workspace.target_brand ?? "Needs configuration"}
            </div>

            <div className="mt-1 text-xs text-slate-400">
              Canonical identity
            </div>
          </div>

          <div className="crystal-card rounded-[20px] p-5">
            <div className="flex items-center justify-between">
              <div className="crystal-eyebrow">
                Primary website
              </div>

              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50">
                <Globe2 className="h-4 w-4 text-blue-500" />
              </div>
            </div>

            <div className="mt-5 truncate text-lg font-medium text-slate-950">
              {workspace.domain ?? "Needs configuration"}
            </div>

            <div className="mt-1 text-xs text-slate-400">
              Registered first-party domain
            </div>
          </div>

          <div className="crystal-card rounded-[20px] p-5">
            <div className="flex items-center justify-between">
              <div className="crystal-eyebrow">
                Competitors
              </div>

              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50">
                <Users className="h-4 w-4 text-violet-500" />
              </div>
            </div>

            <div className="crystal-value mt-5 text-3xl font-medium">
              {workspace.competitor_count}
            </div>

            <div className="mt-1 text-xs text-slate-400">
              Configured brands
            </div>
          </div>

          <div className="crystal-card rounded-[20px] p-5">
            <div className="flex items-center justify-between">
              <div className="crystal-eyebrow">
                Experiments
              </div>

              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-fuchsia-50">
                <FlaskConical className="h-4 w-4 text-fuchsia-500" />
              </div>
            </div>

            <div className="crystal-value mt-5 text-3xl font-medium">
              {workspace.experiment_count}
            </div>

            <div className="mt-1 text-xs text-slate-400">
              Stored measurement sets
            </div>
          </div>
        </section>

        <div className="mt-10 space-y-6">
          <ProjectReadinessPanel readiness={readiness} />

          {workspace.website_id !== null && setupState ? (
            <SetupTechnicalStep
              websiteId={workspace.website_id}
              initialPageCount={setupState.page_count}
              initialAudit={setupState.latest_audit}
            />
          ) : (
            <section className="crystal-panel rounded-[22px] p-6">
              <div className="flex gap-4">
                <div className="crystal-step-badge">2</div>
                <div>
                  <h2 className="font-semibold text-slate-950">Website & Technical Crawl</h2>
                  <p className="mt-1 text-sm leading-6 text-amber-700">
                    Confirm a target brand and primary first-party website before running a bounded crawl.
                  </p>
                </div>
              </div>
            </section>
          )}

          <SetupCompetitorsStep
            projectId={projectId}
            initialCompetitors={
              competitors
            }
          />

          <SetupPromptsStep
            key={
              prompts
                .map(
                  (prompt) =>
                    `${prompt.id}:${prompt.updated_at}:${prompt.is_active ? 1 : 0}`,
                )
                .join("-")
            }
            projectId={projectId}
            targetBrand={
              workspace.target_brand
              ?? "Target brand"
            }
            initialPrompts={
              prompts
            }
          />

          <SetupBaselineStep
            projectId={projectId}
            activePromptCount={
              prompts.filter(
                (prompt) =>
                  prompt.is_active,
              ).length
            }
            eligibility={readiness.measurements}
          />

          <SetupOptimizationStep
            projectId={projectId}
          />
        </div>

        <section className="mt-8 rounded-[22px] border border-blue-200/70 bg-blue-50/65 p-6">
          <div className="flex gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white">
              <Search className="h-4 w-4 text-blue-500" />
            </div>

            <div>
              <div className="crystal-eyebrow">
                Measurement workflow
              </div>

              <h2 className="mt-2 font-medium text-slate-950">
                Establish and refine the controlled baseline
              </h2>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                Crawl the website, register competitors and
                prompts, create the baseline, then reuse the
                frozen measurement set for optimization.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
