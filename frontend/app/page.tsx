"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ShieldCheck, Layers, Terminal, Sparkles, ArrowRight, Eye } from "lucide-react";
import FeatureCard from "@/components/FeatureCard";
import CTAButton from "@/components/CTAButton";

export default function LandingPage() {
  // Automatically smooth-scroll to #about if hash exists on load
  useEffect(() => {
    if (window.location.hash === "#about") {
      const el = document.getElementById("about");
      if (el) {
        // Delay scroll slightly to ensure page renders first
        setTimeout(() => {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 150);
      }
    }
  }, []);

  const features = [
    {
      icon: ShieldCheck,
      title: "Security Agent Analysis",
      description:
        "Scans incoming diffs for secrets leakages, dependency vulnerabilities, and insecure coding patterns before they hit production.",
    },
    {
      icon: Layers,
      title: "Architecture & Clean Code",
      description:
        "Analyzes compliance with modular architecture rules, DRY principles, file structures, and OOP/functional paradigms.",
    },
    {
      icon: Terminal,
      title: "Coverage & Testing Triage",
      description:
        "Inspects code changes against test coverage maps, checks for missing assertions, and reviews unit test additions.",
    },
  ];

  return (
    <div className="relative flex flex-col w-full overflow-hidden">
      
      {/* 1. HERO SECTION */}
      <section className="relative min-h-[85vh] flex flex-col justify-center items-center px-6 py-20 text-center z-10">
        
        {/* Glow indicator */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm text-xs font-medium text-zinc-300 tracking-wide mb-8 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-zinc-400" />
          <span>Automated Agent Orchestration</span>
        </motion.div>

        {/* Large Tagline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut", delay: 0.1 }}
          className="font-outfit text-4xl sm:text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] max-w-4xl text-zinc-100"
        >
          Automated Pull Request <br />
          <span className="bg-gradient-to-r from-zinc-100 via-zinc-400 to-zinc-500 bg-clip-text text-transparent">
            Code Triage & Inspection
          </span>
        </motion.h1>

        {/* Supporting Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 25 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut", delay: 0.2 }}
          className="font-sans text-base sm:text-lg md:text-xl text-zinc-500 max-w-2xl mt-8 leading-relaxed"
        >
          PRism coordinates specialized autonomous agents—Security, Architecture, and Testing—to review patch arrays, verify live CI runs, and deliver high-confidence merge verdicts.
        </motion.p>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut", delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center gap-4 mt-12 w-full sm:w-auto px-4"
        >
          <Link href="/repos" className="w-full sm:w-auto focus-visible:outline-none">
            <CTAButton variant="primary" showArrow className="w-full sm:w-auto py-3.5 px-7">
              Start Free Analysis
            </CTAButton>
          </Link>
          <a href="#about" className="w-full sm:w-auto focus-visible:outline-none">
            <CTAButton
              variant="secondary"
              className="w-full sm:w-auto py-3.5 px-7 flex items-center justify-center gap-2 group"
            >
              <Eye className="w-4 h-4 text-zinc-400 group-hover:text-zinc-200 transition-colors" />
              <span>Explore Mission</span>
            </CTAButton>
          </a>
        </motion.div>

        {/* Decorative Grid bottom shadow fade */}
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-zinc-950 to-transparent pointer-events-none" />
      </section>

      {/* 2. FEATURES SECTION */}
      <section className="px-6 py-24 md:py-32 max-w-7xl mx-auto w-full z-10 border-t border-zinc-900/60">
        <div className="text-center md:text-left mb-16 md:mb-20">
          <span className="text-xs font-semibold uppercase tracking-widest text-zinc-555">Precision Reviews</span>
          <h2 className="font-outfit text-3xl sm:text-4xl font-bold tracking-tight text-zinc-200 mt-2">
            Automated Inspection Core
          </h2>
          <p className="font-sans text-sm text-zinc-500 max-w-lg mt-4 leading-relaxed">
            Our multi-agent debate loop evaluates each code change in isolation and reports precise, structured diagnostics.
          </p>
        </div>

        {/* Responsive Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, idx) => (
            <FeatureCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              delayIndex={idx}
            />
          ))}
        </div>
      </section>

      {/* 3. ABOUT US SECTION */}
      <section
        id="about"
        className="px-6 py-24 md:py-32 max-w-7xl mx-auto w-full z-10 border-t border-zinc-900/60 scroll-mt-24"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-start">
          
          {/* Main Info Column (8 Cols) */}
          <div className="lg:col-span-7 flex flex-col justify-center">
            <span className="text-xs font-semibold uppercase tracking-widest text-zinc-555">Our Purpose</span>
            <h2 className="font-outfit text-3xl sm:text-4xl font-bold tracking-tight text-zinc-200 mt-2 mb-6">
              About PRism AI
            </h2>
            <p className="font-sans text-sm sm:text-base text-zinc-500 leading-relaxed mb-6">
              Modern engineering teams are drowning in code review noise. Line-by-line linting bots trigger spam warnings, while complex architectural drifts and subtle integration risks slip past busy human reviewers.
            </p>
            <p className="font-sans text-sm sm:text-base text-zinc-500 leading-relaxed">
              PRism shifts the paradigm from micro-level annotations to macro-level triage. By orchestrating a debate between independent AI specialists, PRism acts as a digital control tower. It evaluates pull requests holistically, assessing security posture, design conformity, and test coverage maps to provide developers with instant, actionable confidence verdicts.
            </p>
          </div>

          {/* Cards Column (5 Cols) */}
          <div className="lg:col-span-5 flex flex-col gap-6 w-full">
            
            {/* MISSION CARD */}
            <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/20 backdrop-blur-sm hover:border-zinc-700 transition-colors">
              <h3 className="font-outfit text-md font-bold uppercase tracking-wider text-zinc-300 mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
                Our Mission
              </h3>
              <p className="font-sans text-xs sm:text-sm text-zinc-500 leading-relaxed">
                To accelerate high-confidence merges. We equip development groups with automated, structured decision tools, transforming raw patch changes into readable, high-level risk evaluations.
              </p>
            </div>

            {/* VISION CARD */}
            <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-900/20 backdrop-blur-sm hover:border-zinc-700 transition-colors">
              <h3 className="font-outfit text-md font-bold uppercase tracking-wider text-zinc-300 mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
                Our Vision
              </h3>
              <p className="font-sans text-xs sm:text-sm text-zinc-500 leading-relaxed">
                A world where developers write code while automated agent intelligence handles verification, architectural checks, and security guards—making continuous integration truly seamless.
              </p>
            </div>

          </div>

        </div>
      </section>

    </div>
  );
}
