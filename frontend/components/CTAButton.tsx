"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface CTAButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  /** primary = neon green border/fill | secondary = magenta | glitch = solid neon | ghost = no border */
  variant?: "primary" | "secondary" | "glitch" | "ghost" | "outline";
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
  const base =
    "relative inline-flex items-center justify-center gap-2 px-6 py-3 " +
    "font-mono text-xs font-semibold uppercase tracking-[0.18em] " +
    "transition-all duration-150 select-none focus-visible:outline-none " +
    "disabled:opacity-40 disabled:cursor-not-allowed " +
    "focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background";

  const variantStyles: Record<string, string> = {
    /** Default — transparent, neon green border, fills on hover */
    primary:
      "cyber-chamfer-sm border-2 border-accent text-accent " +
      "hover:bg-accent hover:text-background hover:shadow-neon " +
      "active:brightness-90",

    /** Secondary — magenta border, fills on hover */
    secondary:
      "cyber-chamfer-sm border-2 border-accent-secondary text-accent-secondary " +
      "hover:bg-accent-secondary hover:text-background hover:shadow-neon-secondary " +
      "active:brightness-90",

    /** Glitch — solid neon fill, chromatic aberration animation */
    glitch:
      "cyber-chamfer-sm bg-accent text-background border-2 border-accent " +
      "hover:brightness-110 hover:shadow-neon-lg " +
      "active:brightness-90",

    /** Outline — dim border, reveals neon on hover */
    outline:
      "cyber-chamfer-sm border border-border text-muted-foreground " +
      "hover:border-accent hover:text-accent hover:shadow-neon-sm " +
      "active:brightness-90",

    /** Ghost — no border, subtle fill on hover */
    ghost:
      "text-muted-foreground hover:text-accent hover:bg-accent/10 " +
      "active:brightness-90",
  };

  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.97 }}
      className={`${base} ${variantStyles[variant]} ${className}`}
    >
      {/* Glitch variant gets chromatic aberration overlay */}
      {variant === "glitch" && (
        <span
          className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-0 hover:opacity-100 transition-opacity"
          aria-hidden="true"
          style={{ textShadow: "-1px 0 #ff00ff, 1px 0 #00d4ff" }}
        />
      )}

      <span className="relative z-10">{children}</span>
      {showArrow && (
        <ArrowRight
          className="relative z-10 w-3.5 h-3.5 transition-transform group-hover:translate-x-1"
          strokeWidth={1.5}
        />
      )}
    </motion.button>
  );
}
