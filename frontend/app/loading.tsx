"use client";

import { Cpu } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex-grow flex flex-col items-center justify-center px-6 py-20 text-center gap-4">
      <div className="relative flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border border-zinc-800 border-t-zinc-450 animate-spin" />
        <Cpu className="w-5 h-5 text-zinc-500 absolute animate-pulse" />
      </div>
      <span className="font-outfit text-[10px] font-semibold tracking-widest text-zinc-550 uppercase mt-2">
        Loading Assets...
      </span>
    </div>
  );
}
