import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PRism AI — Decisive Pull Request Analysis & Triage Tower",
  description: "Automated, multi-agent evaluation of security risk, architectural patterns, and testing coverage for GitHub Pull Requests.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable} dark`}>
      <body className="font-sans bg-zinc-950 text-zinc-100 flex flex-col min-h-screen">
        {/* Decorative Grid Overlays */}
        <div className="fixed inset-0 bg-grid-pattern opacity-60 pointer-events-none z-0" />
        <div className="fixed top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-zinc-900/30 to-transparent pointer-events-none z-0" />
        
        {/* Page Shell */}
        <Navbar />
        <main className="flex-grow z-10 flex flex-col pt-20">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
