import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Ancient Simples",
  description: "Ancient Simples comparative database MVP",
};

async function getOptionalUser() {
  try {
    const supabase = await createSupabaseServerClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    return user;
  } catch {
    return null;
  }
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await getOptionalUser();

  return (
    <html lang="en">
      <body className="antialiased">
        <div className="min-h-screen bg-stone-50">
          <header className="border-b border-slate-700 bg-slate-900 text-white shadow-sm">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
              <nav className="flex items-center gap-4">
                <Link href="/simples" className="font-semibold tracking-normal">
                  Ancient Simples
                </Link>
                <Link href="/simples" className="text-sm text-slate-200 hover:text-white">
                  Simples
                </Link>
                <Link href="/entries" className="text-sm text-slate-300 hover:text-white">
                  Entries
                </Link>
              </nav>
              <div className="flex items-center gap-3 text-sm">
                {user ? (
                  <>
                    <span className="text-slate-200">{user.email}</span>
                    <form action="/logout" method="post">
                      <button className="rounded-md border border-slate-500 px-3 py-1.5 text-slate-100 hover:border-white hover:bg-slate-800">
                        Sign out
                      </button>
                    </form>
                  </>
                ) : (
                  <Link className="rounded-md border border-slate-500 px-3 py-1.5 text-slate-100 hover:border-white hover:bg-slate-800" href="/login">
                    Editor sign in
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
