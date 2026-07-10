"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ShieldAlert, Cpu } from "lucide-react";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  // Handle transparent background switching to glassmorphism on scroll
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Smooth scroll handler for About Us
  const handleAboutClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (pathname === "/") {
      e.preventDefault();
      const el = document.getElementById("about");
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
    setIsOpen(false);
  };

  const navItems = [
    { label: "Repos", href: "/repos" },
    { label: "About Us", href: "/#about", onClick: handleAboutClick },
    { label: "History", href: "/history" },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/80 py-4 shadow-lg shadow-black/10"
          : "bg-transparent border-b border-transparent py-5"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        {/* LOGO */}
        <Link
          href="/"
          className="flex items-center gap-2.5 group focus-visible:outline-none"
          aria-label="PRism Home"
        >
          <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-700/60 overflow-hidden group-hover:border-zinc-500 transition-colors">
            <Cpu className="w-5 h-5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 via-transparent to-emerald-500/20 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <span className="font-outfit text-xl font-bold tracking-wider bg-gradient-to-r from-zinc-100 via-zinc-300 to-zinc-400 bg-clip-text text-transparent group-hover:text-zinc-100 transition-colors">
            PRism<span className="text-zinc-500">.ai</span>
          </span>
        </Link>

        {/* DESKTOP NAV */}
        <nav className="hidden md:flex items-center gap-8" aria-label="Main Navigation">
          {navItems.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              onClick={item.onClick}
              className={`font-sans text-sm font-medium tracking-wide transition-colors relative py-1 hover:text-zinc-100 ${
                (pathname === item.href || (item.href === "/#about" && pathname === "/" && typeof window !== "undefined" && window.location.hash === "#about"))
                  ? "text-zinc-100"
                  : "text-zinc-400"
              }`}
            >
              {item.label}
              {pathname === item.href && (
                <motion.span
                  layoutId="navUnderline"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-zinc-200"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </Link>
          ))}
        </nav>

        {/* RIGHT ACTION */}
        <div className="hidden md:block">
          <Link href="/signin" className="focus-visible:outline-none">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              className="px-5 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider text-zinc-300 border border-zinc-700/80 bg-zinc-900/50 hover:bg-zinc-900 hover:border-zinc-500 hover:text-white transition-all shadow-sm shadow-black/20"
            >
              Sign In
            </motion.button>
          </Link>
        </div>

        {/* MOBILE MENU TOGGLE */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="md:hidden p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/50 transition-colors"
          aria-expanded={isOpen}
          aria-label="Toggle navigation menu"
        >
          {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* MOBILE NAV OVERLAY */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="md:hidden border-b border-zinc-800 bg-zinc-950/95 backdrop-blur-lg overflow-hidden"
          >
            <div className="px-6 py-6 flex flex-col gap-5">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={item.onClick}
                  className={`text-base font-medium tracking-wide py-1 border-b border-zinc-900/50 ${
                    pathname === item.href ? "text-zinc-100" : "text-zinc-400"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              <div className="pt-2">
                <Link
                  href="/signin"
                  onClick={() => setIsOpen(false)}
                  className="block w-full focus-visible:outline-none"
                >
                  <button className="w-full py-3 rounded-lg text-sm font-semibold uppercase tracking-wider text-zinc-200 border border-zinc-800 bg-zinc-900 text-center hover:bg-zinc-850 hover:text-white transition-colors">
                    Sign In
                  </button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
