"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Search,
  Sparkles,
  Cpu,
  RefreshCw,
  FileCode2,
  Flame,
  Layout,
  TestTube2,
  Lock,
  ArrowRight,
  GitBranch,
} from "lucide-react";
import InputField from "@/components/InputField";
import CTAButton from "@/components/CTAButton";

type VerdictType = "READY_TO_MERGE" | "BLOCKED" | "CAUTION";

interface MockReport {
  verdict: VerdictType;
  confidence: number;
  reasoning: string;
  security: string;
  architecture: string;
  testing: string;
}

const mockReports: Record<string, MockReport> = {
  safe: {
    verdict: "READY_TO_MERGE",
    confidence: 98,
    reasoning: "Clean, well-bounded diff. Standard dependency patch. Fully compliant with system architectural guidelines. 100% test coverage appended for all updated utilities.",
    security: "Zero secrets leakage detected in commit strings. NPM audit reports no vulnerabilities introduced. Diffs are confined to standard dependency updates.",
    architecture: "Follows modular design guidelines. Code duplication factor is 0%. Dependency decoupling matches repository structure patterns.",
    testing: "Unit tests successfully written for modified helpers. All remote CI check-runs passed. Code coverage level remains stable at 94.2%.",
  },
  compromised: {
    verdict: "BLOCKED",
    confidence: 34,
    reasoning: "Critical security alert. Active SQL injection path detected in database module. Core integration tests failing on remote build. Significant test coverage drop.",
    security: "CRITICAL: Hardcoded AWS API token discovered in config.ts. Plain text SQL string concatenation used in database query executor, bypassing ORM sanitization.",
    architecture: "Violates clean routing pattern. Controller handles DB writes directly instead of delegating to repository services. High coupling risk detected.",
    testing: "Code coverage dropped by 14.5% in the modified files. Core integration tests failed in branch build (CI status: Error). No assertions found in test files.",
  },
  custom: {
    verdict: "CAUTION",
    confidence: 72,
    reasoning: "Minor quality flags detected. Patch functions correctly but contains refactoring issues. All security metrics passed. No failing integration tests.",
    security: "No secrets or vulnerability warnings discovered. Dependency checks passed cleanly.",
    architecture: "Minor complexity warning: executeTransaction exceeds 45 lines. Consider breaking this method down into smaller helper utilities.",
    testing: "Mock tests ran successfully. Coverage for new routes is at 60%, below the recommended project baseline of 80%.",
  },
};

