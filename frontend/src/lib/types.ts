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
    entity_verified_response_coverage: number | null;
    entity_verified_share_of_voice: number | null;
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
    entity_verified_responses: number;
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

export type TechnicalSEOIssue = {
  id: number;
  page_id: number;
  page_url: string;
  code: string;
  severity: string;
  message: string;
};

export type TechnicalSEOSummary = {
  project_id: number;

  measurement_state: "ready" | "limited";
  measurement_reason: string | null;
  limitation_note: string | null;

  coverage_state: "unavailable" | "limited_sample" | "bounded_sample";
  coverage_label: string;
  coverage_reason: string;

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
  } | null;

  crawled_pages: number;
  successful_pages: number;
  failed_pages: number;

  total_words: number;
  average_word_count: number;

  pages: TechnicalSEOPage[];

  checks: TechnicalSEOCheck[];
  issues: TechnicalSEOIssue[];

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
  entity_verified_target_mention_count: number;
  entity_verified_target_mention_rate: number | null;
  entity_verified_target_prompt_coverage: number | null;
  entity_verified_target_share_of_voice: number | null;

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
    web_search_measured?: boolean;
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
  unmeasured_prompts: number;

  opportunities: GeoPromptOpportunity[];
};

export type SiteRAGGapEvidence = {
  gap_version?: string;
  benchmark_mode?: string;
  measurement_basis?: string;
  category_weight?: number;

  retrieved_source_count?: number;
  referenced_source_count?: number;

  supporting_urls?: string[];

  unsupported_run_ids?: number[];
  unsupported_response_ids?: number[];
};


export type SiteRAGGap = {
  id: number;
  experiment_id: number;
  project_id: number;
  prompt_id: number;
  target_brand_id: number;

  prompt_text: string;
  category: string;
  intent: string | null;

  run_count: number;
  answerable_runs: number;
  unsupported_runs: number;

  answerability_rate: number;
  unsupported_rate: number;

  gap_type: string;
  gap_score: number;
  priority: string;

  evidence: SiteRAGGapEvidence;
  recommendation: string;
};


export type SiteRAGGapSummary = {
  experiment_id: number;
  project_id: number;
  target_brand_id: number;
  target_brand: string;

  total_prompts: number;
  gap_prompts: number;
  covered_prompts: number;

  high_priority: number;
  medium_priority: number;
  low_priority: number;

  gap_type_counts: Record<string, number>;

  site_answerability_rate_v1: number | null;
  unsupported_answer_rate_v1: number | null;
  evidence_coverage_rate: number | null;
  source_reference_rate: number | null;
  evidence_utilization_rate: number | null;

  gaps: SiteRAGGap[];
};


export type SiteRAGSupportingPage = {
  page_id: number | null;
  url: string;
  title: string | null;

  response_count: number;
  reference_count: number;
};

