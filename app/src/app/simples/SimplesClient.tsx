"use client";

import { useEffect, useMemo, useState } from "react";
import { FACET_FILTERS, filterSimple, sortSimples, type FacetMode, type SimpleFilters } from "@/lib/vocab/filter";
import type { VocabFacet, VocabIndex, VocabQuality, VocabSimple } from "@/lib/vocab/types";

const EMPTY_FACETS: Record<string, string> = Object.fromEntries(FACET_FILTERS.map((facet) => [facet.key, ""]));
const MAX_COMPARE = 4;
const RESULT_LIMIT = 250;

const inputClass =
  "h-10 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm text-zinc-950 shadow-sm outline-none transition focus:border-zinc-700 focus:ring-2 focus:ring-zinc-200";
const smallButtonClass =
  "h-9 rounded-md border border-zinc-300 bg-white px-3 text-sm font-medium text-zinc-800 shadow-sm transition hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-zinc-300";

function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function sourceEntries(simple: VocabSimple): Array<[string, number]> {
  return Object.entries(simple.sources).sort(([a], [b]) => a.localeCompare(b));
}

function qualityLabel(quality: Pick<VocabQuality, "axis" | "degree">): string {
  return `${quality.axis}${quality.degree ? ` ${quality.degree}` : ""}`;
}

function topFacetValues(simple: VocabSimple, label: string, limit = 6): VocabFacet[] {
  return (simple.facets[label] ?? []).slice(0, limit);
}

function confidenceLabel(value: number | null): string {
  if (value === null) return "n/a";
  return value.toFixed(2);
}

function qualityTone(axis: string): string {
  if (axis === "HOT") return "border-red-200 bg-red-50 text-red-950";
  if (axis === "COLD") return "border-sky-200 bg-sky-50 text-sky-950";
  if (axis === "DRY") return "border-amber-200 bg-amber-50 text-amber-950";
  if (axis === "WET") return "border-emerald-200 bg-emerald-50 text-emerald-950";
  return "border-zinc-200 bg-zinc-50 text-zinc-900";
}

function SourceBadges({ simple, compact = false }: { simple: VocabSimple; compact?: boolean }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {sourceEntries(simple).map(([source, count]) => (
        <span
          key={source}
          className={`rounded border border-zinc-200 bg-zinc-50 font-mono text-zinc-700 ${
            compact ? "px-1.5 py-0.5 text-[11px]" : "px-2 py-1 text-xs"
          }`}
        >
          {source} {count}
        </span>
      ))}
    </div>
  );
}

function QualityBadge({ quality }: { quality: VocabQuality }) {
  return (
    <span className={`rounded border px-2 py-1 text-xs font-medium ${qualityTone(quality.axis)}`}>
      {qualityLabel(quality)}
      <span className="ml-1 font-normal opacity-75">{quality.entry_count}</span>
    </span>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-white px-3 py-2">
      <div className="text-[11px] font-semibold uppercase text-zinc-500">{label}</div>
      <div className="mt-0.5 text-sm font-semibold text-zinc-950">{value}</div>
    </div>
  );
}

