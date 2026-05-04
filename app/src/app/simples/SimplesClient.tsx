"use client";

import { useEffect, useMemo, useState } from "react";
import { normalizeGreekForMatch } from "@/lib/greek/normalize";
import { FACET_FILTERS, filterSimple, sortSimples, type FacetMode, type SimpleFilters } from "@/lib/vocab/filter";
import type {
  RegistryQualitySummary,
  RegistryTerm,
  SimplesRegistryIndex,
  VocabFacet,
  VocabIndex,
  VocabQuality,
  VocabSimple,
} from "@/lib/vocab/types";

const EMPTY_FACETS: Record<string, string> = Object.fromEntries(FACET_FILTERS.map((facet) => [facet.key, ""]));
const MAX_COMPARE = 4;
const RESULT_LIMIT = 250;
const REGISTRY_LIMIT = 500;

const inputClass =
  "h-10 w-full rounded-md border border-slate-400 bg-white px-3 text-sm text-slate-950 shadow-sm outline-none transition focus:border-indigo-600 focus:ring-2 focus:ring-indigo-200";
const smallButtonClass =
  "h-9 rounded-md border border-slate-400 bg-white px-3 text-sm font-medium text-slate-900 shadow-sm transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-200";

const WORK_LABELS: Record<string, string> = {
  AET_LM: "Aetius",
  DIOSC_DMM: "Dioscorides",
  GAL_ALIM: "Galen, Foods",
  GAL_SMT: "Galen, Simples",
  ORIB_CM: "Oribasius",
  PAUL_AEG: "Paul",
};

type ViewMode = "registry" | "evidence";
type RegistryMultiwordFilter = "" | "simple" | "multiword" | "head" | "place";

function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function searchNeedle(value: string): string {
  return normalizeGreekForMatch(value).replace(/\s+/g, " ").trim();
}

function confidenceLabel(value: number | null): string {
  if (value === null) return "n/a";
  return value.toFixed(2);
}

function workLabel(source: string): string {
  return WORK_LABELS[source] ?? source;
}

function sortedSources(sources: Iterable<string>): string[] {
  return [...sources].sort((a, b) => workLabel(a).localeCompare(workLabel(b)));
}

function sourcePrefix(source: string): string {
  return `${source}-`;
}

function qualityTone(axis: string): string {
  if (axis === "HOT") return "border-red-200 bg-red-50 text-red-950";
  if (axis === "COLD") return "border-sky-200 bg-sky-50 text-sky-950";
  if (axis === "DRY") return "border-amber-200 bg-amber-50 text-amber-950";
  if (axis === "WET") return "border-emerald-200 bg-emerald-50 text-emerald-950";
  return "border-slate-300 bg-slate-50 text-slate-950";
}

function qualityLabel(quality: Pick<VocabQuality | RegistryQualitySummary, "axis" | "degree">): string {
  return `${quality.axis}${quality.degree ? ` ${quality.degree}` : ""}`;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-300 bg-slate-50 px-3 py-2">
      <div className="text-[11px] font-semibold uppercase text-slate-500">{label}</div>
      <div className="mt-0.5 text-sm font-semibold text-slate-950">{value}</div>
    </div>
  );
}

function SourceBadges({ sources, compact = false }: { sources: Record<string, number>; compact?: boolean }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {Object.entries(sources).sort(([a], [b]) => workLabel(a).localeCompare(workLabel(b))).map(([source, count]) => (
        <span
          key={source}
          className={`rounded border border-indigo-200 bg-indigo-50 font-mono text-indigo-950 ${
            compact ? "px-1.5 py-0.5 text-[11px]" : "px-2 py-1 text-xs"
          }`}
          title={source}
        >
          {workLabel(source)} {count}
        </span>
      ))}
    </div>
  );
}

function QualityBadge({ quality }: { quality: VocabQuality | RegistryQualitySummary }) {
  return (
    <span className={`rounded border px-2 py-1 text-xs font-medium ${qualityTone(quality.axis)}`}>
      {qualityLabel(quality)}
      <span className="ml-1 font-normal opacity-75">{quality.entry_count}</span>
    </span>
  );
}

function reviewLabel(status: RegistryTerm["name_relation"]["status"]): string {
  if (status === "pending_candidates") return "pending";
  if (status === "mixed_review") return "mixed";
  return status;
}

function reviewTone(status: RegistryTerm["name_relation"]["status"]): string {
  if (status === "pending_candidates") return "border-amber-200 bg-amber-50 text-amber-950";
  if (status === "reviewed") return "border-emerald-200 bg-emerald-50 text-emerald-950";
  if (status === "mixed_review") return "border-sky-200 bg-sky-50 text-sky-950";
  return "border-slate-300 bg-slate-50 text-slate-800";
}

function RegistryStatusBadge({ term }: { term: RegistryTerm }) {
  return (
    <span className={`rounded border px-2 py-1 text-xs font-medium ${reviewTone(term.name_relation.status)}`}>
      {reviewLabel(term.name_relation.status)}
      {term.name_relation.candidate_count ? <span className="ml-1 font-normal">{term.name_relation.candidate_count}</span> : null}
    </span>
  );
}

