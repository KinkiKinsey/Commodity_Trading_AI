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

const AI_REASON_TRANSLATIONS: Record<string, string> = {
  "EIA\u539f\u6cb9\u5e93\u5b58\u610f\u5916\u5927\u5e45\u589e\u52a0730\u4e07\u6876 [\u5b9e\u9645\u53d1\u751f] [\u4f4e\u4e8e\u9884\u671f]": "EIA data showed an unexpected 7.3M bbl crude build [Actual] [Below expectation]",
  "EIA\u62a5\u544a\u539f\u6cb9\u5e93\u5b58\u51cf\u5c111150\u4e07\u6876 [\u4ea4\u4ed8] [\u4f18\u4e8e\u9884\u671f]": "EIA report: crude inventories fell by 11.5M bbl [Delivery] [Above expectation]",
  "EIA\u62a5\u544a\u539f\u6cb9\u5e93\u5b58\u51cf\u5c11200\u4e07\u6876 [DELIVERY] [BETTER_THAN_EXPECTATION]": "EIA report: crude inventories down 2.0M bbl [DELIVERY] [BETTER_THAN_EXPECTATION]",
  "EIA\u62a5\u544a\u539f\u6cb9\u5e93\u5b58\u51cf\u5c11580\u4e07\u6876 [\u4ea4\u4ed8] [\u4f4e\u4e8e\u9884\u671f]": "EIA report: crude inventories decreased 5.8M bbl [Delivery] [Below expectation]",
  "EIA\u62a5\u544a\u539f\u6cb9\u5e93\u5b58\u589e\u52a0460\u4e07\u6876 [DELIVERY] [LESS_THAN_EXPECTATION]": "EIA report: crude inventories rose 4.6M bbl [DELIVERY] [LESS_THAN_EXPECTATION]",
  "EIA\u62a5\u544a\u539f\u6cb9\u5e93\u5b58\u589e\u52a0870\u4e07\u6876 [DELIVERY] [LESS_THAN_EXPECTATION]": "EIA report: crude inventories rose 8.7M bbl [DELIVERY] [LESS_THAN_EXPECTATION]",
  "EIA\u62a5\u544a\u5f15\u53d1\u9700\u6c42\u62c5\u5fe7 [\u4ea4\u4ed8] [\u4f4e\u4e8e\u9884\u671f]": "EIA report triggered demand concerns [Delivery] [Below expectation]",
  "EIA\u6570\u636e\u663e\u793a\u5e93\u5b58\u589e\u52a0 [DELIVERY] [LESS_THAN_EXPECTATION]": "EIA data showed inventories increasing [DELIVERY] [LESS_THAN_EXPECTATION]",
  "OPEC+\u53ef\u80fd\u589e\u4ea7\u8d85\u8fc741.1\u4e07\u6876/\u65e5 [\u9884\u671f] [\u4e0d\u9002\u7528]": "OPEC+ may boost output by over 411k bpd [Expectation] [N/A]",
  "OPEC+\u5ef6\u957f\u51cf\u4ea7\u51b3\u5b9a\u672a\u80fd\u652f\u6491\u5e02\u573a [\u4ea4\u4ed8] [\u4f4e\u4e8e\u9884\u671f]": "OPEC+ extension of cuts failed to support the market [Delivery] [Below expectation]",
  "OPEC+\u8ba1\u5212\u57286\u6708\u589e\u52a0\u4ea7\u91cf [\u9884\u671f] [\u4e0d\u9002\u7528]": "OPEC+ plans to raise output in June [Expectation] [N/A]",
  "OPEC\u4e0b\u8c03\u9700\u6c42\u9884\u6d4b [DELIVERY] [LESS_THAN_EXPECTATION]": "OPEC lowered its demand outlook [DELIVERY] [LESS_THAN_EXPECTATION]",
  "\u4e2d\u4e1c\u5c40\u52bf\u63a8\u52a8\u4ea4\u6613\u5458\u589e\u52a0\u591a\u5934\u5934\u5bf8 [\u9884\u671f] [\u4e0d\u9002\u7528]": "Middle East tensions prompted traders to add long positions [Expectation] [N/A]",
  "\u4e2d\u56fd\u523a\u6fc0\u63aa\u65bd\u53ef\u80fd\u63d0\u632f\u77f3\u6cb9\u9700\u6c42 [EXPECTATION] [N/A]": "China's stimulus measures may lift oil demand [EXPECTATION] [N/A]",
  "\u4e2d\u56fd\u7ecf\u6d4e\u62a5\u544a\u672a\u80fd\u652f\u6491\u77f3\u6cb9\u5e02\u573a [\u4ea4\u4ed8] [\u4f4e\u4e8e\u9884\u671f]": "China's economic reports failed to support the oil market [Delivery] [Below expectation]",
  "\u4e2d\u56fd\u7ecf\u6d4e\u62c5\u5fe7\u5bfc\u81f4\u9700\u6c42\u9884\u671f\u4e0b\u964d [\u9884\u671f] [\u4e0d\u9002\u7528]": "Concerns over China's economy dragged demand expectations lower [Expectation] [N/A]",
  "\u4e2d\u56fd\u9700\u6c42\u75b2\u8f6f\u548c\u7f8e\u8054\u50a8\u5229\u7387\u524d\u666f\u62c5\u5fe7 [\u4ea4\u4ed8] [\u4e0d\u9002\u7528]": "Sluggish Chinese demand and Fed rate outlook stoked worries [Delivery] [N/A]",
  "\u4ee5\u8272\u5217-\u4f0a\u6717\u51b2\u7a81\u7d27\u5f20\u5c40\u52bf\u5347\u7ea7 [\u9884\u671f] [\u4e0d\u9002\u7528]": "Israel-Iran conflict tensions escalated [Expectation] [N/A]",
  "\u4fc4\u7f57\u65af\u5728\u9ed1\u6d77\u9650\u5236\u51fa\u53e3\u80fd\u529b\u5bfc\u81f4\u4f9b\u5e94\u7d27\u5f20 [DELIVERY] [N/A]": "Russia's export limits in the Black Sea tightened supply [DELIVERY] [N/A]",
  "\u539f\u6cb9\u5e93\u5b58\u4e0b\u964d [\u4ea4\u4ed8] [\u597d\u4e8e\u9884\u671f]": "Crude inventories declined [Delivery] [Above expectation]",
  "\u5409\u59c6\xb7\u514b\u83b1\u9ed8\u8bc4\u8bba\u7ecf\u6d4e\u5206\u5316\u63a8\u52a8\u4e50\u89c2\u60c5\u7eea [\u9884\u671f] [N/A]": "Jim Cramer noted economic divergence fueling optimism [Expectation] [N/A]",
  "\u5730\u7f18\u653f\u6cbb\u7d27\u5f20\u5c40\u52bf\u5347\u7ea7\u63a8\u52a8\u6cb9\u4ef7\u53cd\u5f39 [\u4ea4\u4ed8] [\u4e0d\u9002\u7528]": "Rising geopolitical tensions drove an oil price rebound [Delivery] [N/A]",
  "\u5bf9\u4fc4\u7f57\u65af\u548c\u4f0a\u6717\u5236\u88c1\u5f15\u53d1\u4f9b\u5e94\u62c5\u5fe7 [EXPECTATION] [N/A]": "Sanctions on Russia and Iran raised supply concerns [EXPECTATION] [N/A]",
  "\u5e02\u573a\u62c5\u5fe7OPEC+\u81ea\u613f\u51cf\u4ea7\u6267\u884c\u60c5\u51b5 [\u4ea4\u4ed8] [\u4e0d\u53ca\u9884\u671f]": "Market questioned OPEC+ voluntary cut compliance [Delivery] [Below expectation]",
  "\u5f3a\u52bf\u7f8e\u5143\u538b\u529b [\u4ea4\u4ed8] [\u4e0d\u9002\u7528]": "Strong dollar pressure [Delivery] [N/A]",
  "\u6295\u673a\u6027\u5934\u5bf8\u8c03\u6574\u63a8\u52a8\u53cd\u5f39 [\u9884\u671f] [\u4e0d\u9002\u7528]": "Speculative position adjustments fueled a rebound [Expectation] [N/A]",
  "\u6295\u673a\u6027\u629b\u552e\u538b\u529b\u589e\u52a0 [DELIVERY] [N/A]": "Speculative selling pressure increased [DELIVERY] [N/A]",
  "\u6b27\u6d32\u5236\u9020\u4e1aPMI\u6570\u636e\u75b2\u8f6f [\u4ea4\u4ed8] [\u4f4e\u4e8e\u9884\u671f]": "Eurozone manufacturing PMI came in weak [Delivery] [Below expectation]",
  "\u7279\u6717\u666e\u5a01\u80c1\u5bf9\u4e2d\u56fd\u52a0\u5f8150%\u5173\u7a0e\u5f15\u53d1\u9700\u6c42\u62c5\u5fe7 [DELIVERY] [N/A]": "Trump's threat of 50% tariffs on China reignited demand fears [DELIVERY] [N/A]",
  "\u77f3\u6cb9\u516c\u53f8\u8d22\u62a5\u663e\u793a\u884c\u4e1a\u75b2\u8f6f [\u4ea4\u4ed8] [\u5dee\u4e8e\u9884\u671f]": "Oil company earnings signaled sector weakness [Delivery] [Worse than expectation]",
  "\u7b2c\u4e09\u5b63\u5ea6\u8d22\u62a5\u663e\u793a\u4e8f\u635f\u5c0f\u4e8e\u9884\u671f [\u4ea4\u4ed8] [\u4f18\u4e8e\u9884\u671f]": "Q3 results showed losses narrower than expected [Delivery] [Above expectation]",
  "\u7f8e\u56fd\u5ba3\u5e03\u53ef\u80fd\u5bf9\u4fc4\u7f57\u65af\u5b9e\u65bd\u65b0\u5236\u88c1 [\u9884\u671f] [N/A]": "U.S. signaled potential new sanctions on Russia [Expectation] [N/A]",
  "\u7f8e\u56fd\u5bf9\u4f0a\u6717\u5b9e\u65bd\u65b0\u5236\u88c1 [\u4ea4\u4ed8] [\u4e0d\u9002\u7528]": "U.S. imposed new sanctions on Iran [Delivery] [N/A]",
  "\u7f8e\u56fd\u80a1\u5e02\u5927\u5e45\u629b\u552e\u5f15\u53d1\u539f\u6cb9\u9700\u6c42\u62c5\u5fe7 [DELIVERY] [N/A]": "Sharp U.S. equity selloff stirred oil demand concerns [DELIVERY] [N/A]",
  "\u7f8e\u8054\u50a8\u653f\u7b56\u9884\u671f\u8f6c\u53d8 [EXPECTATION] [N/A]": "Fed policy expectations shifted toward easing [EXPECTATION] [N/A]",
  "\u7f8e\u8054\u50a8\u9e70\u6d3e\u7acb\u573a\u63a8\u9ad8\u56fd\u503a\u6536\u76ca\u7387 [\u4ea4\u4ed8] [\u4e0d\u9002\u7528]": "Fed's hawkish stance drove Treasury yields higher [Delivery] [N/A]",
};

const HAN_REGEX = /[\\u3400-\\u9FFF]/u;

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
  if (result.startsWith(":") || result.startsWith("：")) {
    result = result.slice(1).trimStart();
  }
  const translated = AI_REASON_TRANSLATIONS[result];
  if (translated) return translated;
  if (HAN_REGEX.test(result)) {
    return "AI insight translation unavailable";
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
                            <span className="font-semibold text-slate-500">AI Analysis:</span>
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





