import type {
  ActionPlanSummary,
  AIVisibilityMetrics,
  EntitiesSummary,
  ExperimentComparison,
  ExperimentsSummary,
  GeoExperiment,
  GeoOpportunitySummary,
  ProjectWorkspace,
  TechnicalSEOSummary,
  VisibilitySummary,
} from "@/lib/types";


function apiBaseUrl(): string {
  return (
    process.env.SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1"
  );
}


async function fetchJson<T>(
  url: string,
): Promise<T> {
  const response = await fetch(
    url,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `SearchIntel API returned ${response.status}.`,
    );
  }

  return response.json() as Promise<T>;
}


async function getLatestCompletedExperiment(
  projectId: number,
): Promise<GeoExperiment> {
  const experiments = await fetchJson<
    GeoExperiment[]
  >(
    `${apiBaseUrl()}/projects/${projectId}/geo-experiments`,
  );

  const completed = experiments
    .filter(
      (experiment) =>
        experiment.status === "completed",
    )
    .sort(
      (a, b) =>
        b.id - a.id,
    );

  if (completed.length === 0) {
    throw new Error(
      "No completed experiment exists for this project.",
    );
  }

  return completed[0];
}


export async function getProjectWorkspaces(): Promise<
  ProjectWorkspace[]
> {
  return fetchJson<ProjectWorkspace[]>(
    `${apiBaseUrl()}/projects/workspaces`,
  );
}


export async function getProjectWorkspace(
  projectId: number,
): Promise<ProjectWorkspace> {
  const workspaces =
    await getProjectWorkspaces();

  const workspace = workspaces.find(
    (item) =>
      item.id === projectId,
  );

  if (!workspace) {
    throw new Error(
      `Project ${projectId} was not found.`,
    );
  }

  return workspace;
}


export async function getLatestCompletedVisibilitySummary(
  projectId: number,
): Promise<VisibilitySummary> {
  const experiment =
    await getLatestCompletedExperiment(
      projectId,
    );

  return fetchJson<VisibilitySummary>(
    `${apiBaseUrl()}/geo-experiments/${experiment.id}/visibility-summary`,
  );
}


export async function getTechnicalSEOSummary(
  projectId: number,
): Promise<TechnicalSEOSummary> {
  return fetchJson<TechnicalSEOSummary>(
    `${apiBaseUrl()}/projects/${projectId}/technical-seo-summary`,
  );
}


export async function getLatestCompletedAIVisibilityMetrics(
  projectId: number,
): Promise<AIVisibilityMetrics> {
  const experiment =
    await getLatestCompletedExperiment(
      projectId,
    );

  return fetchJson<AIVisibilityMetrics>(
    `${apiBaseUrl()}/geo-experiments/${experiment.id}/visibility-metrics`,
  );
}


export async function getLatestCompletedPromptOpportunities(
  projectId: number,
): Promise<GeoOpportunitySummary> {
  const experiment =
    await getLatestCompletedExperiment(
      projectId,
    );

  return fetchJson<GeoOpportunitySummary>(
    `${apiBaseUrl()}/geo-experiments/${experiment.id}/opportunities`,
  );
}


export async function getExperimentsSummary(
  projectId: number,
): Promise<ExperimentsSummary> {
  return fetchJson<ExperimentsSummary>(
    `${apiBaseUrl()}/projects/${projectId}/experiments-summary`,
  );
}


export async function getExperimentComparison(
  projectId: number,
  baselineId: number,
  comparisonId: number,
): Promise<ExperimentComparison> {
  return fetchJson<ExperimentComparison>(
    `${apiBaseUrl()}/projects/${projectId}/geo-experiments/compare?baseline_id=${baselineId}&comparison_id=${comparisonId}`,
  );
}


export async function getEntitiesSummary(
  projectId: number,
): Promise<EntitiesSummary> {
  return fetchJson<EntitiesSummary>(
    `${apiBaseUrl()}/projects/${projectId}/entities-summary`,
  );
}


export async function getActionPlanSummary(
  projectId: number,
): Promise<ActionPlanSummary> {
  return fetchJson<ActionPlanSummary>(
    `${apiBaseUrl()}/projects/${projectId}/action-plan-summary`,
  );
}
