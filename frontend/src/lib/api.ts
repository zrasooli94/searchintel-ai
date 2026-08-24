import type {
  AIVisibilityMetrics,
  GeoExperiment,
  GeoOpportunitySummary,
  TechnicalSEOSummary,
  VisibilitySummary,
} from "@/lib/types";

function apiBaseUrl(): string {
  return (
    process.env.SEARCHINTEL_API_BASE_URL ??
    "http://127.0.0.1:8000/api/v1"
  );
}

function projectId(): number {
  const raw =
    process.env.SEARCHINTEL_PROJECT_ID;

  if (!raw) {
    throw new Error(
      "SEARCHINTEL_PROJECT_ID is not configured.",
    );
  }

  const value = Number(raw);

  if (!Number.isInteger(value)) {
    throw new Error(
      "SEARCHINTEL_PROJECT_ID must be an integer.",
    );
  }

  return value;
}

async function fetchJson<T>(
  url: string,
): Promise<T> {
  const response = await fetch(url, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `SearchIntel API returned ${response.status}.`,
    );
  }

  return response.json() as Promise<T>;
}

export async function getLatestCompletedVisibilitySummary(): Promise<VisibilitySummary> {
  const experiments = await fetchJson<
    GeoExperiment[]
  >(
    `${apiBaseUrl()}/projects/${projectId()}/geo-experiments`,
  );

  const completed = experiments
    .filter(
      (experiment) =>
        experiment.status === "completed",
    )
    .sort((a, b) => b.id - a.id);

  if (completed.length === 0) {
    throw new Error(
      "No completed experiment exists for this project.",
    );
  }

  const experiment = completed[0];

  return fetchJson<VisibilitySummary>(
    `${apiBaseUrl()}/geo-experiments/${experiment.id}/visibility-summary`,
  );
}

export async function getTechnicalSEOSummary(): Promise<TechnicalSEOSummary> {
  return fetchJson<TechnicalSEOSummary>(
    `${apiBaseUrl()}/projects/${projectId()}/technical-seo-summary`,
  );
}


export async function getLatestCompletedAIVisibilityMetrics(): Promise<AIVisibilityMetrics> {
  const experiments = await fetchJson<
    GeoExperiment[]
  >(
    `${apiBaseUrl()}/projects/${projectId()}/geo-experiments`,
  );

  const completed = experiments
    .filter(
      (experiment) =>
        experiment.status === "completed",
    )
    .sort(
      (a, b) => b.id - a.id,
    );

  if (completed.length === 0) {
    throw new Error(
      "No completed experiment exists for this project.",
    );
  }

  const experiment = completed[0];

  return fetchJson<AIVisibilityMetrics>(
    `${apiBaseUrl()}/geo-experiments/${experiment.id}/visibility-metrics`,
  );
}


export async function getLatestCompletedPromptOpportunities(): Promise<GeoOpportunitySummary> {
  const experiments = await fetchJson<
    GeoExperiment[]
  >(
    `${apiBaseUrl()}/projects/${projectId()}/geo-experiments`,
  );

  const completed = experiments
    .filter(
      (experiment) =>
        experiment.status === "completed",
    )
    .sort(
      (a, b) => b.id - a.id,
    );

  if (completed.length === 0) {
    throw new Error(
      "No completed experiment exists for this project.",
    );
  }

  const experiment = completed[0];

  return fetchJson<GeoOpportunitySummary>(
    `${apiBaseUrl()}/geo-experiments/${experiment.id}/opportunities`,
  );
}
