"use client";

import React from "react";
import { motion } from "framer-motion";
import { Github } from "lucide-react";

interface GitHubButtonProps {
  onClick?: () => void;
  label?: string;
  className?: string;
}

export default function GitHubButton({
  onClick,
  label = "Continue with GitHub",
  className = "",
}: GitHubButtonProps) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.01, borderColor: "rgba(255, 255, 255, 0.3)" }}
      whileTap={{ scale: 0.99 }}
      className={`w-full py-3.5 px-4 rounded-xl border border-zinc-800 bg-zinc-900 text-sm font-semibold tracking-wide text-zinc-200 flex items-center justify-center gap-3 transition-colors hover:bg-zinc-850 hover:text-white shadow-sm shadow-black/40 focus-visible:outline-none ${className}`}
    >
      <Github className="w-5 h-5 text-zinc-300" />
      <span>{label}</span>
    </motion.button>
  );
}
