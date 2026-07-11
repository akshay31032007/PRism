"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useSupabase } from "@/components/SessionProvider";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Cpu, LogOut, ChevronDown } from "lucide-react";

export default function Navbar() {
  const [isOpen,    setIsOpen]    = useState(false);
  const [scrolled,  setScrolled]  = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const pathname = usePathname();
  const { user, loading, signOut } = useSupabase();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleAboutClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (pathname === "/") {
      e.preventDefault();
      document.getElementById("about")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    setIsOpen(false);
  };

  const navItems = [
    { label: "Repos",   href: "/repos" },
    { label: "About",   href: "/#about", onClick: handleAboutClick },
    { label: "History", href: "/history" },
  ];

  const isActive = (href: string) =>
    href === "/#about" ? false : pathname === href;

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-200 ${
        scrolled
          ? "bg-background/90 backdrop-blur-md border-b border-border shadow-void"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">

        {/* ── Logo ── */}
        <Link href="/" className="group flex items-center gap-3 focus-visible:outline-none" aria-label="PRism home">
          <div className="w-9 h-9 cyber-chamfer-sm border border-border bg-card flex items-center justify-center transition-all duration-150 group-hover:border-accent group-hover:shadow-neon-sm">
            <Cpu className="w-4 h-4 text-muted-foreground group-hover:text-accent transition-colors duration-150" strokeWidth={1.5} />
          </div>
          <span className="font-orbitron text-base font-bold tracking-widest text-foreground group-hover:text-accent transition-colors duration-150">
            PR<span className="text-accent">ism</span>
            <span className="text-muted-foreground font-mono text-xs">.ai</span>
          </span>
        </Link>

        {/* ── Desktop nav ── */}
        <nav className="hidden md:flex items-center gap-8" aria-label="Main navigation">
          {navItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              onClick={item.onClick}
              className={`relative font-mono text-xs uppercase tracking-[0.18em] py-1 transition-colors duration-150 ${
                isActive(item.href)
                  ? "text-accent"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {item.label}
              {isActive(item.href) && (
                <motion.span
                  layoutId="nav-indicator"
                  className="absolute -bottom-0.5 left-0 right-0 h-px bg-accent shadow-neon-sm"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
            </Link>
          ))}
        </nav>

        {/* ── Auth area ── */}
        <div className="hidden md:block">
          {loading ? (
            /* Skeleton while session loads */
            <div className="w-24 h-8 cyber-chamfer-sm bg-muted animate-pulse" />

          ) : user ? (
            /* ── Logged-in: avatar + dropdown ── */
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2.5 cyber-chamfer-sm border border-border bg-card px-3 py-1.5 hover:border-accent hover:shadow-neon-sm transition-all duration-150 focus-visible:outline-none"
              >
                {user.user_metadata?.avatar_url ? (
                  <Image
                    src={user.user_metadata.avatar_url}
                    alt={user.user_metadata.full_name ?? user.email ?? "User"}
                    width={22}
                    height={22}
                    className="rounded-full"
                  />
                ) : (
                  <div className="w-5 h-5 rounded-full bg-accent/20 flex items-center justify-center">
                    <span className="font-mono text-[10px] text-accent">
                      {(user.user_metadata?.full_name ?? user.email)?.[0]?.toUpperCase() ?? "U"}
                    </span>
                  </div>
                )}
                <span className="font-mono text-xs text-foreground tracking-wide max-w-[120px] truncate">
                  {user.user_metadata?.full_name ?? user.user_metadata?.user_name ?? user.email}
                </span>
                <ChevronDown className="w-3 h-3 text-muted-foreground" strokeWidth={1.5} />
              </button>

              <AnimatePresence>
                {userMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0,  scale: 1 }}
                    exit={{ opacity: 0, y: -8,  scale: 0.97 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-full mt-2 w-48 border border-border bg-card cyber-chamfer shadow-void overflow-hidden z-50"
                  >
                    {/* User info */}
                    <div className="px-4 py-3 border-b border-border">
                      <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-accent">
                        // Authenticated
                      </p>
                      <p className="font-mono text-xs text-foreground mt-1 truncate">
                        {user.email}
                      </p>
                    </div>

                    {/* Sign out */}
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        signOut();
                      }}
                      className="w-full flex items-center gap-2.5 px-4 py-3 font-mono text-xs uppercase tracking-[0.15em] text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-all duration-150"
                    >
                      <LogOut className="w-3.5 h-3.5" strokeWidth={1.5} />
                      Sign Out
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

          ) : (
            /* ── Logged-out: Sign In button ── */
            <Link href="/signin" className="focus-visible:outline-none">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                className="cyber-chamfer-sm border border-border bg-card px-5 py-2 font-mono text-xs uppercase tracking-[0.18em] text-muted-foreground hover:border-accent hover:text-accent hover:shadow-neon-sm transition-all duration-150"
              >
                Sign_In
              </motion.button>
            </Link>
          )}
        </div>

        {/* ── Mobile toggle ── */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="md:hidden p-2 text-muted-foreground hover:text-accent transition-colors duration-150 focus-visible:outline-none"
          aria-expanded={isOpen}
          aria-label="Toggle navigation"
        >
          {isOpen
            ? <X    className="w-5 h-5" strokeWidth={1.5} />
            : <Menu className="w-5 h-5" strokeWidth={1.5} />
          }
        </button>
      </div>

      {/* ── Mobile drawer ── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-b border-border bg-background/95 backdrop-blur-lg overflow-hidden"
          >
            <div className="scanlines px-6 py-5 flex flex-col gap-4">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={item.onClick ?? (() => setIsOpen(false))}
                  className={`font-mono text-xs uppercase tracking-[0.18em] py-2 border-b border-border/50 transition-colors duration-150 ${
                    isActive(item.href) ? "text-accent" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <span className="text-accent mr-2">&gt;</span>
                  {item.label}
                </Link>
              ))}

              <div className="pt-2">
                {user ? (
                  <button
                    onClick={() => { setIsOpen(false); signOut(); }}
                    className="w-full flex items-center gap-2 py-3 cyber-chamfer-sm border border-border font-mono text-xs uppercase tracking-[0.18em] text-muted-foreground hover:border-destructive hover:text-destructive transition-all duration-150"
                  >
                    <LogOut className="w-3.5 h-3.5 ml-4" strokeWidth={1.5} />
                    Sign Out
                  </button>
                ) : (
                  <Link href="/signin" onClick={() => setIsOpen(false)} className="block focus-visible:outline-none">
                    <button className="w-full py-3 cyber-chamfer-sm border border-border font-mono text-xs uppercase tracking-[0.18em] text-muted-foreground hover:border-accent hover:text-accent hover:shadow-neon-sm transition-all duration-150">
                      Sign_In
                    </button>
                  </Link>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
