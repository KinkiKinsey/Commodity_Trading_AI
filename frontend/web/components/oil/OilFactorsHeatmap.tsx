"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";

import type { OilFactorRecord } from "@/lib/api/oilFactors";
import { formatInterval, isMacroScope, isMicroScope } from "@/lib/utils/oilFactors";

type TreemapEntry = {
  interval: string;
  weightedMean: number;
  weightedVariance?: number;
  riskReward?: number;
  durationDays?: number;
  driverType?: string;
  aiReason?: string;
  startDate?: string;
  endDate?: string;
  trendCount?: number;
};

type TreemapNode = {
  id: string;
  factor: string;
  scope: string;
  weightedMean: number;
  areaWeight: number;
  avgVariance?: number;
  avgRiskReward?: number;
  avgDuration?: number;
  avgTrendCount?: number;
  drivers: string[];
  entries: TreemapEntry[];
};

type LayoutItem = TreemapNode & {
  x: number;
  y: number;
  width: number;
  height: number;
};

type OilFactorsHeatmapProps = {
  factors: OilFactorRecord[];
};

const POSITIVE_COLOR = "#13855f";
const NEGATIVE_COLOR = "#b3222d";
const POSITIVE_BORDER = "#0d5c43";
const NEGATIVE_BORDER = "#821821";

function toPercent(value?: number | null): number {
  if (value === undefined || value === null || Number.isNaN(value)) return 0;
  return value * 100;
}

function formatNumber(value?: number | null, digits = 2, suffix = ""): string | null {
  if (value === undefined || value === null || Number.isNaN(value)) return null;
  return `${value.toFixed(digits)}${suffix}`;
}

function cleanAiReason(reason?: string | null): string | null {
  if (!reason) return null;
  const trimmed = reason.trim();
  if (!trimmed) return null;
  let result = trimmed;
  const pairs: Array<{ open: string; close: string }> = [
    { open: "(", close: ")" },
    { open: "[", close: "]" },
    { open: "{", close: "}" },
    { open: "\uFF08", close: "\uFF09" }, // full-width parentheses
    { open: "\u3010", close: "\u3011" } // full-width brackets
  ];
  for (const { open, close } of pairs) {
    if (result.startsWith(open)) {
      const closingIndex = result.indexOf(close);
      if (closingIndex > 0) {
        result = result.slice(closingIndex + 1).trimStart();
      }
      break;
    }
  }
  return result || trimmed;
}

