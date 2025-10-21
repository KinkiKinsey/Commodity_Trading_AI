"use client";

import clsx from "clsx";

type SentimentDialProps = {
  direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  className?: string;
};

const DIRECTION_COLORS: Record<SentimentDialProps["direction"], string> = {
  bullish: "#00B2A9",
  bearish: "#FF5C5C",
  neutral: "#F0A500"
};

const DIRECTION_LABELS: Record<SentimentDialProps["direction"], string> = {
  bullish: "利多",
  bearish: "利空",
  neutral: "中性"
};

export function SentimentDial({ direction, confidence, className }: SentimentDialProps) {
  const pct = Math.round(confidence * 100);
  const sweep = Math.min(270, Math.max(0, confidence * 270));
  const gradient = `conic-gradient(${DIRECTION_COLORS[direction]} ${sweep}deg, rgba(255,255,255,0.08) ${sweep}deg 270deg, transparent 270deg)`;

  return (
    <div
      className={clsx(
        "flex flex-col items-center gap-4 rounded-[18px] border-2 border-border-strong bg-bg-surface p-6 shadow-[6px_6px_0px_rgba(0,0,0,0.85)]",
        className
      )}
    >
      <div className="terminal-text text-[11px] uppercase tracking-[0.3em] text-border-strong">Sentiment</div>
      <div className="relative flex h-40 w-40 items-center justify-center">
        <div
          className="absolute inset-0 rounded-full border-2 border-border-strong"
          style={{ background: gradient }}
          aria-hidden
        />
        <div className="absolute inset-[18%] rounded-full border-2 border-border-strong bg-white" />
        <div className="relative flex flex-col items-center text-center">
          <span
            className={clsx(
              "terminal-text text-xs uppercase tracking-[0.25em]",
              direction === "bullish" && "text-accent-bull",
              direction === "bearish" && "text-accent-bear",
              direction === "neutral" && "text-accent-neutral"
            )}
          >
            {DIRECTION_LABELS[direction]}
          </span>
          <span className="text-3xl font-semibold text-border-strong">{pct}%</span>
          <span className="text-[10px] text-text-secondary">Confidence</span>
        </div>
      </div>
    </div>
  );
}
