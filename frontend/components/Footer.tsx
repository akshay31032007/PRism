import React from "react";
import Link from "next/link";
import { Cpu, Github, Twitter, Linkedin, Shield } from "lucide-react";

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="relative z-10 border-t border-border bg-background">

      {/* Top neon accent line */}
      <div className="h-px w-full bg-gradient-to-r from-transparent via-accent/40 to-transparent shadow-neon-sm" />

      <div className="max-w-7xl mx-auto px-6 pt-12 pb-8 grid grid-cols-1 md:grid-cols-4 gap-10">

        {/* ── Brand column ── */}
        <div className="flex flex-col gap-5">
          <Link href="/" className="group flex items-center gap-2.5 focus-visible:outline-none w-fit">
            <div className="w-8 h-8 cyber-chamfer-sm border border-border bg-card flex items-center justify-center group-hover:border-accent group-hover:shadow-neon-sm transition-all duration-150">
              <Cpu className="w-3.5 h-3.5 text-muted-foreground group-hover:text-accent transition-colors duration-150" strokeWidth={1.5} />
            </div>
            <span className="font-orbitron text-sm font-bold tracking-widest text-foreground">
              PR<span className="text-accent">ism</span>
              <span className="text-muted-foreground font-mono text-xs">.ai</span>
            </span>
          </Link>

          <p className="font-mono text-[11px] text-muted-foreground leading-relaxed max-w-[220px]">
            // Multi-agent orchestrator for automated code analysis, architectural conformity, and repo triage.
          </p>

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-neon-pulse" />
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Systems Nominal
            </span>
          </div>
        </div>

        {/* ── Platform links ── */}
        <div>
          <h4 className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent mb-5">
            // Platform
          </h4>
          <ul className="flex flex-col gap-3">
            {[
              { label: "Repository Analyzer", href: "/repos" },
              { label: "Analysis History",    href: "/history" },
              { label: "About Us",            href: "/#about" },
            ].map((item) => (
              <li key={item.label}>
                <Link
                  href={item.href}
                  className="font-mono text-xs text-muted-foreground hover:text-accent transition-colors duration-150 group flex items-center gap-1.5"
                >
                  <span className="opacity-0 group-hover:opacity-100 text-accent transition-opacity">›</span>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* ── Legal links ── */}
        <div>
          <h4 className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent mb-5">
            // Legal
          </h4>
          <ul className="flex flex-col gap-3">
            {[
              "Terms of Service",
              "Privacy Policy",
              "Security Standards",
            ].map((label) => (
              <li key={label}>
                <a
                  href="#"
                  className="font-mono text-xs text-muted-foreground hover:text-accent transition-colors duration-150 group flex items-center gap-1.5"
                >
                  <span className="opacity-0 group-hover:opacity-100 text-accent transition-opacity">›</span>
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </div>

        {/* ── Community / socials ── */}
        <div>
          <h4 className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent mb-5">
            // Community
          </h4>
          <div className="flex items-center gap-2.5">
            {[
              { Icon: Github,   href: "https://github.com",   label: "GitHub" },
              { Icon: Twitter,  href: "https://twitter.com",  label: "Twitter" },
              { Icon: Linkedin, href: "https://linkedin.com", label: "LinkedIn" },
            ].map(({ Icon, href, label }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noreferrer"
                aria-label={label}
                className="w-8 h-8 cyber-chamfer-sm border border-border bg-card flex items-center justify-center text-muted-foreground hover:border-accent hover:text-accent hover:shadow-neon-sm transition-all duration-150"
              >
                <Icon className="w-3.5 h-3.5" strokeWidth={1.5} />
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* ── Bottom bar ── */}
      <div className="max-w-7xl mx-auto px-6 pb-8 border-t border-border/50 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
        <span className="font-mono text-[10px] text-muted-foreground tracking-widest uppercase">
          &copy; {year} PRism AI — All rights reserved
        </span>
        <div className="flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground/50 tracking-widest uppercase">
          <Shield className="w-3 h-3" strokeWidth={1.5} />
          <span>AES-256 Encrypted Transmission</span>
        </div>
      </div>
    </footer>
  );
}
