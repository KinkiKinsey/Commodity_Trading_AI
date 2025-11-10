"use client";

import { useMemo } from "react";
import clsx from "clsx";

import type { OverlayDataPoint } from "@/lib/utils/oilFactors";

type FactorsSidebarSectionProps = {
  title: string;
  accent: string;
  items: OverlayDataPoint[];
  emptyLabel: string;
};

function formatValue(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function FactorsSidebarSection({ title, accent, items, emptyLabel }: FactorsSidebarSectionProps) {
  if (!items.length) {
    return (
      <div className="flex flex-col gap-2 rounded-xl border border-slate-200 bg-white/70 px-4 py-5">
        <div className="text-sm font-semibold text-slate-700">{title}</div>
        <p className="text-xs text-slate-500">{emptyLabel}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white/80 px-4 py-5">
      <div className="flex items-center gap-2">
        <span className="inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: accent }} />
        <span className="text-sm font-semibold text-slate-700">{title}</span>
      </div>

      <div className="flex flex-col gap-3">
        {items.map((item) => (
          <div
            key={`${item.time}-${item.factor}-${item.value}`}
            className={clsx(
              "rounded-lg border px-3 py-2 text-xs",
              "border-slate-200 bg-white/90 shadow-[0_6px_18px_rgba(15,23,42,0.06)]"
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-slate-900">{item.factor || "Factor"}</p>
              <span className="rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                {formatValue(item.value)}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
              <span>{formatDate(item.time)}</span>
              <span>{item.label}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export type OilFactorsSidebarProps = {
  micro: OverlayDataPoint[];
  macro: OverlayDataPoint[];
  className?: string;
};

export function OilFactorsSidebar({ micro, macro, className }: OilFactorsSidebarProps) {
  const sortedMicro = useMemo(
    () => [...micro].sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 10),
    [micro]
  );
  const sortedMacro = useMemo(
    () => [...macro].sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 10),
    [macro]
  );

  return (
    <aside className={clsx("flex flex-col gap-4", className)}>
      <FactorsSidebarSection
        title="Micro Factors"
        accent="#ff7f0e"
        items={sortedMicro}
        emptyLabel="尚未获取到 micro 因子"
      />
      <FactorsSidebarSection
        title="Macro Factors"
        accent="#003366"
        items={sortedMacro}
        emptyLabel="尚未获取到 macro 因子"
      />
    </aside>
  );
}
