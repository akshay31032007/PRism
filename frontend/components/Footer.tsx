import React from "react";
import Link from "next/link";
import { Cpu, Github, Twitter, Linkedin, Shield } from "lucide-react";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-zinc-900 bg-zinc-950 py-12 px-6 relative z-10">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-10">
        
        {/* BRAND COLUMN */}
        <div className="flex flex-col gap-4">
          <Link href="/" className="flex items-center gap-2 group focus-visible:outline-none">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center">
              <Cpu className="w-4 h-4 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
            </div>
            <span className="font-outfit text-lg font-bold tracking-wider text-zinc-200">
              PRism<span className="text-zinc-500">.ai</span>
            </span>
          </Link>
          <p className="text-xs text-zinc-500 max-w-xs leading-relaxed">
            Multi-agent orchestrator for automated code analysis, architectural conformity, and repository triage.
          </p>
        </div>

        {/* NAVIGATION COLUMN */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">Platform</h4>
          <ul className="flex flex-col gap-2.5 text-xs text-zinc-500 font-medium">
            <li>
              <Link href="/repos" className="hover:text-zinc-350 transition-colors">
                Repository Analyzer
              </Link>
            </li>
            <li>
              <Link href="/history" className="hover:text-zinc-350 transition-colors">
                Analysis History
              </Link>
            </li>
            <li>
              <Link href="/#about" className="hover:text-zinc-350 transition-colors">
                About Us
              </Link>
            </li>
          </ul>
        </div>

        {/* LEGAL COLUMN */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">Legal</h4>
          <ul className="flex flex-col gap-2.5 text-xs text-zinc-500 font-medium">
            <li>
              <a href="#" className="hover:text-zinc-350 transition-colors">Terms of Service</a>
            </li>
            <li>
              <a href="#" className="hover:text-zinc-350 transition-colors">Privacy Policy</a>
            </li>
            <li>
              <a href="#" className="hover:text-zinc-350 transition-colors">Security Standards</a>
            </li>
          </ul>
        </div>

        {/* SOCIALS COLUMN */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">Community</h4>
          <div className="flex items-center gap-3">
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-150 hover:bg-zinc-850 hover:border-zinc-700 transition-colors"
              aria-label="GitHub Profile"
            >
              <Github className="w-4 h-4" />
            </a>
            <a
              href="https://twitter.com"
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-150 hover:bg-zinc-850 hover:border-zinc-700 transition-colors"
              aria-label="Twitter Profile"
            >
              <Twitter className="w-4 h-4" />
            </a>
            <a
              href="https://linkedin.com"
              target="_blank"
              rel="noreferrer"
              className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-150 hover:bg-zinc-850 hover:border-zinc-700 transition-colors"
              aria-label="LinkedIn Profile"
            >
              <Linkedin className="w-4 h-4" />
            </a>
          </div>
        </div>

      </div>

      <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-zinc-900 flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] text-zinc-650 tracking-wider">
        <div>
          &copy; {currentYear} PRism AI. All rights reserved.
        </div>
        <div className="flex items-center gap-1.5 text-zinc-700">
          <Shield className="w-3.5 h-3.5" />
          <span>AES-256 Mock Encrypted Transmission</span>
        </div>
      </div>
    </footer>
  );
}
