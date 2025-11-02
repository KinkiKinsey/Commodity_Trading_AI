"use client";

import clsx from "clsx";
import { useIntl, type TranslationKey } from "@/lib/i18n/IntlContext";

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

const DIRECTION_KEY_MAP: Record<SentimentDialProps["direction"], TranslationKey> = {
  bullish: "sentiment.direction.bullish",
  bearish: "sentiment.direction.bearish",
  neutral: "sentiment.direction.neutral"
};

export function SentimentDial({ direction, confidence, className }: SentimentDialProps) {
  const { t } = useIntl();

  const bounded = Math.max(0, Math.min(1, confidence));
  const pct = Math.round(bounded * 100);
  const sweep = (pct / 100) * 270;
  const gradient = `conic-gradient(${DIRECTION_COLORS[direction]} ${sweep}deg, rgba(255,255,255,0.06) ${sweep}deg 270deg, transparent 270deg)`;

  const directionLabel = t(DIRECTION_KEY_MAP[direction]);
  const confidenceLabel = t("sentiment.confidence");
  const headingLabel = t("sentiment.heading");
  const metaLabel = t("sentiment.meta");

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
