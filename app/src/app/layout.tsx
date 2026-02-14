import type { Metadata } from "next";
import Link from "next/link";
import localFont from "next/font/local";
import "./globals.css";

const gentiumPlus = localFont({
  src: [
    { path: "../fonts/GentiumPlus-Regular.ttf", weight: "400", style: "normal" },
    { path: "../fonts/GentiumPlus-Italic.ttf", weight: "400", style: "italic" },
    { path: "../fonts/GentiumPlus-Bold.ttf", weight: "700", style: "normal" },
    { path: "../fonts/GentiumPlus-BoldItalic.ttf", weight: "700", style: "italic" },
  ],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Ancient Simples",
  description: "Ancient Simples comparative database MVP",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${gentiumPlus.className} antialiased`}>
        <div className="min-h-screen bg-zinc-50">
          <header className="border-b bg-white">
            <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
              <Link href="/entries" className="font-semibold">
                Ancient Simples
              </Link>
              <div className="text-sm text-zinc-600">Public read-only</div>
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
