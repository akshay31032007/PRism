"use client";

import React, { InputHTMLAttributes } from "react";
import { LucideIcon } from "lucide-react";

interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: LucideIcon;
  error?: string;
  containerClassName?: string;
}

export default function InputField({
  icon: Icon,
  error,
  containerClassName = "",
  className = "",
  id,
  ...props
}: InputFieldProps) {
  return (
    <div className={`flex flex-col gap-1.5 w-full ${containerClassName}`}>
      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-4 text-zinc-500 pointer-events-none">
            <Icon className="w-5 h-5" />
          </div>
        )}
        <input
          id={id}
          className={`w-full bg-zinc-900/60 border border-zinc-800 rounded-xl py-3.5 pr-4 text-sm text-zinc-150 placeholder:text-zinc-550 transition-all focus:border-zinc-600 focus:bg-zinc-900/90 focus:ring-1 focus:ring-zinc-650 ${
            Icon ? "pl-12" : "pl-4"
          } ${
            error ? "border-red-900/60 focus:border-red-500 focus:ring-red-500" : ""
          } ${className}`}
          {...props}
        />
      </div>
      {error && (
        <span className="text-xs text-red-500 font-medium px-1" id={`${id}-error`}>
          {error}
        </span>
      )}
    </div>
  );
}