function exportRegistry(rows: RegistryTerm[], format: "csv" | "json") {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `simples-registry-${timestamp}.${format}`;
  let body: string;
  let type: string;

  if (format === "json") {
    body = JSON.stringify(rows, null, 2);
    type = "application/json";
  } else {
    const headers = [
      "term_key",
      "preferred_display",
      "entry_count",
      "occurrence_count",
      "source_count",
      "text_sources",
      "author_groups",
      "is_multiword",
      "head_lemma_normalized",
      "variant_place_lemma_normalized",
      "confidence_avg",
      "review_status",
      "candidate_count",
    ];
    const escape = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    body = [
      headers.join(","),
      ...rows.map((term) => headers.map((header) => {
        if (header === "text_sources") return escape(term.text_sources.join(";"));
        if (header === "author_groups") return escape(term.author_groups.join(";"));
        if (header === "review_status") return escape(term.name_relation.status);
        if (header === "candidate_count") return escape(term.name_relation.candidate_count);
        return escape(term[header as keyof RegistryTerm]);
      }).join(",")),
    ].join("\n");
    type = "text/csv";
  }

  const blob = new Blob([body], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function registryMatches(
  term: RegistryTerm,
  filters: {
    query: string;
    source: string;
    author: string;
    reviewStatus: string;
    multiword: RegistryMultiwordFilter;
    crossCorpus: boolean;
  },
): boolean {
  if (filters.query.trim()) {
    const query = searchNeedle(filters.query);
    if (!searchNeedle(term.search_text).includes(query)) return false;
  }
  if (filters.source && !term.source_counts[filters.source]) return false;
  if (filters.author && !term.author_counts[filters.author]) return false;
  if (filters.reviewStatus && term.name_relation.status !== filters.reviewStatus) return false;
  if (filters.crossCorpus && term.source_count < 2) return false;
  if (filters.multiword === "simple" && term.is_multiword) return false;
  if (filters.multiword === "multiword" && !term.is_multiword) return false;
  if (filters.multiword === "head" && !term.head_lemma_normalized) return false;
  if (filters.multiword === "place" && !term.variant_place_lemma_normalized) return false;
  return true;
}

function sortRegistryTerms(rows: RegistryTerm[], sortKey: string): RegistryTerm[] {
  return [...rows].sort((a, b) => {
    if (sortKey === "source_count") return b.source_count - a.source_count || b.entry_count - a.entry_count;
    if (sortKey === "occurrence_count") return b.occurrence_count - a.occurrence_count || b.entry_count - a.entry_count;
    if (sortKey === "confidence") return (b.confidence_avg ?? 0) - (a.confidence_avg ?? 0) || b.entry_count - a.entry_count;
    if (sortKey === "lemma") return a.preferred_display.localeCompare(b.preferred_display, "el");
    if (sortKey === "review") return b.name_relation.candidate_count - a.name_relation.candidate_count || b.entry_count - a.entry_count;
    return b.entry_count - a.entry_count || b.source_count - a.source_count;
  });
}

function RegistryList({
  terms,
  total,
  selectedKey,
  onSelect,
}: {
  terms: RegistryTerm[];
  total: number;
  selectedKey: string | null;
  onSelect: (term: RegistryTerm) => void;
}) {
  return (
    <section className="overflow-hidden rounded-md border border-slate-300 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-slate-300 bg-slate-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-950">Named Simples</h2>
        <div className="text-xs font-medium text-slate-700">
          {formatCount(Math.min(total, REGISTRY_LIMIT))} of {formatCount(total)}
        </div>
      </div>

      <div className="max-h-[72vh] overflow-y-auto">
        {terms.length === 0 ? (
          <div className="p-6 text-sm text-slate-700">No registry terms match these filters.</div>
        ) : (
          <div className="divide-y divide-slate-200">
            {terms.map((term) => {
              const selected = selectedKey === term.term_key;
              return (
                <article key={term.term_key} className={selected ? "bg-indigo-50" : "bg-white"}>
                  <button
                    type="button"
                    onClick={() => onSelect(term)}
                    className={`grid w-full gap-3 p-3 text-left focus:outline-none focus:ring-2 focus:ring-indigo-200 ${
                      selected ? "border-l-4 border-indigo-700 pl-2" : "border-l-4 border-transparent"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="break-words font-serif text-xl leading-7 text-slate-950">{term.preferred_display}</div>
                        <div className="mt-0.5 break-all font-mono text-xs text-slate-500">{term.term_key}</div>
                      </div>
                      <div className="grid shrink-0 justify-items-end gap-1.5">
                        <span className="rounded border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-800">
                          {formatCount(term.entry_count)} entries
                        </span>
                        <RegistryStatusBadge term={term} />
                      </div>
                    </div>
                    <SourceBadges sources={term.source_counts} compact />
                    {term.quality_summary.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {term.quality_summary.slice(0, 5).map((quality) => (
                          <QualityBadge key={`${quality.axis}-${quality.degree ?? "none"}`} quality={quality} />
                        ))}
                      </div>
                    ) : null}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

function RegistryDetail({
  term,
  activeSource,
  onOpenEvidence,
}: {
  term: RegistryTerm | null;
  activeSource: string;
  onOpenEvidence: (termKey: string, source?: string) => void;
}) {
  if (!term) {
    return (
      <aside className="rounded-md border border-slate-300 bg-white p-5 text-sm text-slate-700 shadow-sm">
        Select a registry term to inspect source coverage and review status.
      </aside>
    );
  }

  const scopedSources = activeSource
    ? { [activeSource]: term.source_counts[activeSource] ?? 0 }
    : term.source_counts;
  const visibleForms = activeSource
    ? term.forms.filter((form) => form.text_sources.includes(activeSource))
    : term.forms;
  const visibleSamples = activeSource
    ? term.entry_samples.filter((entryId) => entryId.startsWith(sourcePrefix(activeSource)))
    : term.entry_samples;
  const sourceMetric = activeSource ? term.source_counts[activeSource] ?? 0 : term.source_count;

  return (
    <aside className="rounded-md border border-slate-300 bg-white shadow-sm">
      <div className="border-b border-slate-300 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="break-words font-serif text-3xl leading-tight text-slate-950">{term.preferred_display}</h2>
              <RegistryStatusBadge term={term} />
            </div>
            <p className="mt-1 break-all font-mono text-xs text-slate-500">{term.term_key}</p>
            <p className="mt-2 text-sm text-slate-700">Draft ancient term, not a final physical substance.</p>
          </div>
          <div className="grid grid-cols-3 gap-2 sm:min-w-[290px]">
            <Metric label="Entries" value={formatCount(term.entry_count)} />
            <Metric label="Occurrences" value={formatCount(term.occurrence_count)} />
            <Metric label={activeSource ? "Work Hits" : "Works"} value={formatCount(sourceMetric)} />
          </div>
        </div>
      </div>

      <div className="grid gap-6 p-5">
        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Work Coverage</h3>
          <div className="mt-2">
            <SourceBadges sources={scopedSources} />
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {Object.entries(term.author_counts).map(([author, count]) => (
              <span key={author} className="rounded-md border border-slate-300 bg-slate-50 px-2 py-1 text-xs">
                {author} <span className="text-slate-500">{count}</span>
              </span>
            ))}
          </div>
        </section>

        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Forms</h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {visibleForms.slice(0, 18).map((form) => (
              <span key={`${form.display}-${form.normalized}`} className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs">
                <span className="font-serif text-sm text-slate-950">{form.display}</span>
                <span className="ml-1 text-slate-500">{form.count}</span>
              </span>
            ))}
          </div>
        </section>

        <section className="grid gap-2">
          <h3 className="text-xs font-semibold uppercase text-slate-500">Registry Flags</h3>
          <div className="grid gap-2 sm:grid-cols-2">
            <Metric label="Confidence" value={confidenceLabel(term.confidence_avg)} />
            <Metric label="Labels" value={Object.entries(term.labels).map(([label, count]) => `${label} ${count}`).join(", ") || "none"} />
            <Metric label="Head" value={term.head_lemma_normalized || "none"} />
            <Metric label="Place Variant" value={term.variant_place_lemma_normalized || "none"} />
          </div>
        </section>

        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Quality Summary</h3>
          {term.quality_summary.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {term.quality_summary.map((quality) => (
                <QualityBadge key={`${quality.axis}-${quality.degree ?? "none"}`} quality={quality} />
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-700">No compact quality summary linked.</p>
          )}
        </section>

        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Name-Relation Review</h3>
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            <Metric label="Status" value={reviewLabel(term.name_relation.status)} />
            <Metric label="Candidates" value={formatCount(term.name_relation.candidate_count)} />
            <Metric label="Reviewed" value={formatCount(term.name_relation.reviewed_count)} />
          </div>
        </section>

        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Entry Samples</h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {visibleSamples.slice(0, 20).map((entryId) => (
              <span key={entryId} className="rounded border border-slate-300 bg-slate-50 px-2 py-1 font-mono text-xs text-slate-800">
                {entryId}
              </span>
            ))}
            {visibleSamples.length === 0 ? <span className="text-sm text-slate-700">No sampled entries for this work.</span> : null}
          </div>
        </section>

        <button type="button" onClick={() => onOpenEvidence(term.term_key, activeSource)} className={smallButtonClass}>
          Open Evidence View
        </button>
      </div>
    </aside>
  );
}

function RegistryView({
  registry,
  onOpenEvidence,
}: {
  registry: SimplesRegistryIndex;
  onOpenEvidence: (termKey: string, source?: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("");
  const [author, setAuthor] = useState("");
  const [reviewStatus, setReviewStatus] = useState("");
  const [multiword, setMultiword] = useState<RegistryMultiwordFilter>("");
  const [crossCorpus, setCrossCorpus] = useState(false);
  const [sortKey, setSortKey] = useState("entry_count");
  const [selectedKey, setSelectedKey] = useState<string | null>(registry.terms[0]?.term_key ?? null);

  const sources = sortedSources(Object.keys(registry.stats.sources));
  const authors = Object.keys(registry.stats.author_groups).sort();

  const filtered = useMemo(() => {
    const filters = { query, source, author, reviewStatus, multiword, crossCorpus };
    return sortRegistryTerms(registry.terms.filter((term) => registryMatches(term, filters)), sortKey);
  }, [author, crossCorpus, multiword, query, registry.terms, reviewStatus, sortKey, source]);

  const selected = useMemo(() => {
    return filtered.find((term) => term.term_key === selectedKey) ?? filtered[0] ?? null;
  }, [filtered, selectedKey]);

  const visible = filtered.slice(0, REGISTRY_LIMIT);

  function resetFilters() {
    setQuery("");
    setSource("");
    setAuthor("");
    setReviewStatus("");
    setMultiword("");
    setCrossCorpus(false);
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-md border border-slate-300 bg-white p-4 shadow-sm">
        <div className="grid gap-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(280px,2fr)_repeat(5,minmax(120px,1fr))]">
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className={inputClass}
                placeholder="Greek display, normalized term, work, author"
              />
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Work</span>
              <select value={source} onChange={(event) => setSource(event.target.value)} className={inputClass}>
                <option value="">All works</option>
                {sources.map((item) => <option key={item} value={item}>{workLabel(item)} ({item})</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Author</span>
              <select value={author} onChange={(event) => setAuthor(event.target.value)} className={inputClass}>
                <option value="">All authors</option>
                {authors.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Review</span>
              <select value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)} className={inputClass}>
                <option value="">Any status</option>
                <option value="none">No candidates</option>
                <option value="pending_candidates">Pending candidates</option>
                <option value="reviewed">Reviewed</option>
                <option value="mixed_review">Mixed review</option>
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Term Type</span>
              <select value={multiword} onChange={(event) => setMultiword(event.target.value as RegistryMultiwordFilter)} className={inputClass}>
                <option value="">Any term</option>
                <option value="simple">Single/simple terms</option>
                <option value="multiword">Multiword terms</option>
                <option value="head">Has head term</option>
                <option value="place">Place-qualified</option>
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Sort</span>
              <select value={sortKey} onChange={(event) => setSortKey(event.target.value)} className={inputClass}>
                <option value="entry_count">Most entries</option>
                <option value="occurrence_count">Most occurrences</option>
                <option value="source_count">Most sources</option>
                <option value="review">Most review candidates</option>
                <option value="confidence">Highest confidence</option>
                <option value="lemma">Greek A-Z</option>
              </select>
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-3 border-t border-slate-300 pt-4 text-sm">
            <label className="flex h-9 items-center gap-2 rounded-md border border-slate-400 bg-white px-3 font-medium text-slate-900">
              <input type="checkbox" checked={crossCorpus} onChange={(event) => setCrossCorpus(event.target.checked)} />
              Appears in multiple works
            </label>
            {source ? (
              <span className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-950">
                Work: {workLabel(source)}
              </span>
            ) : null}
            <button type="button" onClick={resetFilters} className={smallButtonClass}>Reset</button>
            <button type="button" onClick={() => exportRegistry(filtered, "csv")} className={smallButtonClass}>Export CSV</button>
            <button type="button" onClick={() => exportRegistry(filtered, "json")} className={smallButtonClass}>Export JSON</button>
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(360px,0.56fr)_minmax(0,1fr)]">
        <RegistryList
          terms={visible}
          total={filtered.length}
          selectedKey={selected?.term_key ?? null}
          onSelect={(term) => setSelectedKey(term.term_key)}
        />
        <div className="xl:sticky xl:top-4 xl:self-start">
          <RegistryDetail term={selected} activeSource={source} onOpenEvidence={onOpenEvidence} />
        </div>
      </section>
    </div>
  );
}

function topFacetValues(simple: VocabSimple, label: string, limit = 6): VocabFacet[] {
  return (simple.facets[label] ?? []).slice(0, limit);
}

function VocabSourceBadges({ simple, activeSource = "", compact = false }: { simple: VocabSimple; activeSource?: string; compact?: boolean }) {
  const sources = activeSource ? { [activeSource]: simple.sources[activeSource] ?? 0 } : simple.sources;
  return <SourceBadges sources={sources} compact={compact} />;
}

function EvidenceResultList({
  simples,
  total,
  selectedKey,
  compareKeys,
  onSelect,
  onToggleCompare,
}: {
  simples: VocabSimple[];
  total: number;
  selectedKey: string | null;
  compareKeys: string[];
  onSelect: (simple: VocabSimple) => void;
  onToggleCompare: (simple: VocabSimple) => void;
}) {
  return (
    <section className="overflow-hidden rounded-md border border-slate-300 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-slate-300 bg-slate-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-950">Evidence Results</h2>
        <div className="text-xs font-medium text-slate-700">{formatCount(Math.min(total, RESULT_LIMIT))} of {formatCount(total)}</div>
      </div>
      <div className="max-h-[70vh] overflow-y-auto">
        {simples.length === 0 ? (
          <div className="p-6 text-sm text-slate-700">No simples match these filters.</div>
        ) : (
          <div className="divide-y divide-slate-200">
            {simples.map((simple) => {
              const isSelected = selectedKey === simple.lemma_normalized;
              const isCompared = compareKeys.includes(simple.lemma_normalized);
              return (
                <article key={simple.lemma_normalized} className={isSelected ? "bg-indigo-50" : "bg-white"}>
                  <div className={`grid gap-3 p-3 ${isSelected ? "border-l-4 border-indigo-700 pl-2" : "border-l-4 border-transparent"}`}>
                    <div className="flex items-start justify-between gap-3">
                      <button type="button" onClick={() => onSelect(simple)} className="min-w-0 text-left focus:outline-none focus:ring-2 focus:ring-indigo-200">
                        <div className="break-words font-serif text-xl leading-7 text-slate-950">{simple.display}</div>
                        <div className="mt-0.5 break-all font-mono text-xs text-slate-500">{simple.lemma_normalized}</div>
                      </button>
                      <div className="flex shrink-0 flex-col items-end gap-2">
                        <span className="rounded border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-800">
                          {formatCount(simple.entry_count)} entries
                        </span>
                        <button
                          type="button"
                          onClick={() => onToggleCompare(simple)}
                          className={`h-8 rounded-md border px-2.5 text-xs font-medium transition focus:outline-none focus:ring-2 focus:ring-indigo-200 ${
                            isCompared ? "border-indigo-700 bg-indigo-700 text-white" : "border-slate-400 bg-white text-slate-900 hover:bg-slate-100"
                          }`}
                        >
                          {isCompared ? "Added" : "Compare"}
                        </button>
                      </div>
                    </div>
                    <VocabSourceBadges simple={simple} compact />
                    {simple.qualities.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {simple.qualities.slice(0, 6).map((quality) => (
                          <QualityBadge key={`${quality.axis}-${quality.degree ?? "none"}`} quality={quality} />
                        ))}
                      </div>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

function FacetGroup({ title, facets }: { title: string; facets: VocabFacet[] }) {
  if (facets.length === 0) return null;
  return (
    <section className="grid gap-2">
      <h3 className="text-xs font-semibold uppercase text-slate-500">{title}</h3>
      <div className="flex flex-wrap gap-1.5">
        {facets.map((facet) => (
          <span key={facet.key} className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-900">
            <span className="font-serif text-sm text-slate-950">{facet.display}</span>
            <span className="ml-1 text-slate-500">{facet.entry_count}</span>
            {facet.direct ? <span className="ml-1 rounded bg-slate-100 px-1 text-[10px] uppercase text-slate-700">direct</span> : null}
          </span>
        ))}
      </div>
    </section>
  );
}

function SimpleDetail({ simple, activeSource }: { simple: VocabSimple | null; activeSource: string }) {
  if (!simple) {
    return (
      <aside className="rounded-md border border-slate-300 bg-white p-5 text-sm text-slate-700 shadow-sm">
        Select a simple to inspect extracted evidence.
      </aside>
    );
  }

  const visibleForms = activeSource
    ? simple.forms.filter((form) => form.sources.includes(activeSource))
    : simple.forms;
  const visibleQualities = activeSource
    ? simple.qualities.filter((quality) => quality.sources.includes(activeSource))
    : simple.qualities;
  const evidence = visibleQualities.flatMap((quality) =>
    quality.examples
      .filter((example) => !activeSource || example.source === activeSource)
      .map((example) => ({ ...example, axis: quality.axis, degree: quality.degree })),
  ).slice(0, 10);
  const sourceMetric = activeSource ? simple.sources[activeSource] ?? 0 : simple.source_count;

  return (
    <aside className="rounded-md border border-slate-300 bg-white shadow-sm">
      <div className="border-b border-slate-300 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="break-words font-serif text-3xl leading-tight text-slate-950">{simple.display}</h2>
            <p className="mt-1 break-all font-mono text-xs text-slate-500">{simple.lemma_normalized}</p>
          </div>
          <div className="grid grid-cols-3 gap-2 sm:min-w-[280px]">
            <Metric label="Entries" value={formatCount(simple.entry_count)} />
            <Metric label={activeSource ? "Work Hits" : "Works"} value={formatCount(sourceMetric)} />
            <Metric label="Confidence" value={confidenceLabel(simple.confidence_avg)} />
          </div>
        </div>
        <div className="mt-4">
          <VocabSourceBadges simple={simple} activeSource={activeSource} />
        </div>
      </div>
      <div className="grid gap-6 p-5">
        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Quality Profile</h3>
          {visibleQualities.length > 0 ? (
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {visibleQualities.map((quality) => (
                <div key={`${quality.axis}-${quality.degree ?? "none"}`} className={`rounded-md border p-3 ${qualityTone(quality.axis)}`}>
                  <div className="font-semibold">{qualityLabel(quality)}</div>
                  <div className="mt-1 text-xs opacity-80">
                    {activeSource ? quality.examples.filter((example) => example.source === activeSource).length : quality.entry_count} entries, {quality.direct ? "direct" : "co-occurs"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-700">No quality assertions linked.</p>
          )}
        </section>

        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Forms</h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {visibleForms.slice(0, 16).map((form) => (
              <span key={form.display} className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs">
                <span className="font-serif text-sm text-slate-950">{form.display}</span>
                <span className="ml-1 text-slate-500">{form.count}</span>
              </span>
            ))}
            {visibleForms.length === 0 ? <span className="text-sm text-slate-700">No forms for this work.</span> : null}
          </div>
        </section>

        <div className="grid gap-4">
          {FACET_FILTERS.map((facet) => (
            <FacetGroup key={facet.key} title={facet.label} facets={topFacetValues(simple, facet.key, 12)} />
          ))}
        </div>

        <section>
          <h3 className="text-xs font-semibold uppercase text-slate-500">Evidence</h3>
          <ul className="mt-2 divide-y divide-slate-200 overflow-hidden rounded-md border border-slate-300">
            {evidence.length > 0 ? evidence.map((item, index) => (
              <li key={`${item.entry_id}-${index}`} className="bg-white p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-700">
                  <span className="font-mono">{item.entry_id}</span>
                  <span className={`rounded border px-2 py-0.5 ${qualityTone(item.axis)}`}>{item.axis}{item.degree ? ` ${item.degree}` : ""}</span>
                </div>
                <p className="mt-2 font-serif text-base leading-7 text-slate-950">{item.evidence}</p>
              </li>
            )) : (
              <li className="p-3 text-sm text-slate-700">No evidence snippets available.</li>
            )}
          </ul>
        </section>
      </div>
    </aside>
  );
}

function CompareTray({ simples, activeSource, onRemove }: { simples: VocabSimple[]; activeSource: string; onRemove: (key: string) => void }) {
  if (simples.length === 0) return null;
  return (
    <section className="rounded-md border border-slate-300 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-slate-950">Compare</h2>
        <div className="text-xs font-medium text-slate-700">{simples.length}/{MAX_COMPARE}</div>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {simples.map((simple) => (
          <div key={simple.lemma_normalized} className="rounded-md border border-slate-300 bg-slate-50 p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="break-words font-serif text-xl text-slate-950">{simple.display}</div>
                <div className="break-all font-mono text-xs text-slate-500">{simple.lemma_normalized}</div>
              </div>
              <button type="button" onClick={() => onRemove(simple.lemma_normalized)} className={smallButtonClass}>Remove</button>
            </div>
            <div className="mt-3"><VocabSourceBadges simple={simple} activeSource={activeSource} compact /></div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {simple.qualities.slice(0, 8).map((quality) => <QualityBadge key={`${quality.axis}-${quality.degree ?? "none"}`} quality={quality} />)}
            </div>
            <div className="mt-3 text-xs leading-5 text-slate-700">
              <span className="font-medium text-slate-800">Conditions:</span>{" "}
              {topFacetValues(simple, "CONDITION", 3).map((facet) => facet.display).join(", ") || "none"}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function EvidenceExplorer({ focusTerm, initialSource }: { focusTerm: string; initialSource: string }) {
  const [index, setIndex] = useState<VocabIndex | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [query, setQuery] = useState(focusTerm);
  const [source, setSource] = useState(initialSource);
  const [label, setLabel] = useState("");
  const [axis, setAxis] = useState("");
  const [degree, setDegree] = useState("");
  const [minConfidence, setMinConfidence] = useState(0);
  const [crossCorpus, setCrossCorpus] = useState(false);
  const [facetTerms, setFacetTerms] = useState<Record<string, string>>({ ...EMPTY_FACETS });
  const [mode, setMode] = useState<FacetMode>("and");
  const [sortKey, setSortKey] = useState("entry_count");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [compareKeys, setCompareKeys] = useState<string[]>([]);

  useEffect(() => {
    fetch("/vocab/vocab-index.json")
      .then((response) => {
        if (!response.ok) throw new Error(`Index request failed: ${response.status}`);
        return response.json() as Promise<VocabIndex>;
      })
      .then((payload) => {
        setIndex(payload);
        const focused = payload.simples.find((simple) => simple.lemma_normalized === focusTerm);
        setSelectedKey(focused?.lemma_normalized ?? payload.simples[0]?.lemma_normalized ?? null);
      })
      .catch((error: unknown) => setLoadError(error instanceof Error ? error.message : "Could not load vocab index."));
  }, [focusTerm]);

  const filters: SimpleFilters = useMemo(() => ({
    query,
    source,
    label,
    axis,
    degree,
    minConfidence,
    crossCorpus,
    facetTerms,
    mode,
  }), [axis, crossCorpus, degree, facetTerms, label, minConfidence, mode, query, source]);

  const filtered = useMemo(() => {
    if (!index) return [];
    return sortSimples(index.simples.filter((simple) => filterSimple(simple, filters)), sortKey);
  }, [filters, index, sortKey]);

  const selected = useMemo(() => {
    if (!index) return null;
    return filtered.find((simple) => simple.lemma_normalized === selectedKey) ?? filtered[0] ?? null;
  }, [filtered, index, selectedKey]);

  const compared = useMemo(() => {
    if (!index) return [];
    const byKey = new Map(index.simples.map((simple) => [simple.lemma_normalized, simple]));
    return compareKeys.map((key) => byKey.get(key)).filter((simple): simple is VocabSimple => Boolean(simple));
  }, [compareKeys, index]);

  function updateFacet(labelKey: string, value: string) {
    setFacetTerms((current) => ({ ...current, [labelKey]: value }));
  }

  function resetFilters() {
    setQuery("");
    setSource("");
    setLabel("");
    setAxis("");
    setDegree("");
    setMinConfidence(0);
    setCrossCorpus(false);
    setFacetTerms({ ...EMPTY_FACETS });
    setMode("and");
  }

  function toggleCompare(simple: VocabSimple) {
    setCompareKeys((current) => {
      if (current.includes(simple.lemma_normalized)) return current.filter((key) => key !== simple.lemma_normalized);
      if (current.length >= MAX_COMPARE) return current;
      return [...current, simple.lemma_normalized];
    });
  }

  if (loadError) return <div className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800">{loadError}</div>;
  if (!index) return <div className="rounded-md border border-slate-300 bg-white p-4 text-sm text-slate-700 shadow-sm">Loading evidence index...</div>;

  const sources = sortedSources(Object.keys(index.stats.sources));
  const visibleResults = filtered.slice(0, RESULT_LIMIT);

  return (
    <div className="grid gap-5">
      <section className="rounded-md border border-slate-300 bg-white p-4 shadow-sm">
        <div className="grid gap-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(280px,2fr)_repeat(5,minmax(120px,1fr))]">
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Search</span>
              <input value={query} onChange={(event) => setQuery(event.target.value)} className={inputClass} placeholder="Greek, normalized form, work, evidence" />
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Work</span>
              <select value={source} onChange={(event) => setSource(event.target.value)} className={inputClass}>
                <option value="">All works</option>
                {sources.map((item) => <option key={item} value={item}>{workLabel(item)} ({item})</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Label</span>
              <select value={label} onChange={(event) => setLabel(event.target.value)} className={inputClass}>
                <option value="">Any label</option>
                {index.labels.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Quality</span>
              <select value={axis} onChange={(event) => setAxis(event.target.value)} className={inputClass}>
                <option value="">Any quality</option>
                {index.quality_axes.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Degree</span>
              <select value={degree} onChange={(event) => setDegree(event.target.value)} className={inputClass}>
                <option value="">Any degree</option>
                <option value="1">Degree 1</option>
                <option value="2">Degree 2</option>
                <option value="3">Degree 3</option>
                <option value="4">Degree 4</option>
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-slate-700">Sort</span>
              <select value={sortKey} onChange={(event) => setSortKey(event.target.value)} className={inputClass}>
                <option value="entry_count">Most attested</option>
                <option value="source_count">Most sources</option>
                <option value="confidence">Highest confidence</option>
                <option value="lemma">Lemma A-Z</option>
              </select>
            </label>
          </div>

          <div className="grid gap-3 border-t border-slate-300 pt-4 md:grid-cols-2 xl:grid-cols-3">
            {FACET_FILTERS.map((facet) => (
              <label key={facet.key} className="grid gap-1.5">
                <span className="text-xs font-semibold uppercase text-slate-700">{facet.label}</span>
                <input
                  value={facetTerms[facet.key] ?? ""}
                  onChange={(event) => updateFacet(facet.key, event.target.value)}
                  className={inputClass}
                  list={`facet-options-${facet.key}`}
                  placeholder={`Filter ${facet.label.toLowerCase()}`}
                />
                <datalist id={`facet-options-${facet.key}`}>
                  {(index.facet_options[facet.key] ?? []).slice(0, 80).map((option) => <option key={option.key} value={option.key} />)}
                </datalist>
              </label>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3 border-t border-slate-300 pt-4 text-sm">
            <label className="flex min-w-[230px] items-center gap-3">
              <span className="shrink-0 font-medium text-slate-800">Min confidence</span>
              <input type="range" min="0" max="1" step="0.05" value={minConfidence} onChange={(event) => setMinConfidence(Number(event.target.value) || 0)} className="w-full accent-indigo-700" />
              <span className="w-9 text-right font-mono text-xs text-slate-700">{minConfidence.toFixed(2)}</span>
            </label>
            <label className="flex h-9 items-center gap-2 rounded-md border border-slate-400 bg-white px-3 font-medium text-slate-900">
              <input type="checkbox" checked={crossCorpus} onChange={(event) => setCrossCorpus(event.target.checked)} />
              Appears in multiple works
            </label>
            {source ? (
              <span className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-950">
                Work: {workLabel(source)}
              </span>
            ) : null}
            <div className="flex h-9 overflow-hidden rounded-md border border-slate-400 bg-white">
              <button type="button" onClick={() => setMode("and")} className={`px-3 text-sm font-semibold ${mode === "and" ? "bg-indigo-700 text-white" : "text-slate-800 hover:bg-slate-100"}`}>AND</button>
              <button type="button" onClick={() => setMode("or")} className={`border-l border-slate-400 px-3 text-sm font-semibold ${mode === "or" ? "bg-indigo-700 text-white" : "text-slate-800 hover:bg-slate-100"}`}>OR</button>
            </div>
            <button type="button" onClick={resetFilters} className={smallButtonClass}>Reset</button>
          </div>
        </div>
      </section>

      <CompareTray simples={compared} activeSource={source} onRemove={(key) => setCompareKeys((current) => current.filter((item) => item !== key))} />
      <section className="grid gap-5 xl:grid-cols-[minmax(360px,0.55fr)_minmax(0,1fr)]">
        <EvidenceResultList simples={visibleResults} total={filtered.length} selectedKey={selected?.lemma_normalized ?? null} compareKeys={compareKeys} onSelect={(simple) => setSelectedKey(simple.lemma_normalized)} onToggleCompare={toggleCompare} />
        <div className="xl:sticky xl:top-4 xl:self-start">
          <SimpleDetail simple={selected} activeSource={source} />
        </div>
      </section>
    </div>
  );
}

export default function SimplesClient() {
  const [registry, setRegistry] = useState<SimplesRegistryIndex | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("registry");
  const [focusTerm, setFocusTerm] = useState("");
  const [focusSource, setFocusSource] = useState("");

  useEffect(() => {
    fetch("/simples/registry-index.json")
      .then((response) => {
        if (!response.ok) throw new Error(`Registry request failed: ${response.status}`);
        return response.json() as Promise<SimplesRegistryIndex>;
      })
      .then((payload) => setRegistry(payload))
      .catch((error: unknown) => setLoadError(error instanceof Error ? error.message : "Could not load registry index."));
  }, []);

  if (loadError) {
    return (
      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6">
        <div className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800">{loadError}</div>
      </main>
    );
  }

  if (!registry) {
    return (
      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6">
        <div className="rounded-md border border-slate-300 bg-white p-4 text-sm text-slate-700 shadow-sm">Loading registry index...</div>
      </main>
    );
  }

  function openEvidence(termKey: string, source = "") {
    setFocusTerm(termKey);
    setFocusSource(source);
    setViewMode("evidence");
  }

  return (
    <main className="mx-auto grid w-full max-w-[1500px] gap-5 px-4 py-6 sm:px-6">
      <header className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Simples</h1>
          <p className="mt-1 text-sm text-slate-700">
            {formatCount(registry.stats.terms)} draft ancient terms, {formatCount(registry.stats.occurrences)} occurrences
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <Metric label="Works" value={formatCount(Object.keys(registry.stats.sources).length)} />
          <Metric label="Pending" value={formatCount(registry.stats.review_statuses.pending_candidates ?? 0)} />
          <Metric label="Index" value={viewMode === "registry" ? "Registry" : "Evidence"} />
        </div>
      </header>

      <section className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-300 bg-white p-3 shadow-sm">
        <div className="flex h-10 overflow-hidden rounded-md border border-slate-400 bg-white">
          <button
            type="button"
            onClick={() => setViewMode("registry")}
            className={`px-4 text-sm font-semibold ${viewMode === "registry" ? "bg-indigo-700 text-white" : "text-slate-800 hover:bg-slate-100"}`}
          >
            Registry
          </button>
          <button
            type="button"
            onClick={() => setViewMode("evidence")}
            className={`border-l border-slate-400 px-4 text-sm font-semibold ${viewMode === "evidence" ? "bg-indigo-700 text-white" : "text-slate-800 hover:bg-slate-100"}`}
          >
            Evidence
          </button>
        </div>
        <div className="text-sm text-slate-700">
          Draft ancient-term registry. Identification and physical-substance links remain future review layers.
        </div>
      </section>

      {viewMode === "registry" ? (
        <RegistryView registry={registry} onOpenEvidence={openEvidence} />
      ) : (
        <EvidenceExplorer key={`${focusTerm || "evidence"}-${focusSource}`} focusTerm={focusTerm} initialSource={focusSource} />
      )}
    </main>
  );
}
