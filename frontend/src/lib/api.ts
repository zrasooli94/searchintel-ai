import type {
  ActionPlanSummary,
  AIVisibilityMetrics,
  CompetitorDiscoverySuggestion,
  EntitiesSummary,
  ExperimentComparison,
  ExperimentsSummary,
  GeoOpportunitySummary,
  SiteRAGGapSummary,
  StarterPromptGenerationResult,
  ProjectCompetitor,
  ProjectPrompt,
  ProjectWorkspace,
  ProjectReadiness,
  ProjectPrioritySummary,
  TechnicalAuditSetupState,
  TechnicalSEOSummary,
  MonitoringSummary,
  VisibilitySummary,
  WebsiteSetupState,
} from "@/lib/types";
import {
  latestCompletedExperimentForMode,
} from "@/lib/experiment-selection";
import {
  searchIntelApiBaseUrl,
  searchIntelFetch,
} from "@/lib/server-api";


async function fetchJson<T>(
  url: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await searchIntelFetch(
    url,
    { ...init, cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(
      `SearchIntel API returned ${response.status}.`,
    );
  }

  return response.json() as Promise<T>;
}


async function getLatestCompletedExperimentForMode(
  projectId: number,
  benchmarkMode: string,
) {
  const summary = await getExperimentsSummary(
    projectId,
  );

  return latestCompletedExperimentForMode(
    summary.experiments,
    benchmarkMode,
  );
}


async function getRequiredLatestCompletedExperimentForMode(
  projectId: number,
  benchmarkMode: string,
) {
  const experiment =
    await getLatestCompletedExperimentForMode(
      projectId,
      benchmarkMode,
    );

  if (!experiment) {
    throw new Error(
      `No completed ${benchmarkMode} experiment exists for this project.`,
    );
  }

  return experiment;
}


export async function getProjectWorkspaces(): Promise<
  ProjectWorkspace[]
> {
  return fetchJson<ProjectWorkspace[]>(
    `${searchIntelApiBaseUrl()}/projects/workspaces`,
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


export async function getProjectReadiness(
  projectId: number,
): Promise<ProjectReadiness> {
  return fetchJson<ProjectReadiness>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/readiness`,
  );
}

export async function getProjectPriorities(projectId: number): Promise<ProjectPrioritySummary> {
  return fetchJson<ProjectPrioritySummary>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/priorities`,
  );
}

export async function getProjectMonitoring(projectId: number): Promise<MonitoringSummary> {
  return fetchJson<MonitoringSummary>(`${searchIntelApiBaseUrl()}/projects/${projectId}/monitoring`);
}

export async function getStarterPromptProposal(
  projectId: number,
): Promise<StarterPromptGenerationResult | null> {
  return fetchJson<StarterPromptGenerationResult | null>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/prompts/starter-proposal`,
  );
}


export async function getLatestCompletedVisibilitySummary(
  projectId: number,
): Promise<VisibilitySummary> {
  const experiment =
    await getRequiredLatestCompletedExperimentForMode(
      projectId,
      "web_search",
    );

  return fetchJson<VisibilitySummary>(
    `${searchIntelApiBaseUrl()}/geo-experiments/${experiment.id}/visibility-summary`,
  );
}


export async function getLatestCompletedWebVisibilitySummary(
  projectId: number,
): Promise<VisibilitySummary | null> {
  const experiment =
    await getLatestCompletedExperimentForMode(
      projectId,
      "web_search",
    );

  if (!experiment) {
    return null;
  }

  return fetchJson<VisibilitySummary>(
    `${searchIntelApiBaseUrl()}/geo-experiments/${experiment.id}/visibility-summary`,
  );
}


export async function getTechnicalSEOSummary(
  projectId: number,
): Promise<TechnicalSEOSummary | null> {
  const response = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/technical-seo-summary`,
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

  return response.json() as Promise<TechnicalSEOSummary>;
}


export async function getLatestCompletedAIVisibilityMetrics(
  projectId: number,
): Promise<AIVisibilityMetrics> {
  const experiment =
    await getRequiredLatestCompletedExperimentForMode(
      projectId,
      "web_search",
    );

  return fetchJson<AIVisibilityMetrics>(
    `${searchIntelApiBaseUrl()}/geo-experiments/${experiment.id}/visibility-metrics`,
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
        `${searchIntelApiBaseUrl()}/geo-experiments/${experiment.id}/opportunities`,
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
          `${searchIntelApiBaseUrl()}/geo-experiments/${experiment.id}/visibility-summary`,
        );

      return {
        visibilitySummary,
        gaps,
      };
    }
  }

  const visibilitySummary =
    await fetchJson<VisibilitySummary>(
      `${searchIntelApiBaseUrl()}/geo-experiments/${fallback!.experimentId}/visibility-summary`,
    );

  return {
    visibilitySummary,
    gaps: fallback!.gaps,
  };
}




export async function getLatestCompletedSiteRAGGaps(
  projectId: number,
): Promise<SiteRAGGapSummary | null> {
  const experiment =
    await getLatestCompletedExperimentForMode(
      projectId,
      "site_rag",
    );

  if (!experiment) {
    return null;
  }

  return fetchJson<SiteRAGGapSummary>(
    `${searchIntelApiBaseUrl()}/geo-experiments/${experiment.id}/site-rag-gaps`,
  );
}


export async function getExperimentsSummary(
  projectId: number,
): Promise<ExperimentsSummary> {
  return fetchJson<ExperimentsSummary>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/experiments-summary`,
  );
}


export async function getExperimentComparison(
  projectId: number,
  baselineId: number,
  comparisonId: number,
): Promise<ExperimentComparison> {
  return fetchJson<ExperimentComparison>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/geo-experiments/compare?baseline_id=${baselineId}&comparison_id=${comparisonId}`,
  );
}


export async function getEntitiesSummary(
  projectId: number,
): Promise<EntitiesSummary> {
  return fetchJson<EntitiesSummary>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/entities-summary`,
  );
}


export async function getActionPlanSummary(
  projectId: number,
): Promise<ActionPlanSummary | null> {
  const response = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/action-plan-summary`,
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
  const pagesResponse = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/websites/${websiteId}/pages`,
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

  const auditResponse = await searchIntelFetch(
    `${searchIntelApiBaseUrl()}/websites/${websiteId}/technical-audits/latest`,
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
    `${searchIntelApiBaseUrl()}/projects/${projectId}/competitors`,
  );
}


export async function getCompetitorDiscoverySuggestions(
  projectId: number,
): Promise<CompetitorDiscoverySuggestion[]> {
  return fetchJson<CompetitorDiscoverySuggestion[]>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/competitor-discovery-suggestions`,
  );
}


export async function getProjectPrompts(
  projectId: number,
): Promise<ProjectPrompt[]> {
  return fetchJson<ProjectPrompt[]>(
    `${searchIntelApiBaseUrl()}/projects/${projectId}/prompts`,
  );
}

export async function getClientReports(projectId: number): Promise<import("@/lib/types").ClientReport[]> {
  const { operatorBackendHeaders } = await import("@/lib/operator-session");
  return fetchJson(`${searchIntelApiBaseUrl()}/projects/${projectId}/client-reports`, {
    headers: await operatorBackendHeaders(), cache: "no-store",
  });
}

export async function getSharedClientReport(token: string): Promise<import("@/lib/types").ClientReport> {
  return fetchJson(`${searchIntelApiBaseUrl()}/client-reports/share/${encodeURIComponent(token)}`, { cache: "no-store" });
}
