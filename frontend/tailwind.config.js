/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        // Dark background palette
        bg: {
          primary: "#0A0F1E",
          secondary: "#111827",
          card: "#1E293B",
          hover: "#243044",
          border: "#2D3748",
        },
        // CARE dimension accent colors
        care: {
          c: "#6366F1",    // Computational Intelligence – Indigo
          "c-light": "#818CF8",
          a: "#10B981",    // Accuracy – Emerald
          "a-light": "#34D399",
          r: "#F59E0B",    // Reliability – Amber
          "r-light": "#FCD34D",
          e: "#3B82F6",    // Economics – Blue
          "e-light": "#60A5FA",
          score: "#8B5CF6", // Overall CARE score – Purple
        },
        // Status colors
        status: {
          production: "#10B981",
          pilot: "#3B82F6",
          improve: "#F59E0B",
          notRecommended: "#EF4444",
        },
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "score-fill": "scoreFill 1.5s ease-out forwards",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(8px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        scoreFill: {
          "0%": { "stroke-dashoffset": "283" },
          "100%": { "stroke-dashoffset": "var(--target-offset)" },
        },
      },
      boxShadow: {
        card: "0 4px 24px rgba(0,0,0,0.3)",
        glow: "0 0 20px rgba(99, 102, 241, 0.3)",
        "glow-green": "0 0 20px rgba(16, 185, 129, 0.3)",
        "glow-amber": "0 0 20px rgba(245, 158, 11, 0.3)",
      },
    },
  },
  plugins: [],
}
