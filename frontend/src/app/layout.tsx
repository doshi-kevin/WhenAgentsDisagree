import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "When Agents Disagree",
  description: "Multi-Agent Conflict Resolution Research Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`min-h-screen bg-[var(--background)] text-[var(--foreground)] ${spaceGrotesk.className}`}>
        <nav className="border-b-4 border-[var(--border)] bg-[#FFD93D]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <a href="/" className="flex items-center gap-3 group">
                <div className="w-10 h-10 bg-[#FF6B6B] border-2 border-[var(--border)] shadow-[2px_2px_0px_var(--shadow-color)] flex items-center justify-center text-white font-bold text-sm rounded-md">
                  WD
                </div>
                <span className="font-bold text-2xl text-[var(--foreground)]">When Agents Disagree</span>
              </a>
              <div className="flex gap-2">
                <a href="/" className="px-5 py-2.5 font-bold text-[var(--foreground)] border-2 border-[var(--border)] bg-white shadow-[2px_2px_0px_var(--shadow-color)] rounded-md hover:shadow-[4px_4px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all text-base">
                  Debates
                </a>
                <a href="/admin" className="px-5 py-2.5 font-bold text-[var(--foreground)] border-2 border-[var(--border)] bg-white shadow-[2px_2px_0px_var(--shadow-color)] rounded-md hover:shadow-[4px_4px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all text-base">
                  Admin
                </a>
              </div>
            </div>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
