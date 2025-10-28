import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "bg-base": "#FFFFFF",
        "bg-primary": "#FFFFFF",
        "bg-panel": "#FFFFFF",
        "bg-alt": "#F5F7FA",
        "border-muted": "#E3E5E8",
        "border-strong": "#0F0F0F",
        "border-active": "#2F5FFF",
        "text-primary": "#0A0C10",
        "text-secondary": "#4C4C4C",
        "accent-neutral": "#2F5FFF",
        "accent-bull": "#1A8B6D",
        "accent-bear": "#E23B3B",
        "state-warning": "#FFB400",
        "shadow-soft": "rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