function ResultList({
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
    <section className="overflow-hidden rounded-md border border-zinc-200 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-zinc-200 bg-zinc-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-zinc-950">Results</h2>
        <div className="text-xs font-medium text-zinc-600">
          {formatCount(Math.min(total, RESULT_LIMIT))} of {formatCount(total)}
        </div>
      </div>

      <div className="max-h-[70vh] overflow-y-auto">
        {simples.length === 0 ? (
          <div className="p-6 text-sm text-zinc-600">No simples match these filters.</div>
        ) : (
          <div className="divide-y divide-zinc-200">
            {simples.map((simple) => {
              const isSelected = selectedKey === simple.lemma_normalized;
              const isCompared = compareKeys.includes(simple.lemma_normalized);

              return (
                <article key={simple.lemma_normalized} className={isSelected ? "bg-zinc-50" : "bg-white"}>
                  <div className={`grid gap-3 p-3 ${isSelected ? "border-l-4 border-zinc-900 pl-2" : "border-l-4 border-transparent"}`}>
                    <div className="flex items-start justify-between gap-3">
                      <button
                        type="button"
                        onClick={() => onSelect(simple)}
                        className="min-w-0 text-left focus:outline-none focus:ring-2 focus:ring-zinc-300"
                      >
                        <div className="break-words font-serif text-xl leading-7 text-zinc-950">{simple.display}</div>
                        <div className="mt-0.5 break-all font-mono text-xs text-zinc-500">{simple.lemma_normalized}</div>
                      </button>

                      <div className="flex shrink-0 flex-col items-end gap-2">
                        <span className="rounded border border-zinc-200 bg-white px-2 py-1 text-xs font-medium text-zinc-700">
                          {formatCount(simple.entry_count)} entries
                        </span>
                        <button
                          type="button"
                          onClick={() => onToggleCompare(simple)}
                          className={`h-8 rounded-md border px-2.5 text-xs font-medium transition focus:outline-none focus:ring-2 focus:ring-zinc-300 ${
                            isCompared
                              ? "border-zinc-900 bg-zinc-900 text-white"
                              : "border-zinc-300 bg-white text-zinc-800 hover:bg-zinc-100"
                          }`}
                        >
                          {isCompared ? "Added" : "Compare"}
                        </button>
                      </div>
                    </div>

                    <SourceBadges simple={simple} compact />

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
      <h3 className="text-xs font-semibold uppercase text-zinc-500">{title}</h3>
      <div className="flex flex-wrap gap-1.5">
        {facets.map((facet) => (
          <span key={facet.key} className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-800">
            <span className="font-serif text-sm text-zinc-950">{facet.display}</span>
            <span className="ml-1 text-zinc-500">{facet.entry_count}</span>
            {facet.direct ? <span className="ml-1 rounded bg-zinc-100 px-1 text-[10px] uppercase text-zinc-600">direct</span> : null}
          </span>
        ))}
      </div>
    </section>
  );
}

function SimpleDetail({ simple }: { simple: VocabSimple | null }) {
  if (!simple) {
    return (
      <aside className="rounded-md border border-zinc-200 bg-white p-5 text-sm text-zinc-600 shadow-sm">
        Select a simple to inspect extracted evidence.
      </aside>
    );
  }

  const evidence = simple.qualities.flatMap((quality) =>
    quality.examples.map((example) => ({ ...example, axis: quality.axis, degree: quality.degree })),
  ).slice(0, 10);

  return (
    <aside className="rounded-md border border-zinc-200 bg-white shadow-sm">
      <div className="border-b border-zinc-200 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="break-words font-serif text-3xl leading-tight text-zinc-950">{simple.display}</h2>
            <p className="mt-1 break-all font-mono text-xs text-zinc-500">{simple.lemma_normalized}</p>
          </div>
          <div className="grid grid-cols-3 gap-2 sm:min-w-[280px]">
            <Metric label="Entries" value={formatCount(simple.entry_count)} />
            <Metric label="Sources" value={formatCount(simple.source_count)} />
            <Metric label="Confidence" value={confidenceLabel(simple.confidence_avg)} />
          </div>
        </div>

        <div className="mt-4">
          <SourceBadges simple={simple} />
        </div>
      </div>

      <div className="grid gap-6 p-5">
        <section>
          <h3 className="text-xs font-semibold uppercase text-zinc-500">Quality Profile</h3>
          {simple.qualities.length > 0 ? (
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {simple.qualities.map((quality) => (
                <div key={`${quality.axis}-${quality.degree ?? "none"}`} className={`rounded-md border p-3 ${qualityTone(quality.axis)}`}>
                  <div className="font-semibold">{qualityLabel(quality)}</div>
                  <div className="mt-1 text-xs opacity-80">
                    {quality.entry_count} entries, {quality.direct ? "direct" : "co-occurs"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-zinc-600">No quality assertions linked.</p>
          )}
        </section>

        <section>
          <h3 className="text-xs font-semibold uppercase text-zinc-500">Forms</h3>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {simple.forms.slice(0, 16).map((form) => (
              <span key={form.display} className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs">
                <span className="font-serif text-sm text-zinc-950">{form.display}</span>
                <span className="ml-1 text-zinc-500">{form.count}</span>
              </span>
            ))}
          </div>
        </section>

        <div className="grid gap-4">
          {FACET_FILTERS.map((facet) => (
            <FacetGroup key={facet.key} title={facet.label} facets={topFacetValues(simple, facet.key, 12)} />
          ))}
        </div>

        <section>
          <h3 className="text-xs font-semibold uppercase text-zinc-500">Evidence</h3>
          <ul className="mt-2 divide-y divide-zinc-200 overflow-hidden rounded-md border border-zinc-200">
            {evidence.length > 0 ? evidence.map((item, index) => (
              <li key={`${item.entry_id}-${index}`} className="bg-white p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-600">
                  <span className="font-mono">{item.entry_id}</span>
                  <span className={`rounded border px-2 py-0.5 ${qualityTone(item.axis)}`}>
                    {item.axis}{item.degree ? ` ${item.degree}` : ""}
                  </span>
                </div>
                <p className="mt-2 font-serif text-base leading-7 text-zinc-950">{item.evidence}</p>
              </li>
            )) : (
              <li className="p-3 text-sm text-zinc-600">No evidence snippets available.</li>
            )}
          </ul>
        </section>
      </div>
    </aside>
  );
}

function CompareTray({
  simples,
  onRemove,
}: {
  simples: VocabSimple[];
  onRemove: (key: string) => void;
}) {
  if (simples.length === 0) return null;
  return (
    <section className="rounded-md border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-zinc-950">Compare</h2>
        <div className="text-xs font-medium text-zinc-600">{simples.length}/{MAX_COMPARE}</div>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {simples.map((simple) => (
          <div key={simple.lemma_normalized} className="rounded-md border border-zinc-200 bg-zinc-50 p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="break-words font-serif text-xl text-zinc-950">{simple.display}</div>
                <div className="break-all font-mono text-xs text-zinc-500">{simple.lemma_normalized}</div>
              </div>
              <button type="button" onClick={() => onRemove(simple.lemma_normalized)} className={smallButtonClass}>
                Remove
              </button>
            </div>
            <div className="mt-3">
              <SourceBadges simple={simple} compact />
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {simple.qualities.slice(0, 8).map((quality) => (
                <QualityBadge key={`${quality.axis}-${quality.degree ?? "none"}`} quality={quality} />
              ))}
            </div>
            <div className="mt-3 text-xs leading-5 text-zinc-600">
              <span className="font-medium text-zinc-700">Conditions:</span>{" "}
              {topFacetValues(simple, "CONDITION", 3).map((facet) => facet.display).join(", ") || "none"}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function SimplesClient() {
  const [index, setIndex] = useState<VocabIndex | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("");
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
        setSelectedKey(payload.simples[0]?.lemma_normalized ?? null);
      })
      .catch((error: unknown) => {
        setLoadError(error instanceof Error ? error.message : "Could not load vocab index.");
      });
  }, []);

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
    return index.simples.find((simple) => simple.lemma_normalized === selectedKey) ?? filtered[0] ?? null;
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
      if (current.includes(simple.lemma_normalized)) {
        return current.filter((key) => key !== simple.lemma_normalized);
      }
      if (current.length >= MAX_COMPARE) return current;
      return [...current, simple.lemma_normalized];
    });
  }

  if (loadError) {
    return (
      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6">
        <div className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800">{loadError}</div>
      </main>
    );
  }

  if (!index) {
    return (
      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6">
        <div className="rounded-md border border-zinc-200 bg-white p-4 text-sm text-zinc-600 shadow-sm">Loading vocab index...</div>
      </main>
    );
  }

  const sources = Object.keys(index.stats.sources).sort();
  const visibleResults = filtered.slice(0, RESULT_LIMIT);
  const activeFilters: Array<{ key: string; label: string; clear: () => void }> = [];

  if (query.trim()) activeFilters.push({ key: "query", label: `Search: ${query}`, clear: () => setQuery("") });
  if (source) activeFilters.push({ key: "source", label: `Source: ${source}`, clear: () => setSource("") });
  if (label) activeFilters.push({ key: "label", label: `Label: ${label}`, clear: () => setLabel("") });
  if (axis) activeFilters.push({ key: "axis", label: `Quality: ${axis}`, clear: () => setAxis("") });
  if (degree) activeFilters.push({ key: "degree", label: `Degree: ${degree}`, clear: () => setDegree("") });
  if (minConfidence > 0) {
    activeFilters.push({ key: "confidence", label: `Confidence >= ${minConfidence.toFixed(2)}`, clear: () => setMinConfidence(0) });
  }
  if (crossCorpus) activeFilters.push({ key: "crossCorpus", label: "Cross-corpus", clear: () => setCrossCorpus(false) });
  for (const facet of FACET_FILTERS) {
    const value = facetTerms[facet.key]?.trim();
    if (value) {
      activeFilters.push({
        key: `facet-${facet.key}`,
        label: `${facet.label}: ${value}`,
        clear: () => updateFacet(facet.key, ""),
      });
    }
  }

  return (
    <main className="mx-auto grid w-full max-w-[1500px] gap-5 px-4 py-6 sm:px-6">
      <header className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Simples</h1>
          <p className="mt-1 text-sm text-zinc-600">
            {formatCount(index.stats.simples)} simples, {formatCount(index.stats.entries)} entries, {formatCount(filtered.length)} shown
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <Metric label="Sources" value={formatCount(sources.length)} />
          <Metric label="Labels" value={formatCount(index.labels.length)} />
          <Metric label="Generated" value={formatCount(index.stats.result_files)} />
        </div>
      </header>

      <section className="rounded-md border border-zinc-200 bg-white p-4 shadow-sm">
        <div className="grid gap-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(280px,2fr)_repeat(5,minmax(120px,1fr))]">
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-zinc-600">Search</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className={inputClass}
                placeholder="Greek, normalized form, source ID, evidence"
              />
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-zinc-600">Source</span>
              <select value={source} onChange={(event) => setSource(event.target.value)} className={inputClass}>
                <option value="">All sources</option>
                {sources.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-zinc-600">Label</span>
              <select value={label} onChange={(event) => setLabel(event.target.value)} className={inputClass}>
                <option value="">Any label</option>
                {index.labels.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-zinc-600">Quality</span>
              <select value={axis} onChange={(event) => setAxis(event.target.value)} className={inputClass}>
                <option value="">Any quality</option>
                {index.quality_axes.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-zinc-600">Degree</span>
              <select value={degree} onChange={(event) => setDegree(event.target.value)} className={inputClass}>
                <option value="">Any degree</option>
                <option value="1">Degree 1</option>
                <option value="2">Degree 2</option>
                <option value="3">Degree 3</option>
                <option value="4">Degree 4</option>
              </select>
            </label>
            <label className="grid gap-1.5">
              <span className="text-xs font-semibold uppercase text-zinc-600">Sort</span>
              <select value={sortKey} onChange={(event) => setSortKey(event.target.value)} className={inputClass}>
                <option value="entry_count">Most attested</option>
                <option value="source_count">Most sources</option>
                <option value="confidence">Highest confidence</option>
                <option value="lemma">Lemma A-Z</option>
              </select>
            </label>
          </div>

          <div className="grid gap-3 border-t border-zinc-200 pt-4 md:grid-cols-2 xl:grid-cols-3">
            {FACET_FILTERS.map((facet) => (
              <label key={facet.key} className="grid gap-1.5">
                <span className="text-xs font-semibold uppercase text-zinc-600">{facet.label}</span>
                <input
                  value={facetTerms[facet.key] ?? ""}
                  onChange={(event) => updateFacet(facet.key, event.target.value)}
                  className={inputClass}
                  list={`facet-options-${facet.key}`}
                  placeholder={`Filter ${facet.label.toLowerCase()}`}
                />
                <datalist id={`facet-options-${facet.key}`}>
                  {(index.facet_options[facet.key] ?? []).slice(0, 80).map((option) => (
                    <option key={option.key} value={option.key} />
                  ))}
                </datalist>
              </label>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3 border-t border-zinc-200 pt-4 text-sm">
            <label className="flex min-w-[230px] items-center gap-3">
              <span className="shrink-0 font-medium text-zinc-700">Min confidence</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={minConfidence}
                onChange={(event) => setMinConfidence(Number(event.target.value) || 0)}
                className="w-full accent-zinc-900"
              />
              <span className="w-9 text-right font-mono text-xs text-zinc-600">{minConfidence.toFixed(2)}</span>
            </label>

            <label className="flex h-9 items-center gap-2 rounded-md border border-zinc-300 bg-white px-3 font-medium text-zinc-800">
              <input type="checkbox" checked={crossCorpus} onChange={(event) => setCrossCorpus(event.target.checked)} />
              Cross-corpus only
            </label>

            <div className="flex h-9 overflow-hidden rounded-md border border-zinc-300 bg-white">
              <button
                type="button"
                onClick={() => setMode("and")}
                className={`px-3 text-sm font-semibold ${mode === "and" ? "bg-zinc-900 text-white" : "text-zinc-700 hover:bg-zinc-100"}`}
              >
                AND
              </button>
              <button
                type="button"
                onClick={() => setMode("or")}
                className={`border-l border-zinc-300 px-3 text-sm font-semibold ${mode === "or" ? "bg-zinc-900 text-white" : "text-zinc-700 hover:bg-zinc-100"}`}
              >
                OR
              </button>
            </div>

            <button type="button" onClick={resetFilters} className={smallButtonClass}>
              Reset
            </button>
          </div>

          {activeFilters.length > 0 ? (
            <div className="flex flex-wrap gap-2 border-t border-zinc-200 pt-4">
              {activeFilters.map((filter) => (
                <button
                  key={filter.key}
                  type="button"
                  onClick={filter.clear}
                  className="rounded-full border border-zinc-300 bg-zinc-50 px-3 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-100"
                >
                  {filter.label} x
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      <CompareTray simples={compared} onRemove={(key) => setCompareKeys((current) => current.filter((item) => item !== key))} />

      <section className="grid gap-5 xl:grid-cols-[minmax(360px,0.55fr)_minmax(0,1fr)]">
        <ResultList
          simples={visibleResults}
          total={filtered.length}
          selectedKey={selected?.lemma_normalized ?? null}
          compareKeys={compareKeys}
          onSelect={(simple) => setSelectedKey(simple.lemma_normalized)}
          onToggleCompare={toggleCompare}
        />
        <div className="xl:sticky xl:top-4 xl:self-start">
          <SimpleDetail simple={selected} />
        </div>
      </section>
    </main>
  );
}
