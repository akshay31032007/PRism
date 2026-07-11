"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useSupabase } from "@/components/SessionProvider";
import { motion, AnimatePresence } from "framer-motion";
import {
  GitBranch, GitPullRequest, ChevronRight, RefreshCw,
  AlertTriangle, CheckCircle2, ShieldAlert, Zap,
  Lock, Layout, TestTube2, Star, ArrowLeft,
  ExternalLink, Clock, Circle,
} from "lucide-react";
import CTAButton from "@/components/CTAButton";

// ── Types ─────────────────────────────────────────────────────────────────────

interface GHRepo {
  id: number;
  full_name: string;
  name: string;
  owner: { login: string; avatar_url: string };
  description: string | null;
  private: boolean;
  language: string | null;
  stargazers_count: number;
  open_issues_count: number;
  updated_at: string;
  html_url: string;
}

interface GHPR {
  number: number;
  title: string;
  user: { login: string; avatar_url: string };
  state: string;
  draft: boolean;
  html_url: string;
  created_at: string;
  updated_at: string;
  body: string | null;
  head: { ref: string };
  base: { ref: string };
  labels: { name: string; color: string }[];
}

interface AgentSummary {
  agent_name: string;
  status: string;
  score: number;
  confidence: number;
  issue_count: number;
  blocking: number;
  summary: string;
  recommendations: string[];
}

interface AnalysisResult {
  analysis_id: string;
  verdict: "READY_TO_MERGE" | "CAUTION" | "BLOCKED";
  confidence_score: number;
  overall_risk_score: number;
  primary_reasoning: string;
  executive_summary: string | null;
  strengths: string[];
  weaknesses: string[];
  risks: string[];
  blocking_issues: string[];
  review_order: string[];
  agent_summaries: AgentSummary[];
  final_report: string | null;
  total_tokens: number;
  latency_seconds: number;
  analysed_at: string;
}

type View = "repos" | "prs" | "analysis";

// ── Verdict config ────────────────────────────────────────────────────────────

const verdictConfig = {
  READY_TO_MERGE: {
    label: "READY TO MERGE", icon: CheckCircle2,
    color: "text-accent", border: "border-accent/40",
    bg: "bg-accent/5", shadow: "shadow-neon",
  },
  BLOCKED: {
    label: "BLOCKED", icon: ShieldAlert,
    color: "text-destructive", border: "border-destructive/40",
    bg: "bg-destructive/5", shadow: "shadow-neon-destructive",
  },
  CAUTION: {
    label: "CAUTION ADVISED", icon: AlertTriangle,
    color: "text-yellow-400", border: "border-yellow-500/40",
    bg: "bg-yellow-500/5", shadow: "[box-shadow:0_0_5px_#facc15,0_0_20px_#facc1560]",
  },
};

const agentIcons: Record<string, React.ElementType> = {
  SecurityAgent:      Lock,
  ArchitectureAgent:  Layout,
  TestingAgent:       TestTube2,
  CodeQualityAgent:   CheckCircle2,
  DocumentationAgent: GitBranch,
  PerformanceAgent:   Zap,
  DependencyAgent:    ShieldAlert,
};

