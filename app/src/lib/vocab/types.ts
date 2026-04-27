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

