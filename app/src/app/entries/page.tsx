import Link from "next/link";
import { redirect } from "next/navigation";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import { normalizeGreekForMatch } from "@/lib/greek/normalize";

type EntryListItem = {
  entry_id: string;
  source: string;
  ref: string;
  chapter_title_gr: string;
  chapter_title_en: string;
  trans_status: "draft" | "review" | "final";
};

type SearchParams = {
  q?: string;
  source?: string;
  axis?: string;
  degree?: string;
  substance?: string;
};

const QUALITY_AXES = ["HOT", "COLD", "DRY", "WET"];

export default async function EntriesPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const { q, source, axis, degree, substance } = await searchParams;
  const query = (q ?? "").trim();
  const normalized = normalizeGreekForMatch(query).replace(/\s+/g, "");
  const sourceFilter = (source ?? "").trim();
  const axisFilter = QUALITY_AXES.includes((axis ?? "").trim()) ? (axis ?? "").trim() : "";
  const degreeFilter = ["1", "2", "3", "4"].includes((degree ?? "").trim())
    ? (degree ?? "").trim()
    : "";
  const substanceQuery = (substance ?? "").trim();
  const substanceNormalized = normalizeGreekForMatch(substanceQuery).replace(/\s+/g, "");
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("role")
    .eq("id", user.id)
    .maybeSingle();

  const isEditor = profile?.role === "editor";

  const tooShort = normalized.length > 0 && normalized.length < 3;
  const doSearch = normalized.length >= 3;
  const hasFacetFilters = Boolean(sourceFilter || axisFilter || degreeFilter || substanceNormalized);

  const entryIdConstraints: Set<string>[] = [];

  if (axisFilter || degreeFilter) {
    let assertionQuery = supabase
      .from("legacy_vocab_assertions")
      .select("entry_id")
      .eq("assertion_type", "quality")
      .limit(1000);
    if (axisFilter) assertionQuery = assertionQuery.contains("payload", { axis: axisFilter });
    if (degreeFilter) assertionQuery = assertionQuery.contains("payload", { degree: degreeFilter });
    const { data, error } = await assertionQuery;
    if (error) console.error("assertion facet error", error);
    entryIdConstraints.push(new Set((data ?? []).map((row) => row.entry_id as string)));
  }

  if (substanceNormalized) {
    const { data: forms, error: formsError } = await supabase
      .from("legacy_vocab_lemma_forms")
      .select("id")
      .like("form_normalized", `${substanceNormalized}%`)
      .limit(250);
    if (formsError) console.error("substance facet form error", formsError);
    const formIds = (forms ?? []).map((row) => row.id as string);
    if (formIds.length === 0) {
      entryIdConstraints.push(new Set());
    } else {
      const { data: links, error: linksError } = await supabase
        .from("legacy_vocab_entry_lemma_forms")
        .select("entry_id")
        .in("lemma_form_id", formIds)
        .limit(1000);
      if (linksError) console.error("substance facet link error", linksError);
      entryIdConstraints.push(new Set((links ?? []).map((row) => row.entry_id as string)));
    }
  }

  const constrainedEntryIds =
    entryIdConstraints.length === 0
      ? null
      : entryIdConstraints.reduce(
          (acc, item) => new Set([...acc].filter((entryId) => item.has(entryId))),
        );

  let entries: EntryListItem[] = [];
  if (!tooShort && (doSearch || hasFacetFilters)) {
    const bounded = normalized.slice(0, 512);
    let entriesQuery = supabase
      .from("entries")
      .select("entry_id,source,ref,chapter_title_gr,chapter_title_en,trans_status")
      .order("source")
      .order("ref")
      .limit(100);
    if (doSearch) entriesQuery = entriesQuery.like("greek_normalized_prefix", `${bounded}%`);
    if (sourceFilter) entriesQuery = entriesQuery.eq("source", sourceFilter);
    if (constrainedEntryIds !== null) {
      const ids = [...constrainedEntryIds];
      if (ids.length === 0) {
        entries = [];
      } else {
        entriesQuery = entriesQuery.in("entry_id", ids.slice(0, 1000));
      }
    }

    if (constrainedEntryIds === null || constrainedEntryIds.size > 0) {
      const { data, error } = await entriesQuery;
      if (error) console.error("entries search error", error);
      entries = (data ?? []) as EntryListItem[];
    }

  } else if (normalized.length === 0) {
    const { data } = await supabase
      .from("entries")
      .select("entry_id,source,ref,chapter_title_gr,chapter_title_en,trans_status")
      .order("source")
      .order("ref")
      .limit(50);
    entries = (data ?? []) as EntryListItem[];
  }

  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-8">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Entries</h1>
          <p className="mt-1 text-sm text-zinc-600">
          Greek search is diacritics-insensitive prefix matching (≥3 characters).
          </p>
        </div>
        <div className="text-sm text-zinc-600">
          Signed in as <span className="font-medium">{user.email}</span> (
          {isEditor ? "editor" : "viewer"})
        </div>
      </header>

      <form className="mt-6 grid gap-3 rounded-md border bg-white p-4" action="/entries" method="get">
        <input
          name="q"
          defaultValue={query}
          className="w-full rounded-md border px-3 py-2"
          placeholder="Search Greek (prefix ≥ 3)…"
        />
        <div className="grid gap-3 sm:grid-cols-4">
          <select name="source" defaultValue={sourceFilter} className="rounded-md border px-3 py-2">
            <option value="">All sources</option>
            <option value="AET_LM">AET_LM</option>
            <option value="DIOSC_DMM">DIOSC_DMM</option>
            <option value="GAL_ALIM">GAL_ALIM</option>
            <option value="GAL_SMT">GAL_SMT</option>
            <option value="ORIB_CM">ORIB_CM</option>
            <option value="PAUL_AEG">PAUL_AEG</option>
          </select>
          <select name="axis" defaultValue={axisFilter} className="rounded-md border px-3 py-2">
            <option value="">Any quality</option>
            {QUALITY_AXES.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
          <select name="degree" defaultValue={degreeFilter} className="rounded-md border px-3 py-2">
            <option value="">Any degree</option>
            <option value="1">Degree 1</option>
            <option value="2">Degree 2</option>
            <option value="3">Degree 3</option>
            <option value="4">Degree 4</option>
          </select>
          <input
            name="substance"
            defaultValue={substanceQuery}
            className="rounded-md border px-3 py-2"
            placeholder="Substance prefix"
          />
        </div>
        <button className="w-fit rounded-md bg-black px-4 py-2 text-white">Search</button>
      </form>

      {tooShort ? (
        <p className="mt-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm">
          Enter at least 3 Greek characters (after normalization) to search.
        </p>
      ) : null}

      <ul className="mt-6 divide-y rounded-md border bg-white">
        {(entries ?? []).map((e) => (
          <li key={e.entry_id} className="p-3 hover:bg-zinc-50">
            <Link href={`/entries/${encodeURIComponent(e.entry_id)}`}>
              <div className="flex items-baseline justify-between gap-3">
                <div className="font-mono text-sm">{e.entry_id}</div>
                <div className="text-xs text-zinc-600">{e.trans_status}</div>
              </div>
              <div className="mt-1 text-sm">
                <span className="font-medium">{e.chapter_title_en || e.chapter_title_gr}</span>
              </div>
            </Link>
          </li>
        ))}
        {(doSearch || hasFacetFilters) && (entries?.length ?? 0) === 0 ? (
          <li className="p-3 text-sm text-zinc-600">No matches.</li>
        ) : null}
        {!doSearch && !hasFacetFilters ? (
          <li className="p-3 text-sm text-zinc-600">
            Enter a prefix (≥3) or choose filters to see results.
          </li>
        ) : null}
      </ul>
    </main>
  );
}
