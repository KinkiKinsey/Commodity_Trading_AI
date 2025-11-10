"use client";

import clsx from "clsx";
import { useMemo } from "react";

import type { CtpSignal } from "@/lib/hooks/useCtpKline";

type CtpSignalTimelineProps = {
  signals: CtpSignal[];
};

const timeFormatter = new Intl.DateTimeFormat(undefined, {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit"
});

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  month: "2-digit",
  day: "2-digit"
});

export function CtpSignalTimeline({ signals }: CtpSignalTimelineProps) {
  const sortedSignals = useMemo(
    () =>
      [...signals].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 8),
    [signals]
  );

  if (!sortedSignals.length) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-border-muted bg-white/90 p-4 shadow-sm">
      <header className="flex items-center justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-text-secondary">Signal Timeline</p>
          <h4 className="text-base font-semibold text-text-primary">MLMA Crossovers</h4>
        </div>
        <span className="text-[11px] text-text-tertiary">{`${signals.length} total`}</span>
      </header>

      <ol className="mt-4 space-y-3">
        {sortedSignals.map((signal) => {
          const timestamp = new Date(signal.timestamp);
          const isBuy = signal.signal_type === "buy";
          return (
            <li
              key={signal.signal_id}
              className="flex items-center justify-between gap-3 rounded-xl border border-border-muted px-3 py-2 text-sm"
            >
              <div className="flex items-center gap-3">
                <span
                  className={clsx(
                    "rounded-full px-2 py-[2px] text-[11px] font-semibold uppercase tracking-[0.18em]",
                    isBuy ? "bg-accent-bull/10 text-accent-bull" : "bg-accent-bear/10 text-accent-bear"
                  )}
                >
                  {isBuy ? "BUY" : "SELL"}
                </span>
                <div>
                  <p className="text-xs text-text-secondary">
                    {dateFormatter.format(timestamp)} · {timeFormatter.format(timestamp)}
                  </p>
                  <p className="text-sm font-semibold text-text-primary">
                    {signal.description ?? (isBuy ? "Price crossed above MLMA" : "Price crossed below MLMA")}
                  </p>
                </div>
              </div>
              <div className="text-right text-xs text-text-secondary">
                <p className="font-semibold text-text-primary">${signal.price.toFixed(2)}</p>
                {typeof signal.confidence === "number" ? (
                  <p>{Math.round(signal.confidence * 100)}% conf.</p>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
