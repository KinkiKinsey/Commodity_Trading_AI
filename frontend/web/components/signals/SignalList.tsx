"use client";

import clsx from "clsx";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";
import { SignalBadge } from "./SignalBadge";

type SignalListProps = {
  signals: IndexSignal[];
  isLoading: boolean;
  error?: string;
  locale: "zh-CN" | "en-US";
  t: (key: string) => string;
  onSelect?: (signal: IndexSignal) => void;
  className?: string;
};

export function SignalList({ signals, isLoading, error, locale, t, onSelect, className }: SignalListProps) {
  if (isLoading) {
    return (
      <div className={clsx("mt-4 flex flex-col gap-2", className)}>
        {Array.from({ length: 5 }).map((_, index) => (
          <div
            key={index}
            className="h-16 w-full animate-pulse rounded-xl border border-border-muted bg-bg-alt/60"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={clsx("mt-4 rounded-xl border border-accent-bear/40 bg-accent-bear/10 px-4 py-4 text-sm text-accent-bear", className)}>
        {error || t("signals.error")}
      </div>
    );
  }

  if (!signals.length) {
    return (
      <div className={clsx("mt-4 rounded-xl border border-border-muted px-4 py-5 text-sm text-text-secondary", className)}>
        {t("empty.signals")}
      </div>
    );
  }

  const sortedSignals = [...signals].sort(
    (left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime()
  );

  return (
    <div className={clsx("mt-4 flex flex-col gap-2", className)}>
      {sortedSignals.slice(0, 8).map((signal) => (
        <SignalBadge
          key={signal.signalId}
          signal={signal}
          locale={locale}
          onClick={onSelect}
        />
      ))}
      {signals.length > 8 ? (
        <p className="text-[11px] text-text-tertiary">
          {locale === "zh-CN"
            ? `已显示最近 8 条信号，共 ${signals.length} 条`
            : `Showing latest 8 of ${signals.length} signals`}
        </p>
      ) : null}
    </div>
  );
}

