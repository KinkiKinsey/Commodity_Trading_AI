"use client";

import clsx from "clsx";

import type { CtpIndicatorDefinition } from "@/lib/hooks/useCtpKline";

type CtpIndicatorPanelProps = {
  indicators: CtpIndicatorDefinition[];
  selection: Record<string, boolean | undefined>;
  onToggle: (key: string) => void;
  supportedMap?: Record<string, boolean>;
};

export function CtpIndicatorPanel({ indicators, selection, onToggle, supportedMap }: CtpIndicatorPanelProps) {
  if (!indicators.length) {
    return null;
  }

  const activeCount = indicators.reduce((count, indicator) => count + (selection[indicator.key.toUpperCase()] ? 1 : 0), 0);

  return (
    <section className="rounded-2xl border border-border-muted bg-white/90 p-4 shadow-sm">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-text-secondary">CTP 指标控件</p>
          <h4 className="text-base font-semibold text-text-primary">Indicator Panel</h4>
        </div>
        <span className="rounded-full bg-bg-alt px-3 py-1 text-xs text-text-secondary">
          {activeCount}/{indicators.length} 已启用
        </span>
      </header>

      <ul className="mt-4 space-y-3">
        {indicators.map((indicator, index) => {
          const normalizedKey = indicator.key.toUpperCase();
          const enabled = selection[normalizedKey] ?? false;
          const isSupported = supportedMap ? Boolean(supportedMap[normalizedKey]) : true;

          return (
            <li
              key={indicator.key}
              className={clsx(
                "rounded-xl border px-3 py-3 text-sm transition",
                enabled ? "border-accent-primary/60 bg-accent-primary/5" : "border-border-muted bg-white",
                !isSupported && "opacity-60"
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-text-primary">{indicator.label}</p>
                  <p className="text-xs uppercase tracking-[0.18em] text-text-tertiary">
                    {indicator.category ?? "general"}
                  </p>
                  <p className="text-[10px] uppercase tracking-[0.3em] text-text-tertiary">#{index + 1}</p>
                </div>
                <button
                  type="button"
                  onClick={() => isSupported && onToggle(normalizedKey)}
                  disabled={!isSupported}
                  className={clsx(
                    "rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em]",
                    enabled
                      ? "border-text-primary bg-text-primary text-white"
                      : "border-border-muted text-text-secondary hover:text-text-primary"
                  )}
                >
                  {!isSupported ? "即将支持" : enabled ? "关闭" : "启用"}
                </button>
              </div>
              {indicator.description ? (
                <p className="mt-2 text-xs text-text-secondary">{indicator.description}</p>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
