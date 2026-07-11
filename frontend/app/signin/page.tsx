"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Cpu, Shield, AlertTriangle } from "lucide-react";
import GitHubButton from "@/components/GitHubButton";
import { createClient } from "@/utils/supabase/client";

export default function SignInPage() {
  const params = useSearchParams();
  const [loading, setLoading] = useState(false);

  const errorCode = params.get("error");
  const redirect = params.get("redirect") ?? "/repos";
  const errorMessages: Record<string, string> = {
    auth_callback_error: "Authentication callback failed. Try again.",
    OAuthSignin: "Could not start GitHub sign-in. Try again.",
    OAuthCallback: "GitHub returned an error. Try again.",
    OAuthAccountNotLinked: "This email is already linked to another account.",
    AccessDenied: "Access was denied. Authorise the app on GitHub.",
    default: "Authentication failed. Please try again.",
  };
  const errorMsg = errorCode
    ? (errorMessages[errorCode] ?? errorMessages.default)
    : null;

  const handleGitHub = async () => {
    setLoading(true);
    const supabase = createClient();
    const siteUrl =
      process.env.NEXT_PUBLIC_SITE_URL ?? window.location.origin;

    await supabase.auth.signInWithOAuth({
      provider: "github",
      options: {
        redirectTo: `${siteUrl}/auth/callback?next=${encodeURIComponent(redirect)}`,
        scopes: "read:user user:email repo",
      },
    });
  };

  return (
    <div className="flex-grow flex items-center justify-center px-6 py-20 relative overflow-hidden">

      <div
        className="absolute pointer-events-none"
        aria-hidden="true"
        style={{
          width: "500px", height: "500px",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          background: "radial-gradient(circle, rgba(0,255,136,0.04) 0%, transparent 70%)",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: "easeOut" }}
        className="w-full max-w-md"
      >
        <div className="border border-border cyber-chamfer bg-card overflow-hidden shadow-void">

          <div className="flex items-center gap-2 px-5 h-8 bg-muted border-b border-border">
            <span className="w-2 h-2 rounded-full bg-destructive opacity-70" />
            <span className="w-2 h-2 rounded-full bg-yellow-500 opacity-70" />
            <span className="w-2 h-2 rounded-full bg-accent opacity-70" />
            <span className="ml-auto font-mono text-[10px] text-muted-foreground tracking-widest">
              auth.signin
            </span>
          </div>

          <div className="p-8">

            <div className="flex flex-col items-center text-center mb-8 gap-4">
              <div className="w-14 h-14 cyber-chamfer border border-border bg-background flex items-center justify-center hover:border-accent hover:shadow-neon transition-all duration-150">
                <Cpu className="w-6 h-6 text-muted-foreground" strokeWidth={1.5} />
              </div>
              <div>
                <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-accent">
                  // Access Terminal
                </span>
                <h1 className="font-orbitron text-2xl font-bold uppercase tracking-wider text-foreground mt-1">
                  Welcome Back
                </h1>
                <p className="font-mono text-xs text-muted-foreground mt-2">
                  Authenticate to access the analysis deck.
                </p>
              </div>
            </div>

            {errorMsg && (
              <div className="mb-5 cyber-chamfer-sm border border-destructive/40 bg-destructive/10 px-4 py-3 flex items-start gap-2.5">
                <AlertTriangle className="w-3.5 h-3.5 text-destructive shrink-0 mt-0.5" strokeWidth={1.5} />
                <span className="font-mono text-[11px] text-destructive leading-relaxed">
                  // AUTH ERROR: {errorMsg}
                </span>
              </div>
            )}

            <div className="mb-6 border border-border/50 cyber-chamfer-sm bg-background p-4 space-y-1">
              {[
                { prompt: "$", text: "initialize auth_session" },
                { prompt: ">", text: "provider: github_oauth", color: "text-accent-tertiary" },
                { prompt: ">", text: loading ? "redirecting to github..." : "awaiting credentials...", color: "text-accent" },
              ].map(({ prompt, text, color }, i) => (
                <div key={i} className="flex gap-2 font-mono text-xs">
                  <span className="text-accent">{prompt}</span>
                  <span className={color ?? "text-muted-foreground"}>{text}</span>
                </div>
              ))}
              <div className="flex gap-2 font-mono text-xs">
                <span className="text-accent">$</span>
                <span className={`cyber-cursor text-muted-foreground ${loading ? "hidden" : ""}`} />
              </div>
            </div>

            <div className="mb-6">
              <GitHubButton
                onClick={handleGitHub}
                label={loading ? "Redirecting to GitHub..." : "Continue with GitHub"}
                disabled={loading}
              />
            </div>

            <div className="flex items-center gap-3 mb-6">
              <div className="h-px flex-grow bg-border" />
              <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground/50">or</span>
              <div className="h-px flex-grow bg-border" />
            </div>

            <p className="text-center font-mono text-xs text-muted-foreground">
              No account?{" "}
              <Link href="/signup" className="text-accent hover:text-accent/80 underline underline-offset-4 transition-colors focus-visible:outline-none">
                Create one here
              </Link>
            </p>
          </div>

          <div className="border-t border-border bg-muted/30 px-5 py-2.5 flex items-center gap-2">
            <Shield className="w-3 h-3 text-muted-foreground/40" strokeWidth={1.5} />
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground/40">
              Encrypted OAuth Handshake — GitHub via Supabase
            </span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
