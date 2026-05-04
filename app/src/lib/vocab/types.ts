export type FacetRelation = "direct" | "cooccurs";

export type FacetExample = {
  entry_id: string;
  source: string;
  display?: string;
  evidence?: string;
  confidence: number | null;
  relation: FacetRelation;
};

export type VocabFacet = {
  key: string;
  display: string;
  count: number;
  sources: string[];
  entry_count: number;
  direct: boolean;
  examples: FacetExample[];
};

export type VocabQuality = {
  axis: "HOT" | "COLD" | "DRY" | "WET";
  degree: string | null;
  count: number;
  sources: string[];
  entry_count: number;
  direct: boolean;
  examples: FacetExample[];
};

export type VocabSimple = {
  lemma_normalized: string;
  display: string;
  search_text: string;
  labels: Record<string, number>;
  sources: Record<string, number>;
  entry_ids: string[];
  entry_count: number;
  source_count: number;
  confidence_avg: number | null;
  confidence_band: string;
  forms: Array<{
    display: string;
    count: number;
    sources: string[];
  }>;
  facets: Record<string, VocabFacet[]>;
  qualities: VocabQuality[];
};

export type VocabEntry = {
  entry_id: string;
  source: string;
  simple_keys: string[];
  terms: Array<{
    label: string;
    key: string;
    display: string;
    confidence: number | null;
    applies_to: string[];
  }>;
  qualities: Array<{
    axis: string;
    degree: string | null;
    confidence: number | null;
    evidence: string;
    applies_to: string[];
  }>;
};

export type VocabIndex = {
  version: number;
  generated_from: string[];
  labels: string[];
  quality_axes: Array<"HOT" | "COLD" | "DRY" | "WET">;
  stats: {
    result_files: number;
    entries: number;
    simples: number;
    term_labels: Record<string, number>;
    sources: Record<string, number>;
  };
  facet_options: Record<string, Array<{ key: string; count: number }>>;
  quality_options: Array<{ key: string; count: number }>;
  simples: VocabSimple[];
  entries: VocabEntry[];
};

export type RegistryReviewStatus = "none" | "pending_candidates" | "reviewed" | "mixed_review";

export type RegistryForm = {
  display: string;
  normalized: string;
  count: number;
  entry_count: number;
  text_sources: string[];
  author_groups: string[];
};

export type RegistryQualitySummary = {
  axis: "HOT" | "COLD" | "DRY" | "WET";
  degree: string | null;
  entry_count: number;
  direct: boolean;
};

export type RegistryTerm = {
  term_key: string;
  preferred_display: string;
  lemma_normalized: string;
  labels: Record<string, number>;
  is_multiword: boolean;
  head_lemma_normalized: string;
  variant_place_lemma_normalized: string;
  source_count: number;
  entry_count: number;
  occurrence_count: number;
  text_sources: string[];
  author_groups: string[];
  source_counts: Record<string, number>;
  author_counts: Record<string, number>;
  result_runs: string[];
  confidence_avg: number | null;
  status: string;
  forms: RegistryForm[];
  quality_summary: RegistryQualitySummary[];
  entry_samples: string[];
  name_relation: {
    status: RegistryReviewStatus;
    candidate_count: number;
    pending_count: number;
    reviewed_count: number;
  };
  search_text: string;
};

export type SimplesRegistryIndex = {
  version: number;
  generated_at: string;
  git_commit: string;
  source_files: Record<string, string>;
  future_corpora: Array<{
    label: string;
    expected_source_codes?: string[];
    status?: string;
  }>;
  stats: {
    terms: number;
    occurrences: number;
    forms: number;
    sources: Record<string, number>;
    author_groups: Record<string, number>;
    review_statuses: Record<string, number>;
    registry_manifest_counts: Record<string, unknown>;
  };
  terms: RegistryTerm[];
};
