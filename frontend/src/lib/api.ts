import type {
  ActionPlanSummary,
  AIVisibilityMetrics,
  EntitiesSummary,
  ExperimentComparison,
  ExperimentsSummary,
  GeoExperiment,
  GeoOpportunitySummary,
  SiteRAGGapSummary,
  ProjectCompetitor,
  ProjectPrompt,
  ProjectWorkspace,
  TechnicalAuditSetupState,
  TechnicalSEOSummary,
  VisibilitySummary,
  WebsiteSetupState,
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


export async function getLatestCompletedWebVisibilitySummary(
  projectId: number,
): Promise<VisibilitySummary | null> {
  const summary =
    await getExperimentsSummary(
      projectId,
    );

  const experiment =
    summary.experiments
      .filter(
        (item) =>
          item.status === "completed"
          && item.benchmark_mode ===
            "web_search",
      )
      .sort(
        (a, b) =>
          b.id - a.id,
      )[0];

  if (!experiment) {
    return null;
  }

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


export async function getLatestCompletedPromptGapContext(
  projectId: number,
): Promise<{
  visibilitySummary: VisibilitySummary;
  gaps: GeoOpportunitySummary;
}> {
  const summary =
    await getExperimentsSummary(
      projectId,
    );

  const experiments =
    summary.experiments
      .filter(
        (item) =>
          item.status === "completed"
          && item.benchmark_mode ===
            "web_search",
      )
      .sort(
        (a, b) =>
          b.id - a.id,
      );

  if (experiments.length === 0) {
    throw new Error(
      "No completed web-search experiment exists for this project.",
    );
  }

  let fallback:
    | {
        experimentId: number;
        gaps: GeoOpportunitySummary;
      }
    | null = null;

  for (const experiment of experiments) {
    const gaps =
      await fetchJson<GeoOpportunitySummary>(
        `${apiBaseUrl()}/geo-experiments/${experiment.id}/opportunities`,
      );

    fallback ??= {
      experimentId: experiment.id,
      gaps,
    };

    if (
      gaps.total_prompts > 0
      || gaps.opportunities.length > 0
    ) {
      const visibilitySummary =
        await fetchJson<VisibilitySummary>(
          `${apiBaseUrl()}/geo-experiments/${experiment.id}/visibility-summary`,
        );

      return {
        visibilitySummary,
        gaps,
      };
    }
  }

  const visibilitySummary =
    await fetchJson<VisibilitySummary>(
      `${apiBaseUrl()}/geo-experiments/${fallback!.experimentId}/visibility-summary`,
    );

  return {
    visibilitySummary,
    gaps: fallback!.gaps,
  };
}




export async function getLatestCompletedSiteRAGGaps(
  projectId: number,
): Promise<SiteRAGGapSummary | null> {
  const summary =
    await getExperimentsSummary(
      projectId,
    );

  const experiment =
    summary.experiments
      .filter(
        (item) =>
          item.status === "completed"
          && item.benchmark_mode ===
            "site_rag",
      )
      .sort(
        (a, b) =>
          b.id - a.id,
      )[0];

  if (!experiment) {
    return null;
  }

  return fetchJson<SiteRAGGapSummary>(
    `${apiBaseUrl()}/geo-experiments/${experiment.id}/site-rag-gaps`,
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
): Promise<ActionPlanSummary | null> {
  const response = await fetch(
    `${apiBaseUrl()}/projects/${projectId}/action-plan-summary`,
    {
      cache: "no-store",
    },
  );

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(
      `SearchIntel API returned ${response.status}.`,
    );
  }

  return response.json() as Promise<ActionPlanSummary>;
}


export async function getWebsiteSetupState(
  websiteId: number,
): Promise<WebsiteSetupState> {
  const pagesResponse = await fetch(
    `${apiBaseUrl()}/websites/${websiteId}/pages`,
    {
      cache: "no-store",
    },
  );

  if (!pagesResponse.ok) {
    throw new Error(
      `Could not read website pages: ${pagesResponse.status}.`,
    );
  }

  const pages = await pagesResponse.json() as unknown[];

  const auditResponse = await fetch(
    `${apiBaseUrl()}/websites/${websiteId}/technical-audits/latest`,
    {
      cache: "no-store",
    },
  );

  let latestAudit:
    | TechnicalAuditSetupState
    | null = null;

  if (auditResponse.ok) {
    latestAudit =
      await auditResponse.json() as TechnicalAuditSetupState;

  } else if (
    auditResponse.status !== 404
  ) {
    throw new Error(
      `Could not read technical audit: ${auditResponse.status}.`,
    );
  }

  return {
    page_count: pages.length,
    latest_audit: latestAudit,
  };
}


export async function getProjectCompetitors(
  projectId: number,
): Promise<ProjectCompetitor[]> {
  return fetchJson<ProjectCompetitor[]>(
    `${apiBaseUrl()}/projects/${projectId}/competitors`,
  );
}


export async function getProjectPrompts(
  projectId: number,
): Promise<ProjectPrompt[]> {
  return fetchJson<ProjectPrompt[]>(
    `${apiBaseUrl()}/projects/${projectId}/prompts`,
  );
}
