"use client";

import React from "react";
import { motion } from "framer-motion";
import { Github } from "lucide-react";

interface GitHubButtonProps {
  onClick?: () => void;
  label?:    string;
  className?: string;
  disabled?:  boolean;
}

export default function GitHubButton({
  onClick,
  label     = "Continue with GitHub",
  className = "",
  disabled  = false,
}: GitHubButtonProps) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? {} : { scale: 1.01 }}
      whileTap={disabled  ? {} : { scale: 0.98 }}
      className={[
        "w-full py-3.5 px-5 cyber-chamfer-sm",
        "border-2 border-border bg-card",
        "font-mono text-xs font-semibold uppercase tracking-[0.15em] text-foreground",
        "flex items-center justify-center gap-3",
        "transition-all duration-150",
        disabled
          ? "opacity-60 cursor-not-allowed"
          : "hover:border-accent-tertiary hover:text-accent-tertiary hover:shadow-neon-tertiary",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        className,
      ].filter(Boolean).join(" ")}
    >
      <Github className="w-5 h-5" strokeWidth={1.5} />
      <span>{label}</span>
    </motion.button>
  );
}
