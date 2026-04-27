import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Ancient Simples",
  description: "Ancient Simples comparative database MVP",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <html lang="en">
      <body className="antialiased">
        <div className="min-h-screen bg-zinc-50">
          <header className="border-b bg-white">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
              <nav className="flex items-center gap-4">
                <Link href="/entries" className="font-semibold">
                  Ancient Simples
                </Link>
                <Link href="/simples" className="text-sm text-zinc-700 hover:text-black">
                  Simples
                </Link>
              </nav>
              <div className="flex items-center gap-3 text-sm">
                {user ? (
                  <>
                    <span className="text-zinc-600">{user.email}</span>
                    <form action="/logout" method="post">
                      <button className="rounded-md border px-3 py-1.5 hover:bg-zinc-50">
                        Sign out
                      </button>
                    </form>
                  </>
                ) : (
                  <Link className="underline" href="/login">
                    Sign in
                  </Link>
                )}
              </div>
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
