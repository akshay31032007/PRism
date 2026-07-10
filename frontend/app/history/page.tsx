"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { History, Database, Cpu, ArrowRight } from "lucide-react";
import CTAButton from "@/components/CTAButton";

export default function HistoryPage() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-20 w-full flex-grow flex flex-col justify-center items-center relative z-10">
      
      {/* Decorative center glow */}
      <div className="absolute w-[450px] h-[450px] rounded-full bg-zinc-900/10 blur-[130px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-xl text-center flex flex-col items-center gap-6"
      >
        
        {/* EMPTY STATE ILLUSTRATION */}
        <div className="relative w-24 h-24 flex items-center justify-center">
          {/* Animated decorative outer rings */}
          <motion.div
            animate={{ scale: [1, 1.15, 1], opacity: [0.1, 0.25, 0.1] }}
            transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
            className="absolute inset-0 rounded-full border border-zinc-800"
          />
          <motion.div
            animate={{ scale: [1, 1.25, 1], opacity: [0.05, 0.15, 0.05] }}
            transition={{ repeat: Infinity, duration: 4, ease: "easeInOut", delay: 1 }}
            className="absolute -inset-4 rounded-full border border-zinc-900"
          />
          
          {/* Main Icon container */}
          <div className="w-16 h-16 rounded-2xl bg-zinc-900/80 border border-zinc-800/80 flex items-center justify-center shadow-lg shadow-black/20">
            <History className="w-7 h-7 text-zinc-550" />
          </div>
        </div>

        {/* DETAILS */}
        <div className="flex flex-col gap-2.5 mt-2">
          <h2 className="font-outfit text-xl sm:text-2xl font-bold tracking-tight text-zinc-200">
            No analysis history yet
          </h2>
          <p className="font-sans text-xs sm:text-sm text-zinc-500 max-w-sm mx-auto leading-relaxed">
            Your repository analysis pipeline history will appear here. Past reports are currently cleared upon page refresh.
          </p>
        </div>

        {/* FUTURE BACKEND INTEGRATION PLACEHOLDER */}
        <div className="w-full mt-4 p-4 rounded-2xl border border-zinc-900 bg-zinc-950/30 flex items-center justify-center gap-3 max-w-sm">
          <Database className="w-4 h-4 text-zinc-650 shrink-0" />
          <span className="font-sans text-[10px] text-zinc-600 font-semibold tracking-wider uppercase text-left">
            DATABASE INTEGRATION PENDING SETUP
          </span>
        </div>

        {/* ACTION BUTTON */}
        <div className="mt-6">
          <Link href="/repos" className="focus-visible:outline-none">
            <CTAButton variant="primary" showArrow className="py-3 px-6 text-xs">
              Go to Repository Analyzer
            </CTAButton>
          </Link>
        </div>

      </motion.div>
    </div>
  );
}
