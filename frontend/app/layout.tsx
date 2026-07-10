import type { Metadata } from "next";
import { Orbitron, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import SessionProvider from "@/components/SessionProvider";

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-orbitron",
  display: "swap",
  weight: ["400", "500", "600", "700", "800", "900"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "PRism AI — Decisive Pull Request Analysis & Triage Tower",
  description:
    "Automated, multi-agent evaluation of security risk, architectural patterns, and testing coverage for GitHub Pull Requests.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${orbitron.variable} ${jetbrainsMono.variable} dark`}
    >
      <body className="font-mono bg-background text-foreground flex flex-col min-h-screen overflow-x-hidden">

        {/* ── Circuit grid background — subtle PCB trace pattern ── */}
        <div
          className="fixed inset-0 bg-circuit pointer-events-none z-0"
          aria-hidden="true"
        />

        {/* ── Radial corner glow — neon haze bleeding from top ── */}
        <div
          className="fixed top-0 left-0 right-0 h-[600px] pointer-events-none z-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 40% at 50% 0%, rgba(0,255,136,0.04) 0%, transparent 70%)",
          }}
          aria-hidden="true"
        />

        {/* ── Corner accent glows ── */}
        <div
          className="fixed top-0 left-0 w-[300px] h-[300px] pointer-events-none z-0"
          style={{
            background:
              "radial-gradient(circle at 0% 0%, rgba(0,212,255,0.04) 0%, transparent 60%)",
          }}
          aria-hidden="true"
        />
        <div
          className="fixed bottom-0 right-0 w-[400px] h-[400px] pointer-events-none z-0"
          style={{
            background:
              "radial-gradient(circle at 100% 100%, rgba(255,0,255,0.03) 0%, transparent 60%)",
          }}
          aria-hidden="true"
        />

        {/* ── Page shell ── */}
        <SessionProvider>
          <Navbar />
          <main className="flex-grow z-10 flex flex-col pt-20">
            {children}
          </main>
          <Footer />
        </SessionProvider>
      </body>
    </html>
  );
}
