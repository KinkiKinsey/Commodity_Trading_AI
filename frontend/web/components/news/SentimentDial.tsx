"use client";

import clsx from "clsx";

type SentimentDialProps = {
  direction: "bullish" | "bearish" | "neutral";
  confidence: number;
  locale?: "zh-CN" | "en-US";
  className?: string;
};

const DIRECTION_COLORS: Record<SentimentDialProps["direction"], string> = {
  bullish: "#00B2A9",
  bearish: "#FF5C5C",
  neutral: "#F0A500"
};

const DIRECTION_LABELS_ZH: Record<SentimentDialProps["direction"], string> = {
  bullish: "看多",
  bearish: "看空",
  neutral: "中性"
};

const DIRECTION_LABELS_EN: Record<SentimentDialProps["direction"], string> = {
  bullish: "Bullish",
  bearish: "Bearish",
  neutral: "Neutral"
};

export function SentimentDial({ direction, confidence, locale = "zh-CN", className }: SentimentDialProps) {
  const bounded = Math.max(0, Math.min(1, confidence));
  const pct = Math.round(bounded * 100);
  const sweep = (pct / 100) * 270;
  const gradient = `conic-gradient(${DIRECTION_COLORS[direction]} ${sweep}deg, rgba(255,255,255,0.06) ${sweep}deg 270deg, transparent 270deg)`;

  const labelMap = locale === "zh-CN" ? DIRECTION_LABELS_ZH : DIRECTION_LABELS_EN;
  const directionLabel = labelMap[direction];
  const confidenceLabel = locale === "zh-CN" ? "置信度" : "Confidence";
  const headingLabel = locale === "zh-CN" ? "情绪指标" : "Sentiment";
  const metaLabel = locale === "zh-CN" ? "AI 推断" : "AI Insight";

  return (
    <div
      className={clsx(
        "flex w-full flex-col items-center gap-4 rounded-xl border border-border-muted bg-white/90 p-5 shadow-[0_8px_18px_rgba(15,23,42,0.12)]",
        className
      )}
    >
      <div className="flex w-full items-center justify-between text-[11px] uppercase tracking-[0.26em] text-text-tertiary">
        <span>{headingLabel}</span>
        <span className="text-text-secondary">{metaLabel}</span>
      </div>
      <div className="relative flex h-36 w-36 items-center justify-center">
        <div className="absolute inset-0 rounded-full border border-border-muted/60" style={{ background: gradient }} aria-hidden />
        <div className="absolute inset-[22%] rounded-full border border-border-muted/40 bg-white" aria-hidden />
        <div className="relative flex flex-col items-center text-center">
          <span
            className={clsx(
              "text-xs font-medium uppercase tracking-[0.24em]",
              direction === "bullish" && "text-accent-bull",
              direction === "bearish" && "text-accent-bear",
              direction === "neutral" && "text-text-secondary"
            )}
          >
            {directionLabel}
          </span>
          <span className="text-3xl font-semibold tabular-nums text-text-primary">{pct}%</span>
          <span className="text-[11px] text-text-secondary">{confidenceLabel}</span>
        </div>
      </div>
    </div>
  );
}
