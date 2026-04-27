"use client";

import { useEffect, useMemo, useState } from "react";
import { FACET_FILTERS, filterSimple, sortSimples, type FacetMode, type SimpleFilters } from "@/lib/vocab/filter";
import type { VocabFacet, VocabIndex, VocabQuality, VocabSimple } from "@/lib/vocab/types";

const EMPTY_FACETS = Object.fromEntries(FACET_FILTERS.map((facet) => [facet.key, ""]));
const MAX_COMPARE = 4;

function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

function sourceSummary(simple: VocabSimple): string {
  return Object.entries(simple.sources)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([source, count]) => `${source} ${count}`)
    .join(" · ");
}

function qualityLabel(quality: VocabQuality): string {
  return `${quality.axis}${quality.degree ? ` ${quality.degree}` : ""}`;
}

function topFacetValues(simple: VocabSimple, label: string, limit = 6): VocabFacet[] {
  return (simple.facets[label] ?? []).slice(0, limit);
}

function ResultList({
  simples,
  selectedKey,
  compareKeys,
  onSelect,
  onToggleCompare,
}: {
  simples: VocabSimple[];
  selectedKey: string | null;
  compareKeys: string[];
  onSelect: (simple: VocabSimple) => void;
  onToggleCompare: (simple: VocabSimple) => void;
}) {
  return (
    <div className="divide-y rounded-md border bg-white">
      {simples.map((simple) => {
        const isSelected = selectedKey === simple.lemma_normalized;
        const isCompared = compareKeys.includes(simple.lemma_normalized);
        return (
          <button
            key={simple.lemma_normalized}
            type="button"
            onClick={() => onSelect(simple)}
            className={`grid w-full gap-2 p-3 text-left hover:bg-zinc-50 ${isSelected ? "bg-zinc-100" : ""}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-serif text-lg leading-6">{simple.display}</div>
                <div className="mt-1 font-mono text-xs text-zinc-600">{simple.lemma_normalized}</div>
              </div>
              <span className="shrink-0 rounded border px-2 py-1 text-xs text-zinc-600">
                {formatCount(simple.entry_count)} entries
              </span>
            </div>
            <div className="text-xs text-zinc-600">{sourceSummary(simple)}</div>
            <div className="flex flex-wrap gap-1">
              {simple.qualities.slice(0, 5).map((quality) => (
                <span key={`${quality.axis}-${quality.degree ?? "none"}`} className="rounded border bg-zinc-50 px-2 py-0.5 text-xs">
                  {qualityLabel(quality)}
                </span>
              ))}
            </div>
            <div
              role="button"
              tabIndex={0}
              onClick={(event) => {
                event.stopPropagation();
                onToggleCompare(simple);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  event.stopPropagation();
                  onToggleCompare(simple);
                }
              }}
              className={`w-fit rounded-md border px-2 py-1 text-xs ${isCompared ? "bg-black text-white" : "bg-white text-zinc-700"}`}
            >
              {isCompared ? "Comparing" : "Compare"}
            </div>
          </button>
        );
      })}
      {simples.length === 0 ? (
        <div className="p-4 text-sm text-zinc-600">No simples match these filters.</div>
      ) : null}
    </div>
  );
}

function FacetGroup({ title, facets }: { title: string; facets: VocabFacet[] }) {
  if (facets.length === 0) return null;
  return (
    <section>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{title}</h3>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {facets.map((facet) => (
          <span key={facet.key} className="rounded border bg-white px-2 py-1 text-xs">
            <span className="font-serif">{facet.display}</span>
            <span className="ml-1 text-zinc-500">{facet.count}</span>
            {facet.direct ? <span className="ml-1 text-zinc-500">direct</span> : null}
          </span>
        ))}
      </div>
    </section>
  );
}

function SimpleDetail({ simple }: { simple: VocabSimple | null }) {
  if (!simple) {
    return (
      <aside className="rounded-md border bg-white p-4 text-sm text-zinc-600">
        Select a simple to inspect its extracted evidence.
      </aside>
    );
  }

  const evidence = simple.qualities.flatMap((quality) =>
    quality.examples.map((example) => ({ ...example, axis: quality.axis, degree: quality.degree })),
  ).slice(0, 8);

  return (
    <aside className="rounded-md border bg-white p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-serif text-2xl">{simple.display}</h2>
          <p className="mt-1 font-mono text-xs text-zinc-600">{simple.lemma_normalized}</p>
        </div>
        <div className="text-right text-xs text-zinc-600">
          <div>{formatCount(simple.entry_count)} entries</div>
          <div>{simple.source_count} sources</div>
        </div>
      </div>

      <section className="mt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Quality Profile</h3>
        <div className="mt-2 grid grid-cols-2 gap-2">
          {simple.qualities.length > 0 ? simple.qualities.map((quality) => (
            <div key={`${quality.axis}-${quality.degree ?? "none"}`} className="rounded-md border bg-zinc-50 p-2">
              <div className="font-medium">{qualityLabel(quality)}</div>
              <div className="text-xs text-zinc-600">
                {quality.entry_count} entries · {quality.direct ? "direct" : "co-occurs"}
              </div>
            </div>
          )) : (
            <div className="col-span-2 text-sm text-zinc-600">No quality assertions linked.</div>
          )}
        </div>
      </section>

      <div className="mt-5 grid gap-4">
        {FACET_FILTERS.map((facet) => (
          <FacetGroup key={facet.key} title={facet.label} facets={topFacetValues(simple, facet.key, 10)} />
        ))}
      </div>

      <section className="mt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Forms</h3>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {simple.forms.slice(0, 12).map((form) => (
            <span key={form.display} className="rounded border bg-white px-2 py-1 text-xs">
              <span className="font-serif">{form.display}</span>
              <span className="ml-1 text-zinc-500">{form.count}</span>
            </span>
          ))}
        </div>
      </section>

      <section className="mt-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Evidence</h3>
        <ul className="mt-2 divide-y rounded-md border">
          {evidence.length > 0 ? evidence.map((item, index) => (
            <li key={`${item.entry_id}-${index}`} className="p-2 text-sm">
              <div className="flex items-center justify-between gap-2 text-xs text-zinc-600">
                <span>{item.entry_id}</span>
                <span>{item.axis}{item.degree ? ` ${item.degree}` : ""}</span>
              </div>
              <p className="mt-1 font-serif leading-6">{item.evidence}</p>
            </li>
          )) : (
            <li className="p-2 text-sm text-zinc-600">No evidence snippets available.</li>
          )}
        </ul>
      </section>
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
    <section className="mt-6 rounded-md border bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">Compare Simples</h2>
        <div className="text-xs text-zinc-600">{simples.length}/{MAX_COMPARE}</div>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {simples.map((simple) => (
          <div key={simple.lemma_normalized} className="rounded-md border bg-zinc-50 p-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="font-serif text-lg">{simple.display}</div>
                <div className="font-mono text-xs text-zinc-600">{simple.lemma_normalized}</div>
              </div>
              <button
                type="button"
                onClick={() => onRemove(simple.lemma_normalized)}
                className="rounded border px-2 py-1 text-xs"
              >
                Remove
              </button>
            </div>
            <div className="mt-3 text-xs text-zinc-600">{sourceSummary(simple)}</div>
            <div className="mt-3 grid grid-cols-2 gap-1.5">
              {simple.qualities.slice(0, 8).map((quality) => (
                <div key={`${quality.axis}-${quality.degree ?? "none"}`} className="rounded border bg-white px-2 py-1 text-xs">
                  {qualityLabel(quality)} · {quality.entry_count}
                </div>
              ))}
            </div>
            <div className="mt-3 text-xs text-zinc-600">
              Conditions: {topFacetValues(simple, "CONDITION", 3).map((facet) => facet.display).join(", ") || "none"}
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
  const [facetTerms, setFacetTerms] = useState<Record<string, string>>(EMPTY_FACETS);
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
      <main className="mx-auto w-full max-w-7xl px-6 py-8">
        <div className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800">{loadError}</div>
      </main>
    );
  }

  if (!index) {
    return (
      <main className="mx-auto w-full max-w-7xl px-6 py-8">
        <div className="rounded-md border bg-white p-4 text-sm text-zinc-600">Loading vocab index...</div>
      </main>
    );
  }

  const sources = Object.keys(index.stats.sources).sort();

  return (
    <main className="mx-auto w-full max-w-7xl px-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Simples</h1>
          <p className="mt-1 text-sm text-zinc-600">
            {formatCount(index.stats.simples)} simples · {formatCount(index.stats.entries)} entries · {formatCount(filtered.length)} shown
          </p>
        </div>
        <div className="text-xs text-zinc-600">
          {index.generated_from.map((path) => (
            <div key={path}>{path}</div>
          ))}
        </div>
      </header>

      <section className="mt-6 rounded-md border bg-white p-4">
        <div className="grid gap-3 lg:grid-cols-[2fr_repeat(5,1fr)]">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="rounded-md border px-3 py-2"
            placeholder="Search any gathered term, evidence, normalized form, or source ID"
          />
          <select value={source} onChange={(event) => setSource(event.target.value)} className="rounded-md border px-3 py-2">
            <option value="">All sources</option>
            {sources.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={label} onChange={(event) => setLabel(event.target.value)} className="rounded-md border px-3 py-2">
            <option value="">Any label</option>
            {index.labels.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={axis} onChange={(event) => setAxis(event.target.value)} className="rounded-md border px-3 py-2">
            <option value="">Any quality</option>
            {index.quality_axes.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select value={degree} onChange={(event) => setDegree(event.target.value)} className="rounded-md border px-3 py-2">
            <option value="">Any degree</option>
            <option value="1">Degree 1</option>
            <option value="2">Degree 2</option>
            <option value="3">Degree 3</option>
            <option value="4">Degree 4</option>
          </select>
          <select value={sortKey} onChange={(event) => setSortKey(event.target.value)} className="rounded-md border px-3 py-2">
            <option value="entry_count">Most attested</option>
            <option value="source_count">Most sources</option>
            <option value="confidence">Highest confidence</option>
            <option value="lemma">Lemma A-Z</option>
          </select>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {FACET_FILTERS.map((facet) => (
            <label key={facet.key} className="grid gap-1 text-sm">
              <span className="text-xs font-medium text-zinc-600">{facet.label}</span>
              <input
                value={facetTerms[facet.key] ?? ""}
                onChange={(event) => updateFacet(facet.key, event.target.value)}
                className="rounded-md border px-3 py-2"
                placeholder={`Filter ${facet.label.toLowerCase()}`}
              />
            </label>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={crossCorpus} onChange={(event) => setCrossCorpus(event.target.checked)} />
            Cross-corpus only
          </label>
          <label className="flex items-center gap-2">
            <span>Min confidence</span>
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={minConfidence}
              onChange={(event) => setMinConfidence(Number(event.target.value) || 0)}
              className="w-24 rounded-md border px-2 py-1"
            />
          </label>
          <div className="flex rounded-md border">
            <button
              type="button"
              onClick={() => setMode("and")}
              className={`px-3 py-1.5 ${mode === "and" ? "bg-black text-white" : "bg-white"}`}
            >
              AND
            </button>
            <button
              type="button"
              onClick={() => setMode("or")}
              className={`border-l px-3 py-1.5 ${mode === "or" ? "bg-black text-white" : "bg-white"}`}
            >
              OR
            </button>
          </div>
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setSource("");
              setLabel("");
              setAxis("");
              setDegree("");
              setMinConfidence(0);
              setCrossCorpus(false);
              setFacetTerms(EMPTY_FACETS);
              setMode("and");
            }}
            className="rounded-md border px-3 py-1.5"
          >
            Reset
          </button>
        </div>
      </section>

      <CompareTray simples={compared} onRemove={(key) => setCompareKeys((current) => current.filter((item) => item !== key))} />

      <section className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(380px,0.85fr)]">
        <ResultList
          simples={filtered.slice(0, 250)}
          selectedKey={selected?.lemma_normalized ?? null}
          compareKeys={compareKeys}
          onSelect={(simple) => setSelectedKey(simple.lemma_normalized)}
          onToggleCompare={toggleCompare}
        />
        <SimpleDetail simple={selected} />
      </section>
    </main>
  );
}