function buildNodes(records: OilFactorRecord[]): TreemapNode[] {
  const groups = new Map<
    string,
    {
      factor: string;
      scope: string;
      totalImpact: number;
      totalWeightedMean: number;
      sumVariance: number;
      varianceCount: number;
      sumRisk: number;
      riskCount: number;
      sumDuration: number;
      durationCount: number;
      sumTrend: number;
      trendSamples: number;
      drivers: Set<string>;
      entries: TreemapEntry[];
    }
  >();

  records.forEach((record) => {
    const percent = toPercent(record.weighted_mean);
    const impact = Math.abs(percent);
    if (impact <= 0) return;

    const factor = record.factor?.trim() || "Unknown factor";
    const scopeRaw = record.scope?.trim() ?? "unknown";
    const scope = isMicroScope(scopeRaw) ? "Micro" : isMacroScope(scopeRaw) ? "Macro" : scopeRaw;
    const key = `${scope}::${factor}`;

    const entry: TreemapEntry = {
      interval: formatInterval(record),
      weightedMean: percent,
      weightedVariance: record.weighted_variance ?? undefined,
      riskReward: record.risk_reward_ratio ?? undefined,
      durationDays: record.duration_days ?? record.average_duration ?? undefined,
      driverType: record.driver_type ?? undefined,
      aiReason: cleanAiReason(record.AI_Reason) ?? undefined,
      startDate: record.start_date ?? undefined,
      endDate: record.end_date ?? undefined,
      trendCount: record.trend_count ?? undefined
    };

    const group = groups.get(key);
    if (group) {
      group.totalImpact += impact;
      group.totalWeightedMean += percent;
      group.entries.push(entry);
      group.sumVariance += entry.weightedVariance ?? 0;
      group.varianceCount += entry.weightedVariance !== undefined ? 1 : 0;
      group.sumRisk += entry.riskReward ?? 0;
      group.riskCount += entry.riskReward !== undefined ? 1 : 0;
      group.sumDuration += entry.durationDays ?? 0;
      group.durationCount += entry.durationDays !== undefined ? 1 : 0;
      group.sumTrend += entry.trendCount ?? 0;
      group.trendSamples += entry.trendCount !== undefined ? 1 : 0;
      if (entry.driverType) group.drivers.add(entry.driverType);
    } else {
      const drivers = new Set<string>();
      if (entry.driverType) drivers.add(entry.driverType);
      groups.set(key, {
        factor,
        scope,
        totalImpact: impact,
        totalWeightedMean: percent,
        sumVariance: entry.weightedVariance ?? 0,
        varianceCount: entry.weightedVariance !== undefined ? 1 : 0,
        sumRisk: entry.riskReward ?? 0,
        riskCount: entry.riskReward !== undefined ? 1 : 0,
        sumDuration: entry.durationDays ?? 0,
        durationCount: entry.durationDays !== undefined ? 1 : 0,
        sumTrend: entry.trendCount ?? 0,
        trendSamples: entry.trendCount !== undefined ? 1 : 0,
        drivers,
        entries: [entry]
      });
    }
  });

  const nodes = Array.from(groups.entries()).map(([key, group]) => {
    const mean = group.totalWeightedMean / group.entries.length;
    return {
      id: key,
      factor: group.factor,
      scope: group.scope,
      weightedMean: mean,
      areaWeight: group.totalImpact,
      avgVariance: group.varianceCount ? group.sumVariance / group.varianceCount : undefined,
      avgRiskReward: group.riskCount ? group.sumRisk / group.riskCount : undefined,
      avgDuration: group.durationCount ? group.sumDuration / group.durationCount : undefined,
      avgTrendCount: group.trendSamples ? group.sumTrend / group.trendSamples : undefined,
      drivers: Array.from(group.drivers),
      entries: group.entries
    } satisfies TreemapNode;
  });

  const impacts = nodes.map((node) => node.areaWeight);
  if (!impacts.length) return [];
  const maxImpact = Math.max(...impacts);
  const minImpact = Math.min(...impacts);
  const range = maxImpact - minImpact || 1;

  return nodes.map((node) => {
    const normalized = Math.min(1, Math.max(0, (node.areaWeight - minImpact) / range));
    const scaled = 0.4 + 0.6 * normalized;
    return {
      ...node,
      areaWeight: scaled * maxImpact
    } satisfies TreemapNode;
  });
}

function computeLayout(nodes: TreemapNode[], width: number, height: number): LayoutItem[] {
  if (!nodes.length || width <= 0 || height <= 0) return [];
  const totalWeight = nodes.reduce((sum, node) => sum + node.areaWeight, 0);
  if (totalWeight === 0) return [];

  const items = nodes
    .map((node) => ({
      ...node,
      area: (node.areaWeight / totalWeight) * width * height
    }))
    .sort((a, b) => b.area - a.area);

  const result: LayoutItem[] = [];
  const frame = { x: 0, y: 0, width, height };
  let orientation: "horizontal" | "vertical" = width >= height ? "horizontal" : "vertical";
  let row: typeof items = [];
  const remaining = [...items];

  const rowArea = (rowItems: typeof items) => rowItems.reduce((sum, item) => sum + item.area, 0);
  const worstAspect = (rowItems: typeof items, length: number, rowSum: number) => {
    if (!rowItems.length || length <= 0 || rowSum === 0) return Number.POSITIVE_INFINITY;
    const maxArea = Math.max(...rowItems.map((item) => item.area));
    const minArea = Math.min(...rowItems.map((item) => item.area));
    const lenSquared = length * length;
    return Math.max((lenSquared * maxArea) / (rowSum * rowSum), (rowSum * rowSum) / (lenSquared * minArea));
  };

  const placeRow = (rowItems: typeof items, rect: typeof frame, horizontal: boolean) => {
    const sum = rowArea(rowItems);
    if (sum === 0) return;
    if (horizontal) {
      const rowHeight = sum / rect.width;
      let cursor = rect.x;
      rowItems.forEach((item) => {
        const itemWidth = item.area / rowHeight;
        result.push({ ...item, x: cursor, y: rect.y, width: itemWidth, height: rowHeight });
        cursor += itemWidth;
      });
      rect.y += rowHeight;
      rect.height -= rowHeight;
    } else {
      const rowWidth = sum / rect.height;
      let cursor = rect.y;
      rowItems.forEach((item) => {
        const itemHeight = item.area / rowWidth;
        result.push({ ...item, x: rect.x, y: cursor, width: rowWidth, height: itemHeight });
        cursor += itemHeight;
      });
      rect.x += rowWidth;
      rect.width -= rowWidth;
    }
  };

  while (remaining.length) {
    const candidate = remaining[0]!;
    const length = orientation === "horizontal" ? frame.height : frame.width;
    const currentSum = rowArea(row);
    const currentWorst = row.length ? worstAspect(row, length, currentSum) : Number.POSITIVE_INFINITY;
    const newRow = [...row, candidate];
    const newWorst = worstAspect(newRow, length, currentSum + candidate.area);
    if (newWorst <= currentWorst) {
      row.push(candidate);
      remaining.shift();
    } else {
      placeRow(row, frame, orientation === "horizontal");
      orientation = orientation === "horizontal" ? "vertical" : "horizontal";
      row = [];
    }
  }

  if (row.length) {
    placeRow(row, frame, orientation === "horizontal");
  }

  return result;
}

