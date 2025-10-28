"use client";

import clsx from "clsx";
import { Clock, TrendingDown, TrendingUp } from "lucide-react";
import type { NewsStreamEvent } from "@/lib/state/newsStreamStore";

type NewsCardProps = {
  event: NewsStreamEvent;
  directionLabels: Record<NewsStreamEvent["direction"], string>;
  locale: string;
  t: (key: string) => string;
  onSelect?: (event: NewsStreamEvent) => void;
};

/**
 * Bloomberg-styled news card with accessible keyboard handling
 * and live data friendly layout.
 */
export function NewsCard({ event, directionLabels, locale, t, onSelect }: NewsCardProps) {
  const isBullish = event.direction === "bullish";
  const isBearish = event.direction === "bearish";
  const confidencePercent = Math.round((event.confidence ?? 0) * 100);
  const confidenceLabel =
    locale === "zh-CN" ? `置信度 ${confidencePercent}%` : `Confidence ${confidencePercent}%`;
  const relativeTime = formatRelativeTime(event.timestamp, locale);

  const handleActivate = () => {
    onSelect?.(event);
  };

  return (
    <article
      className="flex cursor-pointer flex-col gap-3 rounded-xl border border-border-muted bg-white px-4 py-4 shadow-[0_6px_18px_rgba(15,23,42,0.08)] transition hover:-translate-y-1 hover:border-border-active hover:shadow-[0_12px_28px_rgba(15,23,42,0.16)]"
      onClick={handleActivate}
      onKeyDown={(keyboardEvent) => {
        if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
          keyboardEvent.preventDefault();
          handleActivate();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label={event.headline}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={clsx(
            "terminal-text rounded-full border px-3 py-0.5 text-[10px] uppercase tracking-[0.18em]",
            isBullish && "border-accent-bull text-accent-bull",
            isBearish && "border-accent-bear text-accent-bear",
            !isBullish && !isBearish && "border-accent-neutral text-accent-neutral/80"
          )}
        >
          {directionLabels[event.direction]}
        </span>
        <span className="inline-flex items-center gap-1 text-[11px] text-text-tertiary">
          <Clock size={12} aria-hidden />
          <time dateTime={event.timestamp}>{relativeTime}</time>
        </span>
        {event.signalTags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="rounded-md border border-border-muted bg-background-tertiary px-2 py-0.5 text-[11px] uppercase tracking-[0.18em] text-text-secondary"
          >
            #{tag}
          </span>
        ))}
      </div>

      <h3 className="text-base font-semibold leading-snug text-text-primary">{event.headline}</h3>
      <p className="text-sm leading-relaxed text-text-secondary">
        {event.summary ?? t("modal.summaryFallback")}
      </p>

      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        <div
          className={clsx(
            "inline-flex items-center gap-2 font-medium",
            isBullish && "text-market-positive",
            isBearish && "text-market-negative",
            !isBullish && !isBearish && "text-text-secondary"
          )}
        >
          {isBullish ? <TrendingUp size={16} aria-hidden /> : null}
          {isBearish ? <TrendingDown size={16} aria-hidden /> : null}
          <span>{directionLabels[event.direction]}</span>
        </div>

        <div className="flex items-center gap-2 text-xs text-text-tertiary">
          <span className="terminal-text text-[10px] uppercase tracking-[0.2em]">
            {confidenceLabel}
          </span>
        </div>
      </div>

      {event.signal ? (
        <div className="rounded-lg border border-border-muted/60 bg-background-tertiary/50 px-3 py-2 text-xs text-text-secondary">
          <span className="font-medium uppercase tracking-[0.18em] text-text-tertiary">
            {locale === "zh-CN" ? "信号" : "Signal"}
          </span>
          <span className="mx-2 inline-flex items-center gap-1">
            <strong className="font-semibold text-text-primary">
              {event.signal.signalType.toUpperCase()}
            </strong>
            @ {event.signal.price.toFixed(2)}
          </span>
          {event.signal.reasonTag ? (
            <span className="rounded px-2 py-1 text-[11px] uppercase tracking-[0.18em] text-text-tertiary">
              #{event.signal.reasonTag}
            </span>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function formatRelativeTime(timestamp: string, locale: string): string {
  const target = new Date(timestamp);
  if (Number.isNaN(target.getTime())) {
    return timestamp;
  }

  const diffMs = Date.now() - target.getTime();
  const diffMinutes = Math.floor(diffMs / (60 * 1000));

  if (diffMinutes < 1) {
    return locale === "zh-CN" ? "刚刚" : "Just now";
  }
  if (diffMinutes < 60) {
    return locale === "zh-CN" ? `${diffMinutes} 分钟前` : `${diffMinutes} min ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return locale === "zh-CN" ? `${diffHours} 小时前` : `${diffHours} hr ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) {
    return locale === "zh-CN" ? `${diffDays} 天前` : `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  }

  return new Intl.DateTimeFormat(locale === "zh-CN" ? "zh-CN" : "en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(target);
}

