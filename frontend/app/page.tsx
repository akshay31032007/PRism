"use client";

import React, { useEffect, useRef } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  Layers,
  Terminal,
  ArrowRight,
  Eye,
  GitMerge,
  Zap,
  Lock,
} from "lucide-react";
import FeatureCard from "@/components/FeatureCard";
import CTAButton from "@/components/CTAButton";

/* ── Typing effect hook ── */
function useTypewriter(text: string, speed = 40, startDelay = 600) {
  const [displayed, setDisplayed] = React.useState("");
  useEffect(() => {
    let i = 0;
    const delay = setTimeout(() => {
      const interval = setInterval(() => {
        setDisplayed(text.slice(0, ++i));
        if (i >= text.length) clearInterval(interval);
      }, speed);
      return () => clearInterval(interval);
    }, startDelay);
    return () => clearTimeout(delay);
  }, [text, speed, startDelay]);
  return displayed;
}

const features = [
  {
    icon: ShieldCheck,
    title: "Security Agent",
    description:
      "Scans incoming diffs for secrets leakages, dependency vulnerabilities, and insecure coding patterns before they hit production.",
    terminalId: "sec.agent",
  },
  {
    icon: Layers,
    title: "Architecture Agent",
    description:
      "Analyzes compliance with modular architecture rules, DRY principles, file structures, and OOP/functional paradigms.",
    terminalId: "arc.agent",
  },
  {
    icon: Terminal,
    title: "Testing Agent",
    description:
      "Inspects code changes against test coverage maps, checks for missing assertions, and reviews unit test additions.",
    terminalId: "tst.agent",
  },
];

const stats = [
  { value: "3",    label: "Specialized Agents",  accent: "accent" },
  { value: "98%",  label: "Verdict Accuracy",    accent: "accent" },
  { value: "<2s",  label: "Analysis Time",       accent: "accent-tertiary" },
  { value: "∞",    label: "PRs Supported",       accent: "accent-secondary" },
];

