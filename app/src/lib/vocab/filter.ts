import { normalizeGreekForMatch } from "@/lib/greek/normalize";
import type { VocabSimple } from "@/lib/vocab/types";

export const FACET_FILTERS = [
  { label: "Condition", key: "CONDITION" },
  { label: "Administration", key: "ADMINISTRATION" },
  { label: "Preparation", key: "PREPARATION" },
  { label: "Process", key: "PROCESS" },
  { label: "Place", key: "PLACE" },
  { label: "Quality property", key: "QUALITY_PROPERTY" },
  { label: "Tool/container", key: "TOOL_CONTAINER" },
  { label: "Part", key: "PART" },
  { label: "Application site", key: "APPLICATION_SITE" },
] as const;

export type FacetMode = "and" | "or";

export type SimpleFilters = {
  query: string;
  source: string;
  label: string;
  axis: string;
  degree: string;
  minConfidence: number;
  crossCorpus: boolean;
  facetTerms: Record<string, string>;
  mode: FacetMode;
};

function searchNeedle(value: string): string {
  return normalizeGreekForMatch(value).replace(/\s+/g, " ").trim();
}

function facetMatches(simple: VocabSimple, label: string, rawQuery: string): boolean {
  const query = searchNeedle(rawQuery);
  const facets = simple.facets[label] ?? [];
  if (!query) return true;
  return facets.some((facet) => {
    const haystack = searchNeedle(`${facet.display} ${facet.key}`);
    return haystack.includes(query);
  });
}

function textMatches(simple: VocabSimple, rawQuery: string): boolean {
  const query = searchNeedle(rawQuery);
  if (!query) return true;
  return simple.search_text.includes(query);
}

export function filterSimple(simple: VocabSimple, filters: SimpleFilters): boolean {
  const predicates: boolean[] = [];

  if (filters.query.trim()) {
    predicates.push(textMatches(simple, filters.query));
  }
  if (filters.source) {
    predicates.push(Boolean(simple.sources[filters.source]));
  }
  if (filters.label) {
    predicates.push(Boolean(simple.labels[filters.label] || (simple.facets[filters.label] ?? []).length));
  }
  if (filters.axis) {
    predicates.push(simple.qualities.some((quality) => quality.axis === filters.axis));
  }
  if (filters.degree) {
    predicates.push(simple.qualities.some((quality) => quality.degree === filters.degree));
  }
  if (filters.minConfidence > 0) {
    predicates.push((simple.confidence_avg ?? 0) >= filters.minConfidence);
  }
  if (filters.crossCorpus) {
    predicates.push(simple.source_count >= 2);
  }

  for (const [label, query] of Object.entries(filters.facetTerms)) {
    if (query.trim()) {
      predicates.push(facetMatches(simple, label, query));
    }
  }

  if (predicates.length === 0) return true;
  return filters.mode === "or"
    ? predicates.some(Boolean)
    : predicates.every(Boolean);
}

export function sortSimples(simples: VocabSimple[], sortKey: string): VocabSimple[] {
  const sorted = [...simples];
  sorted.sort((a, b) => {
    if (sortKey === "lemma") {
      return a.display.localeCompare(b.display, "el");
    }
    if (sortKey === "source_count") {
      return b.source_count - a.source_count || b.entry_count - a.entry_count;
    }
    if (sortKey === "confidence") {
      return (b.confidence_avg ?? 0) - (a.confidence_avg ?? 0) || b.entry_count - a.entry_count;
    }
    return b.entry_count - a.entry_count || b.source_count - a.source_count;
  });
  return sorted;
}

