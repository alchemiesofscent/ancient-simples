"use client";

import { useState } from "react";
import { createSupabaseBrowserClient } from "@/lib/supabase/browser";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("");
    setIsSubmitting(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) throw error;
      setStatus("Check your email for a magic link.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-lg flex-col justify-center px-6">
      <h1 className="text-2xl font-semibold">Sign in</h1>
      <p className="mt-2 text-sm text-zinc-600">
        Use your email to receive a magic link.
      </p>

      <form className="mt-6 flex flex-col gap-3" onSubmit={onSubmit}>
        <label className="text-sm font-medium" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-md border px-3 py-2"
          placeholder="you@example.com"
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 rounded-md bg-black px-3 py-2 text-white disabled:opacity-50"
        >
          {isSubmitting ? "Sending…" : "Send magic link"}
        </button>
      </form>

      {status ? <p className="mt-4 text-sm">{status}</p> : null}
    </main>
  );
}

