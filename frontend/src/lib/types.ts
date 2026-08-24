export type GeoExperiment = {
  id: number;
  project_id: number;
  name: string;
  phase: string;
  status: string;
  description: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type VisibilityLeader = {
  brand_id: number;
  name: string;
  exposures: number;
  share_of_voice: number;
  coverage: number;
};

export type VisibilitySummary = {
  project_id: number;
  experiment_id: number;
  experiment_name: string;
  experiment_phase: string;
  experiment_status: string;
  benchmark_mode: string;
  analyzed_runs: number;
  analyzed_prompts: number;

  target: {
    brand_id: number;
    brand: string;
    web_visibility_score: number | null;

    raw_response_coverage: number;
    source_presence_rate: number | null;
    retrieval_associated_response_coverage: number | null;
    cited_response_coverage: number | null;

    response_share_of_voice: number;
    retrieval_associated_response_share_of_voice:
      | number
      | null;
    cited_response_share_of_voice: number | null;

    source_exposure_share_of_voice: number | null;
    citation_exposure_share_of_voice: number | null;
    citation_exposure_conversion: number | null;
  };

  funnel: {
    total_responses: number;
    mentioned_responses: number;
    retrieval_associated_responses: number;
    cited_responses: number;
  };

  leaders: {
    response_visibility: VisibilityLeader[];
    retrieval_visibility: VisibilityLeader[];
    citation_visibility: VisibilityLeader[];
  };

  diagnosis: {
    primary_bottleneck:
      | "retrieval"
      | "citation"
      | "coverage"
      | "none"
      | "not_applicable";
    message: string;
    rule_version: string;
    coverage_threshold: number;
  };
};

export type TechnicalSEOPage = {
  id: number;
  url: string;
  path: string;

  status_code: number | null;

  title: string | null;
  meta_description: string | null;
  h1: string | null;

  canonical_url: string | null;
  robots_meta: string | null;

  word_count: number;
  internal_link_count: number;
  external_link_count: number;

  last_crawled_at: string | null;
};

export type TechnicalSEOCheck = {
  key: string;
  label: string;

  status: string;
  issue_count: number;
};

export type TechnicalSEORecommendation = {
  id: number;
  page_id: number;

  issue_code: string;
  priority: string;
  priority_score: number;

  title: string;
  recommendation: string;
  status: string;
};

export type TechnicalSEOSummary = {
  project_id: number;

  website: {
    id: number;

    brand_id: number;
    brand: string;

    domain: string;
    base_url: string;

    is_primary: boolean;
  };

  audit: {
    id: number;

    score: number;
    pages_checked: number;
    issue_count: number;

    high_issues: number;
    medium_issues: number;
    low_issues: number;

    created_at: string;
  };

  crawled_pages: number;
  successful_pages: number;
  failed_pages: number;

  total_words: number;
  average_word_count: number;

  pages: TechnicalSEOPage[];

  checks: TechnicalSEOCheck[];

  recommendation_count: number;

  recommendations: TechnicalSEORecommendation[];
};