export default function ReposPage() {
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");
  const [report, setReport] = useState<MockReport | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<"safe" | "compromised" | "custom" | null>(null);

  // Loading text rotation effect
  useEffect(() => {
    if (!loading) return;

    const texts = [
      "Scraping GitHub diff arrays...",
      "Orchestrating agent debate engine...",
      "Generating final structured verdict...",
    ];

    setLoadingText(texts[0]);
    
    const t1 = setTimeout(() => setLoadingText(texts[1]), 700);
    const t2 = setTimeout(() => setLoadingText(texts[2]), 1400);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [loading]);

  const handlePresetSelect = (preset: "safe" | "compromised") => {
    setSelectedPreset(preset);
    if (preset === "safe") {
      setRepoUrl("https://github.com/facebook/react/pull/28490");
    } else {
      setRepoUrl("https://github.com/compromised/repo/pull/666");
    }
  };

  const handleAnalyze = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!repoUrl.trim()) return;

    setLoading(true);
    setReport(null);

    // Simulate 2 seconds of orchestrator processing
    setTimeout(() => {
      setLoading(false);
      if (selectedPreset === "safe") {
        setReport(mockReports.safe);
      } else if (selectedPreset === "compromised") {
        setReport(mockReports.compromised);
      } else {
        // If they type their own, assign custom
        setReport(mockReports.custom);
      }
    }, 2100);
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 w-full flex-grow flex flex-col gap-12 relative z-10">
      
      {/* HEADER SECTION */}
      <div>
        <span className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Analyzer Deck</span>
        <h1 className="font-outfit text-3xl sm:text-4xl font-bold tracking-tight text-zinc-200 mt-2">
          Repository Inspection Tower
        </h1>
        <p className="font-sans text-sm text-zinc-550 mt-2 max-w-xl">
          Enter a GitHub PR link or select a quick preset to launch our specialized debate agents.
        </p>
      </div>

      {/* INPUT / CONTROL BLOCK */}
      <div className="bg-zinc-900/10 border border-zinc-900 rounded-3xl p-6 md:p-8 backdrop-blur-sm">
        <form onSubmit={handleAnalyze} className="flex flex-col md:flex-row gap-4 items-center">
          <InputField
            id="repo-input"
            icon={Search}
            placeholder="Paste the GitHub Repository URL here..."
            value={repoUrl}
            onChange={(e) => {
              setRepoUrl(e.target.value);
              setSelectedPreset(null); // Reset preset on custom typing
            }}
            disabled={loading}
            containerClassName="flex-grow"
          />
          <CTAButton
            type="submit"
            variant="primary"
            disabled={loading || !repoUrl.trim()}
            className="w-full md:w-auto h-[48px] px-8"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-zinc-950" />
                Analyzing...
              </span>
            ) : (
              "Analyze Repository"
            )}
          </CTAButton>
        </form>

        {/* DEMO CHIPS (PHASE 5 REQUIREMENT) */}
        <div className="flex flex-wrap items-center gap-3 mt-5">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-600">Quick Anchors:</span>
          <button
            onClick={() => handlePresetSelect("safe")}
            disabled={loading}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
              selectedPreset === "safe"
                ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-350 shadow-sm"
                : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
            }`}
          >
            ⚡ Try Safe Hotfix PR
          </button>
          <button
            onClick={() => handlePresetSelect("compromised")}
            disabled={loading}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
              selectedPreset === "compromised"
                ? "bg-red-950/40 border-red-500/50 text-red-350 shadow-sm"
                : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
            }`}
          >
            ⚡ Try Compromised Query PR
          </button>
        </div>
      </div>

      {/* INTERACTIVE LOAD STATE */}
      <AnimatePresence mode="wait">
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            className="flex flex-col items-center justify-center py-20 text-center gap-4 bg-zinc-900/5 border border-zinc-900/60 rounded-3xl backdrop-blur-sm"
          >
            <div className="relative flex items-center justify-center">
              <div className="w-16 h-16 rounded-full border-2 border-zinc-800 border-t-zinc-450 animate-spin" />
              <Cpu className="w-6 h-6 text-zinc-500 absolute animate-pulse" />
            </div>
            <div className="flex flex-col gap-1.5 mt-2">
              <span className="font-outfit text-sm font-semibold tracking-wider text-zinc-350">
                Orchestrator Processing
              </span>
              <p className="font-sans text-xs text-zinc-550 animate-pulse min-w-[260px]">
                {loadingText}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* MOCK RESULTS VIEW */}
      <AnimatePresence>
        {report && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="flex flex-col gap-8"
          >
            
            {/* PRIMARY VERDICT BANNER (PHASE 3 REQUIREMENT) */}
            <div
              className={`border rounded-3xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 backdrop-blur-sm transition-all shadow-lg ${
                report.verdict === "READY_TO_MERGE"
                  ? "border-emerald-900/40 bg-emerald-950/10 shadow-emerald-950/5"
                  : report.verdict === "BLOCKED"
                  ? "border-red-900/40 bg-red-950/10 shadow-red-950/5"
                  : "border-amber-900/40 bg-amber-950/10 shadow-amber-950/5"
              }`}
            >
              <div className="flex items-start gap-4 flex-grow max-w-3xl">
                <div className="mt-1">
                  {report.verdict === "READY_TO_MERGE" ? (
                    <CheckCircle2 className="w-7 h-7 text-emerald-450" />
                  ) : report.verdict === "BLOCKED" ? (
                    <ShieldAlert className="w-7 h-7 text-red-450" />
                  ) : (
                    <AlertTriangle className="w-7 h-7 text-amber-450" />
                  )}
                </div>
                <div className="flex flex-col gap-2">
                  <span className="font-outfit text-xs font-semibold uppercase tracking-widest text-zinc-550">
                    Orchestration Verdict
                  </span>
                  <h3 className="font-outfit text-xl font-bold tracking-tight text-zinc-200">
                    {report.verdict === "READY_TO_MERGE"
                      ? "READY TO MERGE"
                      : report.verdict === "BLOCKED"
                      ? "BLOCKED"
                      : "CAUTION ADVISED"}
                  </h3>
                  <p className="font-sans text-sm text-zinc-500 leading-relaxed mt-1">
                    {report.reasoning}
                  </p>
                </div>
              </div>

              {/* DIAL CONFIGURATION */}
              <div className="flex flex-col items-center gap-1.5 self-center min-w-[120px]">
                <div className="relative flex items-center justify-center w-20 h-20">
                  <svg className="w-full h-full transform -rotate-95" viewBox="0 0 36 36">
                    <path
                      className="text-zinc-900"
                      strokeWidth="2.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className={
                        report.verdict === "READY_TO_MERGE"
                          ? "text-emerald-500"
                          : report.verdict === "BLOCKED"
                          ? "text-red-500"
                          : "text-amber-500"
                      }
                      strokeWidth="2.5"
                      strokeDasharray={`${report.confidence}, 100`}
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <span className="absolute font-outfit text-md font-bold text-zinc-200">
                    {report.confidence}%
                  </span>
                </div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-550">
                  Confidence
                </span>
              </div>
            </div>

            {/* THREE-COLUMN RESPONSIVE GRID (PHASE 3 REQUIREMENT) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* SECURITY CARD */}
              <div className="rounded-2xl border border-zinc-900 bg-zinc-950/40 p-6 md:p-8 backdrop-blur-sm hover:border-zinc-800 transition-all flex flex-col justify-between shadow-sm">
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-850 flex items-center justify-center">
                      <Lock className="w-4 h-4 text-zinc-400" />
                    </div>
                    <div>
                      <h4 className="font-outfit text-sm font-bold text-zinc-200">Security Agent</h4>
                      <span className="text-[10px] text-zinc-650 tracking-wide uppercase font-semibold">Triage Domain</span>
                    </div>
                  </div>
                  <p className="font-sans text-xs sm:text-sm text-zinc-500 leading-relaxed">
                    {report.security}
                  </p>
                </div>
                <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden mt-8">
                  <div
                    className={`h-full rounded-full ${
                      report.verdict === "READY_TO_MERGE"
                        ? "bg-emerald-500 w-full"
                        : report.verdict === "BLOCKED"
                        ? "bg-red-500 w-[20%]"
                        : "bg-amber-500 w-[70%]"
                    }`}
                  />
                </div>
              </div>

              {/* ARCHITECTURE CARD */}
              <div className="rounded-2xl border border-zinc-900 bg-zinc-950/40 p-6 md:p-8 backdrop-blur-sm hover:border-zinc-800 transition-all flex flex-col justify-between shadow-sm">
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-850 flex items-center justify-center">
                      <Layout className="w-4 h-4 text-zinc-400" />
                    </div>
                    <div>
                      <h4 className="font-outfit text-sm font-bold text-zinc-200">Architecture Agent</h4>
                      <span className="text-[10px] text-zinc-650 tracking-wide uppercase font-semibold">Triage Domain</span>
                    </div>
                  </div>
                  <p className="font-sans text-xs sm:text-sm text-zinc-500 leading-relaxed">
                    {report.architecture}
                  </p>
                </div>
                <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden mt-8">
                  <div
                    className={`h-full rounded-full ${
                      report.verdict === "READY_TO_MERGE"
                        ? "bg-emerald-500 w-full"
                        : report.verdict === "BLOCKED"
                        ? "bg-red-500/60 w-[40%]"
                        : "bg-amber-500 w-[80%]"
                    }`}
                  />
                </div>
              </div>

              {/* TESTING CARD */}
              <div className="rounded-2xl border border-zinc-900 bg-zinc-950/40 p-6 md:p-8 backdrop-blur-sm hover:border-zinc-800 transition-all flex flex-col justify-between shadow-sm">
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-850 flex items-center justify-center">
                      <TestTube2 className="w-4 h-4 text-zinc-400" />
                    </div>
                    <div>
                      <h4 className="font-outfit text-sm font-bold text-zinc-200">Testing Agent</h4>
                      <span className="text-[10px] text-zinc-650 tracking-wide uppercase font-semibold">Triage Domain</span>
                    </div>
                  </div>
                  <p className="font-sans text-xs sm:text-sm text-zinc-500 leading-relaxed">
                    {report.testing}
                  </p>
                </div>
                <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden mt-8">
                  <div
                    className={`h-full rounded-full ${
                      report.verdict === "READY_TO_MERGE"
                        ? "bg-emerald-500 w-full"
                        : report.verdict === "BLOCKED"
                        ? "bg-red-500/80 w-[30%]"
                        : "bg-amber-500 w-[60%]"
                    }`}
                  />
                </div>
              </div>

            </div>

            {/* INTEGRATION INFO FOOTNOTE */}
            <div className="flex items-center justify-between p-4 rounded-xl border border-zinc-900/60 bg-zinc-950/20 text-[10px] text-zinc-600 font-semibold tracking-widest uppercase">
              <span className="flex items-center gap-2">
                <GitBranch className="w-3.5 h-3.5" />
                Target Branch: main
              </span>
              <span>Integrations: GitHub Actions, CodeQL, Semgrep</span>
            </div>

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