export type ExperimentSummaryItem = {
  id: number;
  name: string;

  phase: string;
  status: string;
  benchmark_mode: string;

  runs: number;
  prompts: number;

  analysis_version: string;
  analysis_total_responses: number;
  analysis_current_responses: number;
  analysis_stale_responses: number;
  analysis_is_current: boolean;

  mention_rate: number;
  prompt_coverage: number;
  entity_verified_target_mention_rate: number | null;
  entity_verified_target_prompt_coverage: number | null;
  entity_verified_target_share_of_voice: number | null;
  citation_rate: number;

  visibility_score_v1: number;
  web_visibility_score_v1: number | null;

  site_rag_analyzed_runs: number;
  site_rag_analyzed_prompts: number;

  evidence_coverage_rate: number | null;
  source_reference_rate: number | null;
  evidence_utilization_rate: number | null;

  site_answerability_rate_v1: number | null;
  unsupported_answer_rate_v1: number | null;

  unique_supporting_pages: number;
  unique_supporting_urls: number;

  avg_sources_per_response: number | null;

  top_supporting_pages: SiteRAGSupportingPage[];

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
  entity_verified_target_mention_rate: ExperimentMetricValue;
  entity_verified_target_prompt_coverage: ExperimentMetricValue;
  entity_verified_target_share_of_voice: ExperimentMetricValue;
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

export type SiteRAGActionBridgeItem = {
  gap_type: string;
  gap_count: number;
  gap_score: number;

  priority: string;
  action_type: string;

  title: string;
  rationale: string;

  impacted_prompt_ids: number[];
  impacted_gap_ids: number[];

  implementation_steps: string[];
  evidence: string[];
  success_metrics: string[];
  dependencies: string[];

  effort: string;
};


export type SiteRAGActionBridgeSummary = {
  experiment_id: number;
  experiment_name: string;
  benchmark_mode: string;

  total_prompts: number;
  gap_prompts: number;
  covered_prompts: number;

  answerability_rate: number | null;
  unsupported_rate: number | null;
  evidence_coverage_rate: number | null;
  evidence_utilization_rate: number | null;

  actions: SiteRAGActionBridgeItem[];

  provenance_note: string;
};


export type ActionPlanSummary = {
  project_id: number;

  has_historical_plan: boolean;

  plan_id: number | null;

  experiment_id: number | null;
  experiment_name: string | null;
  experiment_phase: string | null;
  experiment_status: string | null;
  benchmark_mode: string | null;

  target_brand_id: number | null;
  target_brand: string | null;

  plan_status: string | null;
  created_at: string | null;

  strategy_summary: string | null;

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

  provenance_note: string | null;

  site_rag: SiteRAGActionBridgeSummary | null;

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

export type ReadinessState =
  | "ready"
  | "needs_review"
  | "limited"
  | "blocked"
  | "not_applicable";

export type ReadinessIssue = {
  code: string;
  message: string;
  evidence: string[];
  recommended_action: string | null;
};

export type MeasurementEligibility = {
  mode:
    | "technical_seo"
    | "memory"
    | "web_search"
    | "site_rag";
  state: ReadinessState;
  reason: string;
  evidence: string[];
  blocking_issues: ReadinessIssue[];
  warnings: ReadinessIssue[];
  recommended_action: string;
  execution_available: boolean;
  execution_note: string;
  has_historical_results: boolean;
};

export type ReadinessSuggestion = {
  key: string;
  kind:
    | "first_party_domain"
    | "competitor"
    | "prompt_category";
  value: string;
  reason: string;
  evidence: string[];
  approval_required: boolean;
};

export type ProjectReadiness = {
  project_id: number;
  project_name: string;
  overall_state: ReadinessState;
  configuration: {
    measurement_scope: "brand_wide" | "focused";
    measurement_focus: string | null;
    target_brand_id: number | null;
    target_brand: string | null;
    target_brand_count: number;
    primary_website_id: number | null;
    primary_domain: string | null;
    first_party_domains: string[];
    competitor_count: number;
    pending_competitor_suggestion_count: number;
    active_prompt_count: number;
    proposed_prompt_count: number;
    prompt_coverage_state: "ready" | "needs_review" | "blocked";
    prompt_categories: string[];
    usable_page_count: number;
    usable_word_count: number;
    execution_model: string | null;
  };
  issues: ReadinessIssue[];
  warnings: ReadinessIssue[];
  suggestions: ReadinessSuggestion[];
  measurements: Record<
    "technical_seo" | "memory" | "web_search" | "site_rag",
    MeasurementEligibility
  >;
  provenance_note: string;
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
  pages_blocked_by_robots: number;
  crawl_limited: boolean;
  limitations: string[];
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

export type CompetitorDiscoverySuggestion = {
  id: number;
  project_id: number;
  brand_name: string;
  website_url: string;
  domain: string;
  competitor_type: "direct" | "adjacent" | "alternative";
  confidence: "high" | "medium" | "low";
  reason: string;
  evidence: Array<{
    url: string;
    support: string;
  }>;
  status: "pending" | "ignored" | "approved";
  model_name: string | null;
  approved_brand_id: number | null;
};

export type CompetitorDiscoveryResult = {
  project_id: number;
  target_brand: string;
  method: string;
  max_candidates: number;
  generated_count: number;
  suggestions: CompetitorDiscoverySuggestion[];
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

export type StarterPromptSuggestion = {
  text: string;
  category: string;
  topic_cluster: string;
  rationale: string | null;
};

export type StarterPromptGenerationResult = {
  id: number;
  project_id: number;
  status: string;
  generator_version: string;
  measurement_scope: "brand_wide" | "focused";
  focus_label: string | null;

  model_id: number;
  model_name: string;
  provider_model_id: string;

  target_brand: string;

  website_pages_used: number;
  competitors_used: string[];
  existing_prompts_considered: number;

  requested_count: number;
  generated_count: number;

  topic_clusters: {
    name: string;
    evidence: string[];
    allocated_prompts: number;
  }[];
  coverage_blueprint: {
    topic_distribution: Record<string, number>;
    intent_distribution: Record<string, number>;
    largest_topic_share: number;
    concentration_status: "balanced" | "needs_review" | "focused";
  };
  warnings: string[];
  created_at: string;

  prompts: StarterPromptSuggestion[];
};

export type PromptActiveSetResult = {
  project_id: number;

  total_prompts: number;
  active_prompts: number;
  inactive_prompts: number;

  active_prompt_ids: number[];
};

export type SetupExperiment = {
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

export type BenchmarkJob = {
  id: number;
  project_id: number;
  model_id: number;

  experiment_id: number | null;

  benchmark_mode:
    | "memory"
    | "web_search"
    | "site_rag";

  config_snapshot: Record<
    string,
    unknown
  >;

  status: string;

  total_prompts: number;
  completed_runs: number;
  failed_runs: number;

  progress_percentage: number;

  started_at: string | null;
  completed_at: string | null;

  error_message: string | null;

  created_at: string;
};
