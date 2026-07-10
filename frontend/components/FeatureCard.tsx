"use client";

import React from "react";
import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  delayIndex?: number;
}

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  delayIndex = 0,
}: FeatureCardProps) {
  // Stagger entry configurations
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 100,
        damping: 15,
        delay: delayIndex * 0.1,
      },
    },
  };

  return (
    <motion.div
      variants={itemVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-50px" }}
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
      className="group relative rounded-2xl border border-zinc-800/80 bg-zinc-900/30 p-8 backdrop-blur-sm overflow-hidden flex flex-col justify-between hover:border-zinc-700 hover:bg-zinc-900/50 transition-all shadow-lg shadow-black/10"
    >
      {/* Decorative gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-tr from-zinc-900/10 via-transparent to-zinc-800/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      
      <div>
        {/* ICON CONTAINER */}
        <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-6 group-hover:border-zinc-650 transition-colors shadow-inner">
          <Icon className="w-5 h-5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
        </div>

        {/* DETAILS */}
        <h3 className="font-outfit text-lg font-bold text-zinc-200 mb-3 group-hover:text-white transition-colors">
          {title}
        </h3>
        <p className="font-sans text-sm text-zinc-500 leading-relaxed group-hover:text-zinc-450 transition-colors">
          {description}
        </p>
      </div>

      {/* Decorative accent bottom line */}
      <div className="h-0.5 w-0 bg-zinc-400 group-hover:w-full transition-all duration-300 mt-6" />
    </motion.div>
  );
}
