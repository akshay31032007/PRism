"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2, ShieldAlert, AlertTriangle,
  Clock, Zap, Trash2, ExternalLink, Database, GitPullRequest,
} from "lucide-react";
import { loadHistory, clearHistory, type HistoryEntry } from "@/lib/historyStore";
import CTAButton from "@/components/CTAButton";

const verdictConfig = {
  READY_TO_MERGE: { label: "Ready",   color: "text-accent",      border: "border-accent/30",      bg: "bg-accent/5",      icon: CheckCircle2  },
  CAUTION:        { label: "Caution", color: "text-yellow-400",  border: "border-yellow-500/30",  bg: "bg-yellow-500/5",  icon: AlertTriangle },
  BLOCKED:        { label: "Blocked", color: "text-destructive", border: "border-destructive/30", bg: "bg-destructive/5", icon: ShieldAlert   },
};

function timeAgo(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [mounted, setMounted] = useState(false);

  const refresh = () => setEntries(loadHistory());

  useEffect(() => {
    setMounted(true);
    refresh();
    // Listen for new analyses saved from repos page
    window.addEventListener("prism_history_updated", refresh);
    return () => window.removeEventListener("prism_history_updated", refresh);
  }, []);

  if (!mounted) return null;

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 w-full flex-grow flex flex-col gap-8 relative z-10">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent">
            // Analysis History
          </span>
          <h1 className="font-orbitron text-3xl sm:text-4xl font-bold uppercase tracking-wider text-foreground mt-2">
            Past Analyses
          </h1>
          <p className="font-mono text-xs text-muted-foreground mt-1">
            {entries.length} record{entries.length !== 1 ? "s" : ""} stored locally
          </p>
        </div>

        {entries.length > 0 && (
          <button
            onClick={() => { clearHistory(); refresh(); }}
            className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.15em] text-muted-foreground hover:text-destructive transition-colors duration-150"
          >
            <Trash2 className="w-3.5 h-3.5" strokeWidth={1.5} />
            Clear All
          </button>
        )}
      </div>

      {/* ── Empty state ── */}
      {entries.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-8 py-16"
        >
          <div className="border border-border cyber-chamfer bg-card overflow-hidden w-full max-w-lg">
            <div className="flex items-center gap-2 px-5 h-8 bg-muted border-b border-border">
              <span className="w-2 h-2 rounded-full bg-destructive opacity-70" />
              <span className="w-2 h-2 rounded-full bg-yellow-500 opacity-70" />
              <span className="w-2 h-2 rounded-full bg-border" />
              <span className="ml-auto font-mono text-[10px] text-muted-foreground tracking-widest">history.log</span>
            </div>
            <div className="p-6 space-y-1.5">
              {[
                { p: "$", t: "query analysis_history --limit=50" },
                { p: ">", t: "connecting to local store..." },
                { p: ">", t: "ERROR: no records found", c: "text-destructive" },
                { p: ">", t: "status: EMPTY_STATE", c: "text-yellow-400" },
              ].map(({ p, t, c }, i) => (
                <div key={i} className="flex gap-2 font-mono text-xs">
                  <span className="text-accent">{p}</span>
                  <span className={c ?? "text-muted-foreground"}>{t}</span>
                </div>
              ))}
              <div className="flex gap-2 font-mono text-xs">
                <span className="text-accent">$</span>
                <span className="cyber-cursor text-muted-foreground" />
              </div>
            </div>
          </div>

          <div className="flex flex-col items-center gap-2 text-center">
            <h2 className="font-orbitron text-xl font-bold uppercase tracking-wider text-foreground">
              No Analysis History
            </h2>
            <p className="font-mono text-xs text-muted-foreground max-w-xs leading-relaxed">
              Analyses you run will appear here automatically. Results are stored in your browser.
            </p>
          </div>

          <Link href="/repos" className="focus-visible:outline-none">
            <CTAButton variant="primary" showArrow className="py-3.5 px-8">
              <Zap className="w-3.5 h-3.5" strokeWidth={1.5} />
              Launch Analyzer
            </CTAButton>
          </Link>
        </motion.div>
      )}

      {/* ── History list ── */}
      <AnimatePresence>
        {entries.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col gap-3"
          >
            {entries.map((entry, idx) => {
              const cfg  = verdictConfig[entry.verdict] ?? verdictConfig.CAUTION;
              const Icon = cfg.icon;
              const conf = Math.round(entry.confidence * 100);

              return (
                <motion.div
                  key={entry.analysis_id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className={`group border ${cfg.border} ${cfg.bg} cyber-chamfer p-5 flex flex-col sm:flex-row sm:items-center gap-4 hover:shadow-neon-sm transition-all duration-150`}
                >
                  {/* Verdict icon */}
                  <div className={`w-10 h-10 cyber-chamfer-sm border ${cfg.border} bg-background flex items-center justify-center shrink-0`}>
                    <Icon className={`w-4 h-4 ${cfg.color}`} strokeWidth={1.5} />
                  </div>

                  {/* Main info */}
                  <div className="flex flex-col gap-1 flex-grow min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-mono text-[10px] uppercase tracking-widest font-bold ${cfg.color}`}>
                        {cfg.label}
                      </span>
                      <span className="font-mono text-[10px] text-muted-foreground/60">
                        {conf}% confidence
                      </span>
                      {entry.blocking_issues > 0 && (
                        <span className="font-mono text-[9px] uppercase tracking-widest border border-destructive/40 bg-destructive/10 text-destructive px-1.5 py-0.5">
                          {entry.blocking_issues} blocking
                        </span>
                      )}
                    </div>

                    <div className="font-orbitron text-sm font-bold uppercase tracking-wide text-foreground truncate">
                      {entry.pr_title}
                    </div>

                    <div className="flex items-center gap-4 font-mono text-[10px] text-muted-foreground/60 flex-wrap">
                      <span className="flex items-center gap-1">
                        <GitPullRequest className="w-3 h-3" strokeWidth={1.5} />
                        {entry.repo}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" strokeWidth={1.5} />
                        {timeAgo(entry.analysed_at)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Zap className="w-3 h-3" strokeWidth={1.5} />
                        {entry.latency_seconds}s
                      </span>
                      <span>{entry.agent_count} agents</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={entry.pr_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-accent transition-colors border border-border cyber-chamfer-sm px-3 py-2 hover:border-accent hover:shadow-neon-sm"
                    >
                      <ExternalLink className="w-3 h-3" strokeWidth={1.5} />
                      PR
                    </a>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Storage notice */}
      {entries.length > 0 && (
        <div className="cyber-chamfer-sm border border-border bg-card px-5 py-3 flex items-center gap-3">
          <Database className="w-3.5 h-3.5 text-muted-foreground/40 shrink-0" strokeWidth={1.5} />
          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground/40">
            // Stored in browser localStorage · Cleared on browser data wipe
          </span>
        </div>
      )}
    </div>
  );
}