const loadingLines = [
  "$ initializing orchestrator...",
  "> fetching github diff arrays...",
  "> spawning security_agent...",
  "> spawning architecture_agent...",
  "> spawning testing_agent...",
  "> spawning code_quality_agent...",
  "> running multi-agent debate...",
  "> synthesising final verdict...",
  "$ compiling report...",
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function timeAgo(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60)    return `${diff}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

// ── Main page component ───────────────────────────────────────────────────────

export default function ReposPage() {
  const { session } = useSupabase();
  const accessToken = session?.provider_token;

  const [view,          setView]          = useState<View>("repos");
  const [repos,         setRepos]         = useState<GHRepo[]>([]);
  const [prs,           setPrs]           = useState<GHPR[]>([]);
  const [selectedRepo,  setSelectedRepo]  = useState<GHRepo | null>(null);
  const [selectedPR,    setSelectedPR]    = useState<GHPR | null>(null);
  const [analysis,      setAnalysis]      = useState<AnalysisResult | null>(null);
  const [loadingRepos,  setLoadingRepos]  = useState(false);
  const [loadingPRs,    setLoadingPRs]    = useState(false);
  const [analyzing,     setAnalyzing]     = useState(false);
  const [loadingLine,   setLoadingLine]   = useState(0);
  const [error,         setError]         = useState<string | null>(null);

  // ── Tick loading terminal lines while analyzing ───────────────────────────
  useEffect(() => {
    if (!analyzing) { setLoadingLine(0); return; }
    const iv = setInterval(() => {
      setLoadingLine(l => Math.min(l + 1, loadingLines.length - 1));
    }, 320);
    return () => clearInterval(iv);
  }, [analyzing]);

  // ── Fetch repos on mount ──────────────────────────────────────────────────
  const fetchRepos = useCallback(async () => {
    if (!accessToken) return;
    setLoadingRepos(true);
    setError(null);
    try {
      const res = await fetch(
        "https://api.github.com/user/repos?sort=updated&per_page=50&affiliation=owner,collaborator",
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!res.ok) throw new Error(`GitHub API ${res.status}`);
      const data: GHRepo[] = await res.json();
      setRepos(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load repositories.");
    } finally {
      setLoadingRepos(false);
    }
  }, [accessToken]);

  useEffect(() => { fetchRepos(); }, [fetchRepos]);

  // ── Fetch open PRs for a repo ─────────────────────────────────────────────
  const openRepo = async (repo: GHRepo) => {
    setSelectedRepo(repo);
    setView("prs");
    setLoadingPRs(true);
    setError(null);
    setPrs([]);
    try {
      const res = await fetch(
        `https://api.github.com/repos/${repo.full_name}/pulls?state=open&per_page=30`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!res.ok) throw new Error(`GitHub API ${res.status}`);
      const data: GHPR[] = await res.json();
      setPrs(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load pull requests.");
    } finally {
      setLoadingPRs(false);
    }
  };

  // ── Run analysis ──────────────────────────────────────────────────────────
  const runAnalysis = async (pr: GHPR) => {
    if (!selectedRepo) return;
    setSelectedPR(pr);
    setView("analysis");
    setAnalyzing(true);
    setAnalysis(null);
    setError(null);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pr_url: pr.html_url, enable_rag: false, skip_indexing: true }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Analysis API returned ${res.status}`);
      }
      const result: AnalysisResult = await res.json();
      setAnalysis(result);
      // Save to localStorage history
      const { saveToHistory } = await import("@/lib/historyStore");
      await saveToHistory({
        analysis_id:     result.analysis_id,
        pr_url:          pr.html_url,
        pr_title:        pr.title,
        repo:            selectedRepo?.full_name ?? "",
        verdict:         result.verdict,
        confidence:      result.confidence_score,
        latency_seconds: result.latency_seconds,
        analysed_at:     result.analysed_at,
        agent_count:     result.agent_summaries.length,
        blocking_issues: result.blocking_issues.length,
      });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-7xl mx-auto px-6 py-12 w-full flex-grow flex flex-col gap-8 relative z-10">

      {/* ── Page header with breadcrumb ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mb-2">
            <span className="text-accent">// Analyzer Deck</span>
            {selectedRepo && (
              <><ChevronRight className="w-3 h-3" /><span className="text-foreground">{selectedRepo.name}</span></>
            )}
            {selectedPR && (
              <><ChevronRight className="w-3 h-3" /><span className="text-foreground">PR #{selectedPR.number}</span></>
            )}
          </div>
          <h1 className="font-orbitron text-3xl sm:text-4xl font-bold uppercase tracking-wider text-foreground">
            {view === "repos" && "Your Repositories"}
            {view === "prs"   && selectedRepo?.name}
            {view === "analysis" && "Analysis Report"}
          </h1>
        </div>

        {view !== "repos" && (
          <button
            onClick={() => {
              if (view === "analysis") { setView("prs"); setAnalysis(null); }
              else { setView("repos"); setSelectedRepo(null); setPrs([]); }
            }}
            className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.15em] text-muted-foreground hover:text-accent transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back
          </button>
        )}
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div className="cyber-chamfer-sm border border-destructive/40 bg-destructive/10 px-4 py-3 flex items-start gap-2.5">
          <AlertTriangle className="w-3.5 h-3.5 text-destructive shrink-0 mt-0.5" strokeWidth={1.5} />
          <span className="font-mono text-[11px] text-destructive">// ERROR: {error}</span>
        </div>
      )}

      <AnimatePresence mode="wait">

        {/* ════════ VIEW: REPOS ════════ */}
        {view === "repos" && (
          <motion.div key="repos" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {loadingRepos ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-32 cyber-chamfer bg-card border border-border animate-pulse" />
                ))}
              </div>
            ) : repos.length === 0 ? (
              <div className="text-center py-20 font-mono text-sm text-muted-foreground">
                No repositories found.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {repos.map(repo => (
                  <motion.button
                    key={repo.id}
                    onClick={() => openRepo(repo)}
                    whileHover={{ y: -3 }}
                    className="group text-left border border-border cyber-chamfer bg-card p-5 flex flex-col gap-3 hover:border-accent hover:shadow-neon transition-all duration-150"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-orbitron text-xs font-bold uppercase tracking-wider text-foreground group-hover:text-accent transition-colors truncate">
                          {repo.name}
                        </div>
                        <div className="font-mono text-[10px] text-muted-foreground/60 mt-0.5">{repo.owner.login}</div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        {repo.private && (
                          <span className="font-mono text-[9px] uppercase tracking-widest border border-border px-1.5 py-0.5 text-muted-foreground">
                            Private
                          </span>
                        )}
                        <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-accent transition-colors" strokeWidth={1.5} />
                      </div>
                    </div>
                    {repo.description && (
                      <p className="font-mono text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">{repo.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-auto font-mono text-[10px] text-muted-foreground/60">
                      {repo.language && <span className="flex items-center gap-1"><Circle className="w-2 h-2 fill-accent text-accent" />{repo.language}</span>}
                      <span className="flex items-center gap-1"><Star className="w-3 h-3" strokeWidth={1.5} />{repo.stargazers_count}</span>
                      <span className="flex items-center gap-1"><GitPullRequest className="w-3 h-3" strokeWidth={1.5} />{repo.open_issues_count} open</span>
                    </div>
                  </motion.button>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* ════════ VIEW: PRs ════════ */}
        {view === "prs" && (
          <motion.div key="prs" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-3">
            {loadingPRs ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-20 cyber-chamfer bg-card border border-border animate-pulse" />
              ))
            ) : prs.length === 0 ? (
              <div className="text-center py-20 border border-border cyber-chamfer bg-card">
                <GitPullRequest className="w-8 h-8 text-muted-foreground/30 mx-auto mb-3" strokeWidth={1.5} />
                <p className="font-mono text-xs text-muted-foreground">No open pull requests in this repository.</p>
              </div>
            ) : prs.map(pr => (
              <motion.div
                key={pr.number}
                whileHover={{ x: 2 }}
                className="group border border-border cyber-chamfer bg-card p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-accent hover:shadow-neon-sm transition-all duration-150"
              >
                <div className="flex flex-col gap-1.5 flex-grow min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-[10px] text-accent">#{pr.number}</span>
                    {pr.draft && (
                      <span className="font-mono text-[9px] uppercase tracking-widest border border-border px-1.5 py-0.5 text-muted-foreground">Draft</span>
                    )}
                    {pr.labels.slice(0, 3).map(l => (
                      <span key={l.name} className="font-mono text-[9px] px-1.5 py-0.5 border" style={{ borderColor: `#${l.color}40`, color: `#${l.color}`, background: `#${l.color}15` }}>{l.name}</span>
                    ))}
                  </div>
                  <div className="font-orbitron text-sm font-bold uppercase tracking-wide text-foreground group-hover:text-accent transition-colors truncate">
                    {pr.title}
                  </div>
                  <div className="flex items-center gap-4 font-mono text-[10px] text-muted-foreground/60">
                    <span>{pr.user.login}</span>
                    <span className="flex items-center gap-1"><GitBranch className="w-3 h-3" strokeWidth={1.5} />{pr.head.ref} → {pr.base.ref}</span>
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" strokeWidth={1.5} />{timeAgo(pr.updated_at)}</span>
                    <a href={pr.html_url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                      className="flex items-center gap-1 hover:text-accent transition-colors">
                      <ExternalLink className="w-3 h-3" strokeWidth={1.5} />GitHub
                    </a>
                  </div>
                </div>
                <CTAButton variant="glitch" onClick={() => runAnalysis(pr)} className="shrink-0 py-2.5 px-6 text-[11px]">
                  <Zap className="w-3 h-3" strokeWidth={1.5} />
                  Start Analysis
                </CTAButton>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* ════════ VIEW: ANALYSIS ════════ */}
        {view === "analysis" && (
          <motion.div key="analysis" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-6">

            {/* Loading terminal */}
            {analyzing && (
              <div className="border border-accent/30 cyber-chamfer bg-card overflow-hidden shadow-neon-sm">
                <div className="flex items-center gap-2 px-5 h-8 bg-muted border-b border-border">
                  <span className="w-2 h-2 rounded-full bg-destructive opacity-70" />
                  <span className="w-2 h-2 rounded-full bg-yellow-500 opacity-70" />
                  <span className="w-2 h-2 rounded-full bg-accent animate-neon-pulse" />
                  <span className="ml-auto font-mono text-[10px] text-accent tracking-widest">processing...</span>
                </div>
                <div className="p-6 flex flex-col gap-1.5">
                  {loadingLines.slice(0, loadingLine + 1).map((line, i) => (
                    <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                      className="flex items-center gap-2 font-mono text-xs">
                      <span className={line.startsWith("$") ? "text-accent" : "text-muted-foreground"}>{line}</span>
                      {i === loadingLine && <span className="inline-block w-1.5 h-3 bg-accent animate-blink" />}
                    </motion.div>
                  ))}
                </div>
                <div className="h-1 w-full bg-border overflow-hidden">
                  <motion.div className="h-full bg-accent shadow-neon-sm" initial={{ width: "0%" }}
                    animate={{ width: "100%" }} transition={{ duration: 35, ease: "linear" }} />
                </div>
              </div>
            )}

            {/* Results */}
            {analysis && !analyzing && (() => {
              const cfg = verdictConfig[analysis.verdict];
              const VIcon = cfg.icon;
              return (
                <>
                  {/* Verdict banner */}
                  <div className={`border ${cfg.border} ${cfg.bg} ${cfg.shadow} cyber-chamfer overflow-hidden`}>
                    <div className="flex items-center gap-2 px-5 h-8 bg-muted/60 border-b border-border/60">
                      <span className="w-2 h-2 rounded-full bg-destructive opacity-70" />
                      <span className="w-2 h-2 rounded-full bg-yellow-500 opacity-70" />
                      <span className={`w-2 h-2 rounded-full ${analysis.verdict === "READY_TO_MERGE" ? "bg-accent" : analysis.verdict === "BLOCKED" ? "bg-destructive" : "bg-yellow-400"}`} />
                      <span className="ml-auto font-mono text-[10px] text-muted-foreground tracking-widest">orchestrator.verdict</span>
                    </div>
                    <div className="p-6 md:p-8 flex flex-col md:flex-row items-start gap-6 justify-between">
                      <div className="flex items-start gap-4 flex-grow">
                        <VIcon className={`w-7 h-7 mt-0.5 shrink-0 ${cfg.color}`} strokeWidth={1.5} />
                        <div>
                          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">// Orchestration Verdict</span>
                          <h3 className={`font-orbitron text-xl sm:text-2xl font-black uppercase tracking-wider mt-1 mb-3 ${cfg.color}`}>
                            {cfg.label}
                          </h3>
                          <p className="font-mono text-xs text-muted-foreground leading-relaxed max-w-2xl">{analysis.primary_reasoning}</p>
                        </div>
                      </div>
                      {/* Confidence dial */}
                      <div className="flex flex-col items-center gap-2 shrink-0">
                        <div className="relative w-20 h-20">
                          <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                            <path stroke="#2a2a3a" strokeWidth="2.5" fill="none" d="M18 2.0845 a15.9155 15.9155 0 0 1 0 31.831 a15.9155 15.9155 0 0 1 0 -31.831" />
                            <path className={cfg.color} strokeWidth="2.5" strokeDasharray={`${Math.round(analysis.confidence_score * 100)}, 100`}
                              strokeLinecap="round" stroke="currentColor" fill="none" d="M18 2.0845 a15.9155 15.9155 0 0 1 0 31.831 a15.9155 15.9155 0 0 1 0 -31.831" />
                          </svg>
                          <span className={`absolute inset-0 flex items-center justify-center font-orbitron text-sm font-black ${cfg.color}`}>
                            {Math.round(analysis.confidence_score * 100)}%
                          </span>
                        </div>
                        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Confidence</span>
                      </div>
                    </div>

                    {/* Strengths / Weaknesses / Risks */}
                    {(analysis.strengths.length > 0 || analysis.weaknesses.length > 0 || analysis.risks.length > 0) && (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-border border-t border-border">
                        {[
                          { label: "Strengths",  items: analysis.strengths,  color: "text-accent" },
                          { label: "Weaknesses", items: analysis.weaknesses, color: "text-yellow-400" },
                          { label: "Risks",      items: analysis.risks,      color: "text-destructive" },
                        ].map(({ label, items, color }) => (
                          <div key={label} className="bg-card p-5">
                            <div className={`font-mono text-[10px] uppercase tracking-[0.2em] mb-3 ${color}`}>// {label}</div>
                            <ul className="flex flex-col gap-2">
                              {items.slice(0, 4).map((item, i) => (
                                <li key={i} className="flex items-start gap-2 font-mono text-[11px] text-muted-foreground leading-relaxed">
                                  <span className={`mt-0.5 shrink-0 ${color}`}>›</span>{item}
                                </li>
                              ))}
                              {items.length === 0 && <li className="font-mono text-[11px] text-muted-foreground/40">None detected.</li>}
                            </ul>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Blocking issues */}
                  {analysis.blocking_issues.length > 0 && (
                    <div className="cyber-chamfer border border-destructive/40 bg-destructive/5 p-5">
                      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-destructive mb-3">// Blocking Issues — Must Fix Before Merge</div>
                      <ul className="flex flex-col gap-2">
                        {analysis.blocking_issues.map((issue, i) => (
                          <li key={i} className="flex items-start gap-2 font-mono text-xs text-destructive/80 leading-relaxed">
                            <ShieldAlert className="w-3.5 h-3.5 shrink-0 mt-0.5" strokeWidth={1.5} />{issue}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Agent cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-border cyber-chamfer overflow-hidden">
                    {analysis.agent_summaries.map(agent => {
                      const Icon = agentIcons[agent.agent_name] ?? Zap;
                      const pct  = Math.round(agent.score * 100);
                      return (
                        <div key={agent.agent_name} className="bg-card p-5 flex flex-col gap-4 group hover:bg-muted/40 transition-colors">
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 cyber-chamfer-sm border border-border bg-background flex items-center justify-center group-hover:border-accent group-hover:shadow-neon-sm transition-all duration-150">
                              <Icon className="w-3.5 h-3.5 text-muted-foreground group-hover:text-accent transition-colors" strokeWidth={1.5} />
                            </div>
                            <div>
                              <div className="font-orbitron text-[11px] font-bold uppercase tracking-wider text-foreground">
                                {agent.agent_name.replace("Agent", "")}
                              </div>
                              <div className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground/60">
                                {agent.issue_count} issues · {agent.blocking} blocking
                              </div>
                            </div>
                            <span className={`ml-auto font-orbitron text-sm font-black ${pct >= 80 ? "text-accent" : pct >= 50 ? "text-yellow-400" : "text-destructive"}`}>
                              {pct}%
                            </span>
                          </div>
                          <p className="font-mono text-[11px] text-muted-foreground leading-relaxed flex-grow">{agent.summary}</p>
                          {agent.recommendations.length > 0 && (
                            <ul className="flex flex-col gap-1.5 border-t border-border pt-3">
                              {agent.recommendations.slice(0, 3).map((rec, i) => (
                                <li key={i} className="flex items-start gap-1.5 font-mono text-[10px] text-muted-foreground/70 leading-relaxed">
                                  <span className="text-accent mt-0.5 shrink-0">›</span>{rec}
                                </li>
                              ))}
                            </ul>
                          )}
                          <div className="h-px w-full bg-border overflow-hidden">
                            <motion.div
                              className={`h-full ${pct >= 80 ? "bg-accent" : pct >= 50 ? "bg-yellow-400" : "bg-destructive"}`}
                              initial={{ width: "0%" }} animate={{ width: `${pct}%` }}
                              transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Full report */}
                  {analysis.final_report && (
                    <div className="border border-border cyber-chamfer bg-card overflow-hidden">
                      <div className="flex items-center gap-2 px-5 h-8 bg-muted border-b border-border">
                        <span className="w-2 h-2 rounded-full bg-destructive opacity-70" />
                        <span className="w-2 h-2 rounded-full bg-yellow-500 opacity-70" />
                        <span className="w-2 h-2 rounded-full bg-accent opacity-70" />
                        <span className="ml-auto font-mono text-[10px] text-muted-foreground tracking-widest">full_report.md</span>
                      </div>
                      <pre className="p-6 font-mono text-[11px] text-muted-foreground leading-relaxed whitespace-pre-wrap overflow-x-auto max-h-[600px] overflow-y-auto">
                        {analysis.final_report}
                      </pre>
                    </div>
                  )}

                  {/* Footer */}
                  <div className="cyber-chamfer-sm border border-border bg-card px-5 py-3 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground/60">
                    <span>Tokens used: {analysis.total_tokens.toLocaleString()}</span>
                    <span>Latency: {analysis.latency_seconds}s</span>
                    <span>ID: {analysis.analysis_id}</span>
                  </div>
                </>
              );
            })()}
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