export function OilFactorsHeatmap({ factors }: OilFactorsHeatmapProps) {
  const nodes = useMemo(() => buildNodes(factors), [factors]);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [containerSize, setContainerSize] = useState<{ width: number; height: number }>({ width: 0, height: 0 });
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [hoverPos, setHoverPos] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      if (!entry) return;
      setContainerSize({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const layout = useMemo(() => {
    if (!containerSize.width || !containerSize.height) return [] as LayoutItem[];
    return computeLayout(nodes, containerSize.width, containerSize.height);
  }, [containerSize, nodes]);

  const hoveredNode = hoveredId ? layout.find((item) => item.id === hoveredId) ?? null : null;

  if (!nodes.length) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white/90 px-5 py-6 text-sm text-slate-500 shadow-[0_18px_32px_rgba(15,23,42,0.1)]">
        No factor data available yet.
      </div>
    );
  }

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className="relative h-[72vh] min-h-[460px] w-full overflow-hidden rounded-[22px] border border-slate-900/40 bg-[#0d1720] shadow-[0_30px_80px_rgba(3,7,9,0.65)]"

      >
        {layout.map((item) => {
          const positive = item.weightedMean >= 0;
          const background = positive ? POSITIVE_COLOR : NEGATIVE_COLOR;
          const borderColor = positive ? POSITIVE_BORDER : NEGATIVE_BORDER;
          return (
            <div
              key={item.id}
              className={clsx(
                "group absolute flex cursor-pointer flex-col justify-between rounded-lg border px-3 py-3 text-left",
                "transition-transform duration-150 ease-out hover:-translate-y-[1px] hover:shadow-[0_12px_28px_rgba(0,0,0,0.35)]"
              )}
              style={{
                left: `${item.x}px`,
                top: `${item.y}px`,
                width: `${Math.max(item.width, 0)}px`,
                height: `${Math.max(item.height, 0)}px`,
                backgroundColor: background,
                borderColor
              }}
              onMouseEnter={(event) => {
                const rect = event.currentTarget.getBoundingClientRect();
                const containerRect = containerRef.current?.getBoundingClientRect();
                if (containerRect) {
                  setHoverPos({
                    x: rect.left - containerRect.left + rect.width / 2,
                    y: rect.top - containerRect.top + rect.height / 2
                  });
                }
                setHoveredId(item.id);
              }}
              onMouseLeave={() => {
                setHoveredId(null);
                setHoverPos(null);
              }}
            >
              <div className="text-[12px] font-semibold tracking-[0.02em] text-white drop-shadow-[0_1px_1px_rgba(0,0,0,0.6)]">
                <span className="block break-words leading-tight">{item.factor}</span>
              </div>
              <div className="pb-1 text-lg font-bold tracking-[0.02em] text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.65)]">
                {item.weightedMean >= 0 ? "+" : ""}
                {item.weightedMean.toFixed(2)}%
              </div>
            </div>
          );
        })}

        {hoveredNode && hoverPos ? (
          (() => {
            const TOOLTIP_WIDTH = 520;
            const TOOLTIP_HEIGHT = 480;
            const left = Math.max(
              16,
              Math.min(containerSize.width - TOOLTIP_WIDTH - 16, hoverPos.x - TOOLTIP_WIDTH / 2)
            );
            const top = Math.max(
              16,
              Math.min(containerSize.height - TOOLTIP_HEIGHT - 16, hoverPos.y - TOOLTIP_HEIGHT - 20)
            );
            return (
              <div
                className="pointer-events-none absolute z-30 rounded-2xl border border-slate-200 bg-white px-6 py-5 text-xs text-slate-700 shadow-[0_30px_70px_rgba(15,23,42,0.45)]"
                style={{
                  width: TOOLTIP_WIDTH,
                  height: TOOLTIP_HEIGHT,
                  left,
                  top
                }}
              >
                <div className="flex items-center justify-between gap-3 text-[11px] text-slate-500">
                  <span>{hoveredNode.scope}</span>
                  <span>
                    {hoveredNode.weightedMean >= 0 ? "+" : ""}
                    {hoveredNode.weightedMean.toFixed(2)}%
                  </span>
                </div>
                <p className="mt-1 text-base font-semibold text-slate-900">{hoveredNode.factor}</p>

                <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[11px] text-slate-600">
                  <TooltipField label="Variance" value={formatNumber(hoveredNode.avgVariance, 4)} />
                  <TooltipField label="Risk / Reward" value={formatNumber(hoveredNode.avgRiskReward, 3)} />
                  <TooltipField label="Average Duration" value={formatNumber(hoveredNode.avgDuration, 1, " days")} />
                  <TooltipField label="Trend Count" value={formatNumber(hoveredNode.avgTrendCount, 0)} />
                  <TooltipField
                    label="Drivers"
                    value={hoveredNode.drivers.length ? hoveredNode.drivers.join(" / ") : null}
                    isFull
                  />
                </div>

                <div className="mt-3 space-y-2">
                  {hoveredNode.entries.map((entry, index) => {
                    const range = entry.startDate || entry.endDate ? `${entry.startDate ?? "--"} to ${entry.endDate ?? "--"}` : null;
                    return (
                      <div
                        key={`${hoveredNode.id}-${index}`}
                        className="rounded-lg border border-slate-200/70 bg-slate-50 px-3 py-2 shadow-sm"
                      >
                        <div className="flex items-center justify-between text-[11px] text-slate-500">
                          <span>{entry.interval}</span>
                          <span>
                            {entry.weightedMean >= 0 ? "+" : ""}
                            {entry.weightedMean.toFixed(2)}%
                          </span>
                        </div>
                        <TooltipField label="Duration" value={formatNumber(entry.durationDays, 0, " days")} />
                        <TooltipField label="Driver" value={entry.driverType ?? null} />
                        <TooltipField label="Date Range" value={range} isFull />
                        {entry.aiReason ? (
                          <p className="mt-1 text-[11px] leading-snug text-slate-600">
                            <span className="font-semibold text-slate-500">(AI Analysis)</span>
                            <span className="ml-1 text-slate-600">{entry.aiReason}</span>
                          </p>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })()
        ) : null}
      </div>
    </div>
  );
}

type TooltipFieldProps = {
  label: string;
  value: string | null | undefined;
  isFull?: boolean;
};

function TooltipField({ label, value, isFull = false }: TooltipFieldProps) {
  if (!value) return null;
  if (isFull) {
    return (
      <div className="col-span-2 text-[11px] text-slate-600">
        <span className="font-semibold text-slate-500">{label}:</span>
        <span className="ml-1 text-slate-700">{value}</span>
      </div>
    );
  }
  return (
    <div className="flex items-center justify-between gap-2 text-[11px] text-slate-600">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-700">{value}</span>
    </div>
  );
}



