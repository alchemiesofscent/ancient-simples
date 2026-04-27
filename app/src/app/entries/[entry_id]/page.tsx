import Link from "next/link";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { createSupabaseServerClient } from "@/lib/supabase/server";

type LegacyForm = {
  id: string;
  source_code: string;
  form_grc: string;
  form_normalized: string;
  status: string;
  confidence: number | null;
};

type LegacyLink = {
  lemma_form_id: string;
  role: string;
  confidence: number | null;
};

type LegacyAssertion = {
  id: string;
  assertion_type: string;
  payload: {
    axis?: string;
    degree?: string;
    intensity?: string;
    hedge?: string;
    evidence_display?: string;
    applies_to?: {
      kind?: string;
      lemma_normalized?: string | null;
      substance_lemma_normalized?: string | null;
      part_lemma_normalized?: string | null;
    };
  };
  status: string;
  confidence: number | null;
};

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

  const { data: formLinks } = await supabase
    .from("legacy_vocab_entry_lemma_forms")
    .select("lemma_form_id,role,confidence")
    .eq("entry_id", entry_id)
    .order("confidence", { ascending: false });
  const links = (formLinks ?? []) as LegacyLink[];
  const formIds = links.map((link) => link.lemma_form_id);
  let formsById = new Map<string, LegacyForm>();
  if (formIds.length > 0) {
    const { data: forms } = await supabase
      .from("legacy_vocab_lemma_forms")
      .select("id,source_code,form_grc,form_normalized,status,confidence")
      .in("id", formIds);
    formsById = new Map(((forms ?? []) as LegacyForm[]).map((form) => [form.id, form]));
  }

  const { data: assertions } = await supabase
    .from("legacy_vocab_assertions")
    .select("id,assertion_type,payload,status,confidence")
    .eq("entry_id", entry_id)
    .order("confidence", { ascending: false });
  const qualityAssertions = ((assertions ?? []) as LegacyAssertion[]).filter(
    (item) => item.assertion_type === "quality",
  );

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

      <section className="mt-6 grid gap-6 md:grid-cols-2">
        <div>
          <h2 className="text-sm font-semibold">Extracted Substances</h2>
          <ul className="mt-2 divide-y rounded-md border bg-white">
            {links.length > 0 ? links.map((link) => {
              const form = formsById.get(link.lemma_form_id);
              if (!form) return null;
              return (
                <li key={`${link.lemma_form_id}-${link.role}`} className="p-3 text-sm">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="font-serif text-base">{form.form_grc}</span>
                    <span className="text-xs text-zinc-500">{link.confidence?.toFixed(2) ?? ""}</span>
                  </div>
                  <div className="mt-1 font-mono text-xs text-zinc-600">
                    {form.form_normalized} · {form.status}
                  </div>
                </li>
              );
            }) : (
              <li className="p-3 text-sm text-zinc-600">No imported substances.</li>
            )}
          </ul>
        </div>

        <div>
          <h2 className="text-sm font-semibold">Quality Assertions</h2>
          <ul className="mt-2 divide-y rounded-md border bg-white">
            {qualityAssertions.length > 0 ? qualityAssertions.map((assertion) => (
              <li key={assertion.id} className="p-3 text-sm">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="font-medium">
                    {assertion.payload.axis}
                    {assertion.payload.degree ? ` ${assertion.payload.degree}` : ""}
                  </span>
                  <span className="text-xs text-zinc-500">
                    {assertion.confidence?.toFixed(2) ?? assertion.status}
                  </span>
                </div>
                {assertion.payload.evidence_display ? (
                  <div className="mt-1 font-serif text-sm leading-6">
                    {assertion.payload.evidence_display}
                  </div>
                ) : null}
                {assertion.payload.applies_to?.lemma_normalized ? (
                  <div className="mt-1 font-mono text-xs text-zinc-600">
                    applies to {assertion.payload.applies_to.lemma_normalized}
                  </div>
                ) : null}
              </li>
            )) : (
              <li className="p-3 text-sm text-zinc-600">No imported quality assertions.</li>
            )}
          </ul>
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
