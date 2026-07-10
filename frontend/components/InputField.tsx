"use client";

import React, { InputHTMLAttributes } from "react";
import { LucideIcon } from "lucide-react";

interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: LucideIcon;
  error?: string;
  containerClassName?: string;
  /** Show terminal ">" prefix (default: true) */
  terminalPrefix?: boolean;
}

export default function InputField({
  icon: Icon,
  error,
  containerClassName = "",
  className = "",
  id,
  terminalPrefix = true,
  ...props
}: InputFieldProps) {
  return (
    <div className={`flex flex-col gap-1.5 w-full ${containerClassName}`}>
      <div className="relative flex items-center">

        {/* Terminal ">" prompt prefix */}
        {terminalPrefix && (
          <span
            className="absolute left-3 font-mono text-accent text-sm font-bold pointer-events-none select-none z-10"
            aria-hidden="true"
          >
            &gt;
          </span>
        )}

        {/* Optional icon — placed after the ">" */}
        {Icon && (
          <div className={`absolute pointer-events-none text-muted-foreground ${terminalPrefix ? "left-10" : "left-4"}`}>
            <Icon className="w-4 h-4" strokeWidth={1.5} />
          </div>
        )}

        <input
          id={id}
          aria-describedby={error ? `${id}-error` : undefined}
          aria-invalid={!!error}
          className={[
            "w-full bg-input border border-border cyber-chamfer-sm",
            "font-mono text-sm text-accent placeholder:text-muted-foreground/50",
            "py-3 pr-4 transition-all duration-150 outline-none",
            "focus:border-accent focus:shadow-neon-sm",
            error ? "border-destructive focus:border-destructive focus:shadow-neon-destructive" : "",
            terminalPrefix && Icon  ? "pl-16" : "",
            terminalPrefix && !Icon ? "pl-8"  : "",
            !terminalPrefix && Icon ? "pl-11" : "",
            !terminalPrefix && !Icon ? "pl-4" : "",
            className,
          ]
            .filter(Boolean)
            .join(" ")}
          {...props}
        />
      </div>

      {error && (
        <span
          id={`${id}-error`}
          className="font-mono text-xs text-destructive tracking-wide px-1"
          role="alert"
        >
          // ERROR: {error}
        </span>
      )}
    </div>
  );
}
