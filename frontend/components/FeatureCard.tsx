"use client";

import React from "react";
import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  delayIndex?: number;
  /** default = chamfered card | terminal = CRT terminal variant */
  variant?: "default" | "terminal";
  /** index shown in terminal variant header, e.g. "01" */
  terminalId?: string;
}

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  delayIndex = 0,
  variant = "default",
  terminalId,
}: FeatureCardProps) {
  const itemVariants = {
    hidden:   { opacity: 0, y: 24 },
    visible:  {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring" as const,
        stiffness: 80,
        damping: 14,
        delay: delayIndex * 0.12,
      },
    },
  };

  if (variant === "terminal") {
    return (
      <motion.div
        variants={itemVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-40px" }}
        whileHover={{ y: -4, transition: { duration: 0.15 } }}
        className="group relative border border-border bg-card overflow-hidden cyber-chamfer flex flex-col transition-all duration-150 hover:border-accent hover:shadow-neon"
      >
        {/* Terminal header bar */}
        <div className="flex items-center gap-2 px-4 h-7 bg-muted border-b border-border shrink-0">
          <span className="w-2 h-2 rounded-full bg-destructive opacity-80" />
          <span className="w-2 h-2 rounded-full bg-yellow-500 opacity-80" />
          <span className="w-2 h-2 rounded-full bg-accent opacity-80" />
          <span className="ml-auto font-mono text-[10px] text-muted-foreground tracking-widest uppercase">
            {terminalId ?? String(delayIndex + 1).padStart(2, "0")}.agent
          </span>
        </div>

        <div className="p-6 flex flex-col gap-4 flex-grow">
          {/* Icon */}
          <div className="w-10 h-10 border border-border bg-background flex items-center justify-center cyber-chamfer-sm group-hover:border-accent group-hover:shadow-neon-sm transition-all duration-150">
            <Icon
              className="w-4 h-4 text-muted-foreground group-hover:text-accent transition-colors duration-150"
              strokeWidth={1.5}
            />
          </div>

          <div>
            <h3 className="font-orbitron text-sm font-bold text-foreground mb-2 tracking-wider uppercase group-hover:text-accent transition-colors duration-150">
              {title}
            </h3>
            <p className="font-mono text-xs text-muted-foreground leading-relaxed">
              {description}
            </p>
          </div>

          {/* Neon bottom bar — expands on hover */}
          <div className="mt-auto pt-4">
            <div className="h-px w-0 bg-accent group-hover:w-full transition-all duration-300 shadow-neon-sm" />
          </div>
        </div>
      </motion.div>
    );
  }

  /* ── Default chamfered card ── */
  return (
    <motion.div
      variants={itemVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-40px" }}
      whileHover={{ y: -5, transition: { duration: 0.15 } }}
      className="group relative border border-border bg-card overflow-hidden cyber-chamfer p-8 flex flex-col transition-all duration-150 hover:border-accent hover:shadow-neon"
    >
      {/* Corner accent marks — holographic feel */}
      <span className="absolute top-0 left-0 w-4 h-px bg-accent opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden="true" />
      <span className="absolute top-0 left-0 w-px h-4 bg-accent opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden="true" />
      <span className="absolute bottom-0 right-0 w-4 h-px bg-accent opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden="true" />
      <span className="absolute bottom-0 right-0 w-px h-4 bg-accent opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden="true" />

      {/* Icon container */}
      <div className="w-12 h-12 border border-border bg-background flex items-center justify-center cyber-chamfer-sm mb-6 group-hover:border-accent group-hover:shadow-neon-sm transition-all duration-150">
        <Icon
          className="w-5 h-5 text-muted-foreground group-hover:text-accent transition-colors duration-150"
          strokeWidth={1.5}
        />
      </div>

      <h3 className="font-orbitron text-sm font-bold text-foreground mb-3 tracking-wider uppercase group-hover:text-accent transition-colors duration-150">
        {title}
      </h3>

      <p className="font-mono text-xs text-muted-foreground leading-relaxed flex-grow">
        {description}
      </p>

      {/* Expanding neon bottom bar */}
      <div className="h-px w-0 bg-accent group-hover:w-full transition-all duration-300 mt-6 shadow-neon-sm" />
    </motion.div>
  );
}
