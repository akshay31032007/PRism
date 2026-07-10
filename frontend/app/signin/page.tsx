"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Cpu } from "lucide-react";
import GitHubButton from "@/components/GitHubButton";

export default function SignInPage() {
  const router = useRouter();

  const handleMockGithubLogin = () => {
    // Navigate to repositories analyzer page as a mock login success state
    router.push("/repos");
  };

  return (
    <div className="flex-grow flex items-center justify-center px-6 py-20 relative overflow-hidden">
      
      {/* Visual background details */}
      <div className="absolute w-[400px] h-[400px] rounded-full bg-indigo-500/5 blur-[120px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-md bg-zinc-900/30 border border-zinc-800/80 rounded-3xl p-8 backdrop-blur-md shadow-2xl relative"
      >
        
        {/* LOGO */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-850 flex items-center justify-center mb-4">
            <Cpu className="w-6 h-6 text-zinc-350" />
          </div>
          <h1 className="font-outfit text-2xl font-bold tracking-tight text-zinc-200">
            Welcome Back
          </h1>
          <p className="font-sans text-xs text-zinc-550 mt-1">
            Analyze codebases, detect risks, inspect quality.
          </p>
        </div>

        {/* MOCK ACTION BUTTON */}
        <div className="mb-8">
          <GitHubButton onClick={handleMockGithubLogin} label="Continue with GitHub" />
        </div>

        {/* REDIRECT SIGNUP LINK */}
        <div className="text-center font-sans text-xs text-zinc-500">
          <span>No Account? </span>
          <Link
            href="/signup"
            className="text-zinc-300 font-semibold hover:text-white transition-colors underline underline-offset-4 focus-visible:outline-none"
          >
            Create Here
          </Link>
        </div>

      </motion.div>
    </div>
  );
}
