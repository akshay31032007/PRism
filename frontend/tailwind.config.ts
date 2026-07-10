import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      /* ── Fonts ── */
      fontFamily: {
        orbitron: ["Orbitron", "Share Tech Mono", "monospace"],
        mono:     ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
        label:    ["Share Tech Mono", "monospace"],
        // Legacy aliases kept for compatibility
        sans:     ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
        outfit:   ["Orbitron", "Share Tech Mono", "monospace"],
      },

      /* ── Colors ── */
      colors: {
        /* Backgrounds */
        background: "#0a0a0f",
        foreground: "#e0e0e0",

        /* Card surfaces */
        card: {
          DEFAULT:    "#12121a",
          foreground: "#e0e0e0",
        },

        /* Muted surfaces */
        muted: {
          DEFAULT:    "#1c1c2e",
          foreground: "#6b7280",
        },

        /* Neon accents */
        accent: {
          DEFAULT:   "#00ff88",
          secondary: "#ff00ff",
          tertiary:  "#00d4ff",
          foreground: "#0a0a0f",
        },

        /* UI chrome */
        border:      "#2a2a3a",
        input:       "#12121a",
        ring:        "#00ff88",
        destructive: {
          DEFAULT:    "#ff3366",
          foreground: "#e0e0e0",
        },

        /* Semantic aliases for convenience */
        neon:    "#00ff88",
        magenta: "#ff00ff",
        cyan:    "#00d4ff",
      },

      /* ── Border radius — sharp by default ── */
      borderRadius: {
        none: "0px",
        sm:   "2px",
        DEFAULT: "2px",
        md:   "4px",
        lg:   "4px",
        xl:   "4px",
        "2xl": "4px",
        "3xl": "4px",
        full: "9999px",
      },

      /* ── Box shadows (neon glows) ── */
      boxShadow: {
        "neon":           "0 0 5px #00ff88, 0 0 10px #00ff8840",
        "neon-sm":        "0 0 3px #00ff88, 0 0 6px #00ff8830",
        "neon-lg":        "0 0 10px #00ff88, 0 0 20px #00ff8860, 0 0 40px #00ff8830",
        "neon-secondary": "0 0 5px #ff00ff, 0 0 20px #ff00ff60",
        "neon-tertiary":  "0 0 5px #00d4ff, 0 0 20px #00d4ff60",
        "neon-destructive":"0 0 5px #ff3366, 0 0 20px #ff336660",
        "panel":          "0 0 0 1px #2a2a3a, 0 4px 32px rgba(0,0,0,0.6)",
        "void":           "0 8px 48px rgba(0,0,0,0.9)",
      },

      /* ── Animations ── */
      keyframes: {
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%":       { opacity: "0" },
        },
        glitch: {
          "0%, 100%": { transform: "translate(0, 0) skewX(0deg)" },
          "10%":       { transform: "translate(-2px, 1px) skewX(-1deg)" },
          "20%":       { transform: "translate(2px, -1px) skewX(1deg)" },
          "30%":       { transform: "translate(0, 0) skewX(0deg)" },
          "60%":       { transform: "translate(-1px, 2px) skewX(0.5deg)" },
          "80%":       { transform: "translate(0, 0)" },
        },
        rgbShift: {
          "0%, 100%": { textShadow: "-2px 0 #ff00ff, 2px 0 #00d4ff" },
          "50%":       { textShadow: "2px 0 #ff00ff, -2px 0 #00d4ff" },
        },
        neonPulse: {
          "0%, 100%": { boxShadow: "0 0 5px #00ff88, 0 0 10px #00ff8840" },
          "50%":       { boxShadow: "0 0 10px #00ff88, 0 0 20px #00ff8860, 0 0 40px #00ff8830" },
        },
        neonPulseText: {
          "0%, 100%": { textShadow: "0 0 6px #00ff88, 0 0 12px #00ff8850" },
          "50%":       { textShadow: "0 0 12px #00ff88, 0 0 24px #00ff8870, 0 0 40px #00ff8830" },
        },
        floatY: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":       { transform: "translateY(-8px)" },
        },
        spinSlow: {
          from: { transform: "rotate(0deg)" },
          to:   { transform: "rotate(360deg)" },
        },
        fadeInUp: {
          from: { opacity: "0", transform: "translateY(16px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        scanlineScroll: {
          "0%":   { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
      },

      animation: {
        "blink":             "blink 1s step-end infinite",
        "glitch":            "glitch 8s infinite",
        "rgb-shift":         "rgbShift 4s ease-in-out infinite",
        "neon-pulse":        "neonPulse 3s ease-in-out infinite",
        "neon-pulse-text":   "neonPulseText 3s ease-in-out infinite",
        "float":             "floatY 4s ease-in-out infinite",
        "spin-slow":         "spinSlow 8s linear infinite",
        "fade-in-up":        "fadeInUp 0.5s ease-out forwards",
        "scanline":          "scanlineScroll 8s linear infinite",
      },

      /* ── Spacing / sizing extras ── */
      screens: {
        xs: "480px",
      },
    },
  },
  plugins: [],
};

export default config;
