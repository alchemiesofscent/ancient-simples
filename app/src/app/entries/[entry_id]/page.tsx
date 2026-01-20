import Link from "next/link";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export default async function EntryDetailPage({
  params,
}: {
  params: Promise<{ entry_id: string }>;
}) {
  const { entry_id } = await params;

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

  async function updateEntry(formData: FormData) {
    "use server";
    const translation = String(formData.get("translation") ?? "");
    const transStatus = String(formData.get("trans_status") ?? "draft");
    if (!["draft", "review", "final"].includes(transStatus)) {
      throw new Error("Invalid trans_status");
    }

    const supabase = await createSupabaseServerClient();
    const { error } = await supabase
      .from("entries")
      .update({ translation, trans_status: transStatus })
      .eq("entry_id", entry_id);
    if (error) throw new Error(error.message);

    revalidatePath(`/entries/${encodeURIComponent(entry_id)}`);
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
        <div className="mt-2 whitespace-pre-wrap rounded-md border bg-white p-3 font-serif text-sm leading-7">
          {entry.greek}
        </div>
      </section>

      <section className="mt-6">
        <h2 className="text-sm font-semibold">Translation</h2>
        <div className="mt-2 whitespace-pre-wrap rounded-md border bg-white p-3 text-sm leading-7">
          {entry.translation}
        </div>
      </section>

      {isEditor ? (
        <section className="mt-8 rounded-md border bg-white p-4">
          <h2 className="text-sm font-semibold">Edit (editor)</h2>
          <form className="mt-3 flex flex-col gap-3" action={updateEntry}>
            <label className="text-sm font-medium" htmlFor="trans_status">
              Status
            </label>
            <select
              id="trans_status"
              name="trans_status"
              defaultValue={entry.trans_status}
              className="w-48 rounded-md border px-3 py-2"
            >
              <option value="draft">draft</option>
              <option value="review">review</option>
              <option value="final">final</option>
            </select>

            <label className="text-sm font-medium" htmlFor="translation">
              Translation (supports line breaks)
            </label>
            <textarea
              id="translation"
              name="translation"
              defaultValue={entry.translation}
              rows={12}
              className="w-full rounded-md border px-3 py-2 font-sans text-sm"
            />
            <button className="w-fit rounded-md bg-black px-4 py-2 text-white">
              Save
            </button>
          </form>
        </section>
      ) : (
        <p className="mt-8 text-sm text-zinc-600">
          Viewer mode: editing disabled.
        </p>
      )}
    </main>
  );
}
