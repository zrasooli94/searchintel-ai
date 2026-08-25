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

export type MentionShareOfVoiceItem = {
  brand_id: number;
  name: string;
  mention_count: number;
  share_of_voice: number;
};

export type ResponseVisibilityItem = {
  brand_id: number;
  name: string;
  response_exposures: number;
  response_share_of_voice: number;
  response_coverage: number;
};

export type RetrievalVisibilityItem = {
  brand_id: number;
  name: string;
  grounded_response_exposures: number;
  grounded_response_share_of_voice: number;
  grounded_response_coverage: number;
};

export type CitedVisibilityItem = {
  brand_id: number;
  name: string;
  cited_response_exposures: number;
  cited_response_share_of_voice: number;
  cited_response_coverage: number;
};

export type SourceExposureItem = {
  brand_id: number;
  name: string;
  source_exposures: number;
  source_exposure_share_of_voice: number;
};

export type CitationExposureItem = {
  brand_id: number;
  name: string;
  citation_exposures: number;
  citation_exposure_share_of_voice: number;
};

export type BrandCitationConversionItem = {
  brand_id: number;
  name: string;
  source_exposures: number;
  citation_exposures: number;
  citation_exposure_conversion: number;
};

export type AIVisibilityMetrics = {
  project_id: number;
  experiment_id: number | null;
  benchmark_mode: string;

  target_brand_id: number;
  target_brand: string;

  analyzed_runs: number;
  analyzed_prompts: number;
  web_search_analyzed_runs: number;

  target_mention_count: number;

  mention_rate: number;
  prompt_coverage: number;
  citation_rate: number;

  average_mention_position: number | null;

  target_share_of_voice: number;
  target_response_share_of_voice: number;
  target_response_coverage: number;

  position_quality: number;
  visibility_score_v1: number;
  web_visibility_score_v1: number | null;

  target_source_presence_rate: number | null;
  target_source_prompt_coverage: number | null;

  grounded_target_mention_rate: number | null;
  grounded_target_prompt_coverage: number | null;

  target_grounded_response_share_of_voice:
    | number
    | null;

  target_cited_response_share_of_voice:
    | number
    | null;

  target_cited_response_coverage:
    | number
    | null;

  unique_search_source_urls: number;
  unique_search_domains: number;

  source_to_citation_conversion:
    | number
    | null;

  target_source_to_citation_conversion:
    | number
    | null;

  target_source_share_of_voice:
    | number
    | null;

  target_citation_share_of_voice:
    | number
    | null;

  target_source_exposure_share_of_voice:
    | number
    | null;

  target_citation_exposure_share_of_voice:
    | number
    | null;

  target_citation_exposure_conversion:
    | number
    | null;

  resolved_first_party_source_rate:
    | number
    | null;

  share_of_voice:
    MentionShareOfVoiceItem[];

  response_share_of_voice:
    ResponseVisibilityItem[];

  grounded_response_share_of_voice:
    RetrievalVisibilityItem[];

  cited_response_share_of_voice:
    CitedVisibilityItem[];

  source_exposure_share_of_voice:
    SourceExposureItem[];

  citation_exposure_share_of_voice:
    CitationExposureItem[];

  brand_citation_conversion:
    BrandCitationConversionItem[];
};

export type PromptGapCompetitorEvidence = {
  brand_id: number;
  name: string;
  run_coverage: number;
  mention_count: number;
  average_position: number;
};

export type GeoPromptOpportunity = {
  id: number;
  experiment_id: number;
  project_id: number;
  prompt_id: number;
  target_brand_id: number;

  prompt_text: string;
  category: string;
  intent: string | null;

  run_count: number;
  target_mention_runs: number;
  target_mention_rate: number;

  top_competitor_brand_id: number | null;
  top_competitor_name: string | null;
  top_competitor_run_coverage: number;

  opportunity_score: number;
  priority: string;
  gap_type: string;

  evidence: {
    competitors?: PromptGapCompetitorEvidence[];
    visibility_gap?: number;
    category_weight?: number;
    benchmark_mode?: string;
    measurement_basis?: string;
    web_grounding_note?: string | null;
  } | null;

  recommendation: string;
};

export type GeoOpportunitySummary = {
  experiment_id: number;
  project_id: number;

  target_brand_id: number;
  target_brand: string;

  total_prompts: number;

  high_priority: number;
  medium_priority: number;
  low_priority: number;

  target_absent_prompts: number;
  competitor_dominance_prompts: number;
  covered_prompts: number;

  opportunities: GeoPromptOpportunity[];
};

