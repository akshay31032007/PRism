"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface CTAButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary";
  showArrow?: boolean;
  type?: "button" | "submit" | "reset";
  className?: string;
  disabled?: boolean;
}

export default function CTAButton({
  children,
  onClick,
  variant = "primary",
  showArrow = false,
  type = "button",
  className = "",
  disabled = false,
}: CTAButtonProps) {
  const baseStyle =
    "px-6 py-3 rounded-lg text-sm font-semibold uppercase tracking-wider flex items-center justify-center gap-2 transition-all select-none focus-visible:outline-none";

  const variants = {
    primary:
      "bg-zinc-100 text-zinc-950 hover:bg-zinc-200 border border-transparent shadow-md shadow-white/5 disabled:bg-zinc-800 disabled:text-zinc-650",
    secondary:
      "bg-zinc-950/60 border border-zinc-800 text-zinc-350 hover:text-zinc-100 hover:border-zinc-550 shadow-sm shadow-black/30 disabled:border-zinc-900 disabled:text-zinc-700",
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      className={`${baseStyle} ${variants[variant]} ${className}`}
    >
      <span>{children}</span>
      {showArrow && <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />}
    </motion.button>
  );
}
