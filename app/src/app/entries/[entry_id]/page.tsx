import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export default async function EntryDetailPage({
  params,
}: {
  params: Promise<{ entry_id: string }>;
}) {
  const { entry_id } = await params;

  const supabase = await createSupabaseServerClient();

  const { data: entry, error } = await supabase
    .from("entries")
    .select(
      "entry_id,source,ref,chapter_title_gr,chapter_title_en,greek,translation,trans_status,word_count,notes"
    )
    .eq("entry_id", entry_id)
    .maybeSingle();

  if (error || !entry) {
    return (
      <main className="mx-auto w-full max-w-4xl px-6 py-8">
        <p className="text-sm text-zinc-600">Entry not found.</p>
        <Link className="mt-4 inline-block underline" href="/entries">
          Back to entries
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-4xl px-6 py-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <Link className="text-sm underline" href="/entries">
            Back
          </Link>
          <h1 className="mt-2 font-mono text-lg">{entry.entry_id}</h1>
          <p className="mt-1 text-sm text-zinc-600">
            {entry.chapter_title_en || entry.chapter_title_gr}
          </p>
        </div>
        <div className="text-right text-xs text-zinc-600">
          <div>{entry.trans_status}</div>
          <div>{entry.word_count ? `${entry.word_count} words` : ""}</div>
        </div>
      </div>

      <section className="mt-6">
        <h2 className="text-sm font-semibold">Greek</h2>
        <div className="mt-2 whitespace-pre-wrap rounded-md border bg-white p-3 text-base leading-8">
          {entry.greek}
        </div>
      </section>

      <section className="mt-6">
        <h2 className="text-sm font-semibold">Translation</h2>
        <div className="mt-2 whitespace-pre-wrap rounded-md border bg-white p-3 text-sm leading-7">
          {entry.translation}
        </div>
      </section>
    </main>
  );
}
