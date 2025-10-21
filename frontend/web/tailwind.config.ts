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
        "bg-primary": "#FFFFFF",
        "bg-surface": "#FFFFFF",
        "accent-bull": "#1A8B6D",
        "accent-bear": "#E23B3B",
        "accent-neutral": "#FFB400",
        "text-primary": "#111111",
        "text-secondary": "#4C4C4C",
        "border-strong": "#0F0F0F",
        "accent-blue": "#2F5FFF",
        "accent-purple": "#7B61FF"
      }
    }
  },
  plugins: []
};

export default config;