export type ExperimentSummaryItem = {
  id: number;
  name: string;

  phase: string;
  status: string;
  benchmark_mode: string;

  runs: number;
  prompts: number;

  mention_rate: number;
  prompt_coverage: number;
  citation_rate: number;

  visibility_score_v1: number;
  web_visibility_score_v1: number | null;

  target_response_coverage: number;
  grounded_target_mention_rate: number | null;
  target_cited_response_coverage: number | null;
  target_source_presence_rate: number | null;

  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type ComparableExperimentPair = {
  baseline_id: number;
  baseline_name: string;

  comparison_id: number;
  comparison_name: string;

  benchmark_mode: string;
};

export type ExperimentsSummary = {
  project_id: number;

  total_experiments: number;
  completed_experiments: number;
  draft_experiments: number;

  experiments: ExperimentSummaryItem[];

  comparable_pairs: ComparableExperimentPair[];
};

export type ExperimentMetricValue = {
  baseline: number | null;
  comparison: number | null;
  delta: number | null;
};

export type ExperimentComparison = {
  project_id: number;

  baseline_experiment_id: number;
  comparison_experiment_id: number;

  baseline_name: string;
  comparison_name: string;

  baseline_runs: number;
  comparison_runs: number;

  mention_rate: ExperimentMetricValue;
  prompt_coverage: ExperimentMetricValue;
  citation_rate: ExperimentMetricValue;
  target_share_of_voice: ExperimentMetricValue;
  visibility_score_v1: ExperimentMetricValue;
  average_mention_position: ExperimentMetricValue;

  target_source_presence_rate: ExperimentMetricValue;
  target_source_prompt_coverage: ExperimentMetricValue;

  grounded_target_mention_rate: ExperimentMetricValue;
  grounded_target_prompt_coverage: ExperimentMetricValue;

  source_to_citation_conversion: ExperimentMetricValue;
  target_source_to_citation_conversion: ExperimentMetricValue;

  target_source_share_of_voice: ExperimentMetricValue;
  target_citation_share_of_voice: ExperimentMetricValue;

  resolved_first_party_source_rate: ExperimentMetricValue;
};

export type EntityRelationshipSummary = {
  id: number;

  subject_entity_id: number;
  subject_name: string;
  subject_type: string;

  relationship_type: string;

  object_entity_id: number;
  object_name: string;
  object_type: string;

  confidence: number;
  source: string;
};

export type EntityRegistryItem = {
  id: number;

  name: string;
  normalized_name: string;
  entity_type: string;

  rollup_brand_id: number | null;
  rollup_brand: string | null;
  project_role: string | null;

  description: string | null;

  aliases: string[];

  parent_relationships:
    EntityRelationshipSummary[];

  child_relationships:
    EntityRelationshipSummary[];
};

export type EntityCandidateSummary = {
  rule_id: number;

  name: string;
  normalized_name: string;

  entity_type: string | null;

  proposed_parent_name: string | null;
  proposed_relationship_type:
    | string
    | null;

  classification_confidence:
    | number
    | null;

  classification_source:
    | string
    | null;
};

export type EntitiesSummary = {
  project_id: number;

  stats: {
    total_entities: number;

    brands: number;
    companies: number;
    products: number;
    software_projects: number;
    organizations: number;
    services: number;

    aliases: number;
    relationships: number;

    candidates: number;
    resolved_rules: number;
    rejected_rules: number;
  };

  entities: EntityRegistryItem[];

  relationships:
    EntityRelationshipSummary[];

  candidates:
    EntityCandidateSummary[];
};

export type ActionPlanItem = {
  id: number;
  sort_order: number;

  priority: string;
  action_type: string;

  title: string;
  rationale: string;

  target_page: string | null;

  impacted_prompt_ids: number[];
  impacted_opportunity_ids: number[];

  implementation_steps: string[];
  evidence: string[];
  success_metrics: string[];
  dependencies: string[];

  effort: string;
  status: string;
};

export type ActionPlanSummary = {
  project_id: number;

  plan_id: number;

  experiment_id: number;
  experiment_name: string;
  experiment_phase: string;
  experiment_status: string;
  benchmark_mode: string;

  target_brand_id: number;
  target_brand: string;

  plan_status: string;
  created_at: string;

  strategy_summary: string;

  baseline_metrics: Record<
    string,
    number | string | null
  >;

  recommended_sequence: string[];
  risks_and_limits: string[];

  total_actions: number;
  open_actions: number;
  completed_actions: number;

  high_priority_actions: number;
  medium_priority_actions: number;
  low_priority_actions: number;

  action_type_counts: Record<
    string,
    number
  >;

  provenance_note: string;

  actions: ActionPlanItem[];
};

export type ProjectWorkspace = {
  id: number;
  name: string;
  description: string | null;

  target_brand_id: number | null;
  target_brand: string | null;

  website_id: number | null;
  domain: string | null;
  base_url: string | null;

  competitor_count: number;

  experiment_count: number;
  completed_experiment_count: number;

  latest_completed_experiment_id:
    | number
    | null;

  latest_completed_experiment_name:
    | string
    | null;
};

export type ProjectOnboardResponse = {
  project_id: number;
  project_name: string;

  target_brand_id: number;
  target_brand: string;

  website_id: number;
  domain: string;
  base_url: string;

  brand_created: boolean;
  website_created: boolean;
  canonical_entity_created: boolean;

  setup_status: string;
};

export type CrawlResult = {
  website_id: number;
  pages_crawled: number;
  pages_discovered: number;
  pages_failed: number;
};

export type TechnicalAuditSetupState = {
  id: number;
  website_id: number;
  score: number;
  pages_checked: number;
  issue_count: number;
  created_at: string;
};

export type WebsiteSetupState = {
  page_count: number;
  latest_audit: TechnicalAuditSetupState | null;
};

export type ProjectCompetitor = {
  brand_id: number;
  name: string;

  website_id: number | null;
  domain: string | null;
  base_url: string | null;
};

export type ProjectCompetitorCreateResult = {
  brand_id: number;
  name: string;

  role: string;

  website_id: number | null;
  domain: string | null;
  base_url: string | null;

  brand_created: boolean;
  website_created: boolean;
  canonical_entity_created: boolean;
};

export type ProjectPrompt = {
  id: number;
  project_id: number;

  text: string;
  category: string;
  intent: string | null;

  is_active: boolean;

  created_at: string;
  updated_at: string;
};

export type PromptBulkResult = {
  project_id: number;

  requested: number;
  created: number;
  skipped_duplicates: number;

  created_prompt_ids: number[];
};
