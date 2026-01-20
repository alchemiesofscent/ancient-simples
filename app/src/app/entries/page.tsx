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

export default async function EntriesPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  const query = (q ?? "").trim();
  const normalized = normalizeGreekForMatch(query).replace(/\s+/g, "");

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

  let entries: EntryListItem[] = [];
  if (doSearch) {
    const { data } = await supabase
      .from("entries")
      .select("entry_id,source,ref,chapter_title_gr,chapter_title_en,trans_status")
      .like("greek_normalized", `${normalized}%`)
      .order("source")
      .order("ref")
      .limit(100);
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

      <form className="mt-6 flex gap-2" action="/entries" method="get">
        <input
          name="q"
          defaultValue={query}
          className="w-full rounded-md border px-3 py-2"
          placeholder="Search Greek (prefix ≥ 3)…"
        />
        <button className="rounded-md bg-black px-4 py-2 text-white">
          Search
        </button>
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
        {doSearch && (entries?.length ?? 0) === 0 ? (
          <li className="p-3 text-sm text-zinc-600">No matches.</li>
        ) : null}
        {!doSearch ? (
          <li className="p-3 text-sm text-zinc-600">
            Enter a prefix (≥3) to see results.
          </li>
        ) : null}
      </ul>
    </main>
  );
}