export default function LandingPage() {
  const subtitle = useTypewriter(
    "Not more comments. One verdict.",
    28,
    900
  );

  useEffect(() => {
    if (window.location.hash === "#about") {
      setTimeout(() => {
        document.getElementById("about")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 150);
    }
  }, []);

  return (
    <div className="relative flex flex-col w-full overflow-hidden">

      {/* ════════════════════════════════════
          1. HERO
      ════════════════════════════════════ */}
      <section className="relative min-h-[92vh] flex flex-col justify-center items-center px-6 pt-8 pb-24 text-center z-10">

        {/* Radial glow behind headline */}
        <div
          className="absolute inset-0 pointer-events-none"
          aria-hidden="true"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 50% 40%, rgba(0,255,136,0.05) 0%, transparent 70%)",
          }}
        />

        {/* System status badge */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="inline-flex items-center gap-2 cyber-chamfer-sm border border-border bg-card px-4 py-1.5 mb-10"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-neon-pulse" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
            Orchestration Engine v2.4 — Online
          </span>
        </motion.div>

        {/* ── Glitched H1 ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-8 max-w-5xl"
        >
          <h1
            className="cyber-glitch font-orbitron text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black uppercase tracking-widest leading-[0.95] text-foreground"
            data-text="THE VERDICT SYSTEM FOR PULL REQUESTS"
            style={{
              textShadow: "0 0 30px rgba(0,255,136,0.15)",
            }}
          >
            <span className="block">THE VERDICT</span>
            <span
              className="block text-accent"
              style={{
                textShadow: "0 0 20px rgba(0,255,136,0.4), 0 0 60px rgba(0,255,136,0.15)",
              }}
            >
              SYSTEM FOR
            </span>
            <span className="block">PULL REQUESTS</span>
          </h1>
        </motion.div>

        {/* ── Typewriter subtitle ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.7 }}
          className="max-w-2xl mx-auto mb-12"
        >
          <p className="font-mono text-sm sm:text-base text-muted-foreground leading-relaxed tracking-wide">
            <span className="text-accent mr-1">//</span>
            {subtitle}
            <span className="cyber-cursor" />
          </p>
        </motion.div>

        {/* ── CTAs ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 1.1 }}
          className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto px-4"
        >
          <Link href="/repos" className="w-full sm:w-auto focus-visible:outline-none">
            <CTAButton variant="glitch" showArrow className="w-full sm:w-auto py-4 px-8 text-sm">
              Start Free Analysis
            </CTAButton>
          </Link>
          <a href="#about" className="w-full sm:w-auto focus-visible:outline-none">
            <CTAButton
              variant="outline"
              className="w-full sm:w-auto py-4 px-8 text-sm flex items-center gap-2"
            >
              <Eye className="w-3.5 h-3.5" strokeWidth={1.5} />
              Explore Mission
            </CTAButton>
          </a>
        </motion.div>

        {/* ── Stats strip ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 1.4 }}
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-px bg-border w-full max-w-3xl mx-auto overflow-hidden cyber-chamfer"
        >
          {stats.map(({ value, label }) => (
            <div
              key={label}
              className="bg-card px-6 py-5 flex flex-col items-center gap-1.5 group hover:bg-muted transition-colors duration-150"
            >
              <span
                className="font-orbitron text-2xl font-black text-accent"
                style={{ textShadow: "0 0 12px rgba(0,255,136,0.4)" }}
              >
                {value}
              </span>
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground text-center">
                {label}
              </span>
            </div>
          ))}
        </motion.div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent pointer-events-none" />
      </section>

      {/* ════════════════════════════════════
          2. FEATURES
      ════════════════════════════════════ */}
      <section className="relative px-6 py-24 md:py-32 z-10 border-t border-border">

        {/* Circuit bg accent on this section */}
        <div className="absolute inset-0 bg-circuit opacity-50 pointer-events-none" aria-hidden="true" />

        <div className="max-w-7xl mx-auto relative">

          {/* Section header */}
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-16">
            <div>
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent">
                // Agent Architecture
              </span>
              <h2 className="font-orbitron text-3xl sm:text-4xl font-bold uppercase tracking-wider text-foreground mt-2">
                Inspection Core
              </h2>
            </div>
            <p className="font-mono text-xs text-muted-foreground max-w-sm leading-relaxed md:text-right">
              Three specialized agents run in parallel, each operating on isolated domain knowledge and reporting structured diagnostics.
            </p>
          </div>

          {/* Feature grid — terminal variant */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-border overflow-hidden cyber-chamfer">
            {features.map((f, i) => (
              <FeatureCard
                key={f.title}
                icon={f.icon}
                title={f.title}
                description={f.description}
                delayIndex={i}
                variant="terminal"
                terminalId={f.terminalId}
              />
            ))}
          </div>

          {/* How it works — horizontal flow */}
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "01", icon: GitMerge,  label: "Ingest PR Diff",      desc: "Webhook receives GitHub event, raw diff is parsed into structured patch arrays." },
              { step: "02", icon: Zap,       label: "Debate Engine",       desc: "Three agents analyze in parallel, each challenging the others' confidence scores." },
              { step: "03", icon: Lock,      label: "Verdict Delivered",   desc: "Orchestrator synthesizes a final MERGE / CAUTION / BLOCK decision with evidence." },
            ].map(({ step, icon: Icon, label, desc }, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.12, duration: 0.4 }}
                className="flex flex-col gap-4"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="font-orbitron text-3xl font-black text-accent/20"
                    style={{ textShadow: "0 0 20px rgba(0,255,136,0.1)" }}
                  >
                    {step}
                  </span>
                  <div className="h-px flex-grow bg-border" />
                </div>
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-accent shrink-0" strokeWidth={1.5} />
                  <span className="font-orbitron text-xs font-bold uppercase tracking-wider text-foreground">
                    {label}
                  </span>
                </div>
                <p className="font-mono text-xs text-muted-foreground leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════
          3. ABOUT
      ════════════════════════════════════ */}
      <section
        id="about"
        className="relative px-6 py-24 md:py-32 z-10 border-t border-border scroll-mt-20"
      >
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-16 items-start">

          {/* Main column */}
          <div className="lg:col-span-7 flex flex-col justify-center">
            <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent mb-3">
              // Our Purpose
            </span>
            <h2 className="font-orbitron text-3xl sm:text-4xl font-bold uppercase tracking-wider text-foreground mb-8">
              About PRism AI
            </h2>
            <p className="font-mono text-xs sm:text-sm text-muted-foreground leading-relaxed mb-5">
              Modern engineering teams are drowning in code review noise. Line-by-line linting bots
              trigger spam warnings, while complex architectural drifts and subtle integration risks
              slip past busy human reviewers.
            </p>
            <p className="font-mono text-xs sm:text-sm text-muted-foreground leading-relaxed">
              PRism shifts the paradigm from micro-level annotations to macro-level triage. By
              orchestrating a debate between independent AI specialists, PRism acts as a digital
              control tower — evaluating pull requests holistically, assessing security posture,
              design conformity, and test coverage to deliver instant, actionable confidence verdicts.
            </p>

            {/* Terminal prompt aesthetic */}
            <div className="mt-10 border border-border cyber-chamfer bg-card overflow-hidden">
              <div className="flex items-center gap-2 px-4 h-7 bg-muted border-b border-border">
                <span className="w-2 h-2 rounded-full bg-destructive opacity-70" />
                <span className="w-2 h-2 rounded-full bg-yellow-500 opacity-70" />
                <span className="w-2 h-2 rounded-full bg-accent opacity-70" />
                <span className="ml-auto font-mono text-[10px] text-muted-foreground tracking-widest">mission.log</span>
              </div>
              <div className="p-5 space-y-1.5">
                {[
                  { prompt: "$", text: "initialize agent_debate_loop --agents=3" },
                  { prompt: ">", text: "security_agent:    ready [OK]", color: "text-accent" },
                  { prompt: ">", text: "architecture_agent: ready [OK]", color: "text-accent" },
                  { prompt: ">", text: "testing_agent:     ready [OK]", color: "text-accent" },
                  { prompt: "$", text: "run analysis --pr=main --confidence=high" },
                  { prompt: ">", text: "verdict: READY_TO_MERGE (confidence: 98%)", color: "text-accent" },
                ].map(({ prompt, text, color }, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="font-mono text-xs text-accent shrink-0">{prompt}</span>
                    <span className={`font-mono text-xs ${color ?? "text-muted-foreground"}`}>{text}</span>
                  </div>
                ))}
                <div className="flex gap-2">
                  <span className="font-mono text-xs text-accent">$</span>
                  <span className="font-mono text-xs text-muted-foreground cyber-cursor" />
                </div>
              </div>
            </div>
          </div>

          {/* Cards column */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            {[
              {
                tag: "01 / mission",
                title: "Our Mission",
                body: "To accelerate high-confidence merges. We equip development groups with automated, structured decision tools — transforming raw patch changes into readable, high-level risk evaluations.",
              },
              {
                tag: "02 / vision",
                title: "Our Vision",
                body: "A world where developers write code while automated agent intelligence handles verification, architectural checks, and security guards — making continuous integration truly seamless.",
              },
            ].map(({ tag, title, body }) => (
              <motion.div
                key={tag}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4 }}
                className="group border border-border bg-card cyber-chamfer p-6 hover:border-accent hover:shadow-neon transition-all duration-150"
              >
                <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent">
                  // {tag}
                </span>
                <h3 className="font-orbitron text-sm font-bold uppercase tracking-wider text-foreground mt-2 mb-3 group-hover:text-accent transition-colors duration-150">
                  {title}
                </h3>
                <p className="font-mono text-xs text-muted-foreground leading-relaxed">{body}</p>
              </motion.div>
            ))}

            {/* CTA panel */}
            <div className="border border-accent/30 bg-accent/5 cyber-chamfer p-6 shadow-neon-sm">
              <p className="font-mono text-xs text-muted-foreground leading-relaxed mb-5">
                Ready to eliminate review noise? Run your first analysis now — no setup required.
              </p>
              <Link href="/repos" className="focus-visible:outline-none">
                <CTAButton variant="primary" showArrow className="w-full justify-center py-3">
                  Launch Analyzer
                </CTAButton>
              </Link>
            </div>
          </div>

        </div>
      </section>

    </div>
  );
}
