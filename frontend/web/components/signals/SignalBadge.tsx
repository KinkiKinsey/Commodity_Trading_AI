"use client";

import clsx from "clsx";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";

type SignalBadgeProps = {
  signal: IndexSignal;
  locale: "zh-CN" | "en-US";
  onClick?: (signal: IndexSignal) => void;
  className?: string;
};

const TYPE_LABELS: Record<"zh-CN" | "en-US", Record<IndexSignal["signalType"], string>> = {
  "zh-CN": {
    buy: "买入信号",
    sell: "卖出信号"
  },
  "en-US": {
    buy: "Buy Signal",
    sell: "Sell Signal"
  }
};

export function SignalBadge({ signal, locale, onClick, className }: SignalBadgeProps) {
  const typeLabel = TYPE_LABELS[locale][signal.signalType];
  const reasonLabel = signal.reasonTag ?? (locale === "zh-CN" ? "AI 推理" : "AI Insight");
  const timestampLabel = formatTime(signal.createdAt, locale);

  return (
    <button
      type="button"
      onClick={onClick ? () => onClick(signal) : undefined}
      className={clsx(
        "group flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left shadow-[0_4px_12px_rgba(15,23,42,0.08)] transition",
        signal.signalType === "buy"
          ? "border-accent-bull/60 bg-accent-bull/6 hover:-translate-y-0.5 hover:border-accent-bull"
          : "border-accent-bear/60 bg-accent-bear/6 hover:-translate-y-0.5 hover:border-accent-bear",
        className
      )}
    >
      <div className="flex min-w-0 items-center gap-3">
        <span
          className={clsx(
            "flex h-10 w-10 items-center justify-center rounded-full border text-white shadow-[0_6px_16px_rgba(15,23,42,0.18)]",
            signal.signalType === "buy"
              ? "border-accent-bull bg-accent-bull"
              : "border-accent-bear bg-accent-bear"
          )}
        >
          {signal.signalType === "buy" ? (
            <ArrowUpRight size={18} strokeWidth={2.5} />
          ) : (
            <ArrowDownRight size={18} strokeWidth={2.5} />
          )}
        </span>
        <div className="min-w-0">
          <p className="terminal-text text-[11px] uppercase tracking-[0.2em] text-text-secondary">
            {typeLabel}
          </p>
          <p className="truncate text-sm font-semibold text-text-primary">
            {reasonLabel}
            {signal.indexValue !== undefined ? ` · ${signal.indexValue.toFixed(2)}` : ""}
          </p>
        </div>
      </div>
      <div className="flex flex-col items-end gap-1 text-xs tabular-nums text-text-secondary">
        <span className="font-semibold text-text-primary">
          {signal.price.toFixed(2)}
        </span>
        <span>{timestampLabel}</span>
      </div>
    </button>
  );
}

function formatTime(timestamp: string, locale: "zh-CN" | "en-US") {
  try {
    return new Intl.DateTimeFormat(locale, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    }).format(new Date(timestamp));
  } catch {
    return timestamp;
  }
}

