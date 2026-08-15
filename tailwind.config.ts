import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#14161f",
        surface: "#1c1f2b",
        "surface-2": "#262a3a",
        "surface-3": "#313650",
        border: "#333849",
        "border-soft": "#262a38",
        ink: "#ecedf3",
        "ink-muted": "#8b8fa3",
        "ink-faint": "#5c6178",
        primary: "#7c6ff0",
        "primary-hover": "#6c5ce0",
        glm: "#4fd1c5",
        kimi: "#f2a65a",
        danger: "#f1667a",
        success: "#5fd68c",
        warning: "#f2c94c",
      },
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        body: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        control: "10px",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        blink: { "50%": { opacity: "0" } },
        "fade-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pop-in": {
          from: { opacity: "0", transform: "scale(0.97)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s linear infinite",
        blink: "blink 1s step-start infinite",
        "fade-up": "fade-up 320ms cubic-bezier(0.23,1,0.32,1) both",
        "pop-in": "pop-in 180ms cubic-bezier(0.23,1,0.32,1) both",
      },
    },
  },
  plugins: [],
} satisfies Config;
