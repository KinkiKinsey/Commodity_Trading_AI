"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import {
  ColorType,
  createChart,
  CrosshairMode,
  LineStyle,
  type HistogramData,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type LineData,
  type Time
} from "lightweight-charts";

import type { OverlayDataPoint } from "@/lib/utils/oilFactors";

const GRID_COLOR = "rgba(148, 163, 184, 0.2)";
const TEXT_COLOR = "#1f2937";
const GRID_LINE_COLOR = "rgba(148, 163, 184, 0.35)";

// Vibrant color palette with good contrast
const FACTOR_COLORS = [
  "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
  "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788",
  "#FF8B94", "#6CCCB8"
];

type AggregatedPoint = {
  time: string;
  value: number;
  factors: Array<{ factor: string; value: number; color: string }>;
};

export type OilFactorsOverlayChartProps = {
  micro: OverlayDataPoint[];
  macro: OverlayDataPoint[];
  className?: string;
  height?: number;
  showAnnotations?: boolean;
};

// Aggregate factors by time, keeping track of individual contributions
function aggregateWithDetails(points: OverlayDataPoint[]): AggregatedPoint[] {
  const timeMap = new Map<string, Array<{ factor: string; value: number }>>();

  // Group by time
  points.forEach((point) => {
    const factorName = point.factor || "Unknown";
    if (!timeMap.has(point.time)) {
      timeMap.set(point.time, []);
    }
    timeMap.get(point.time)!.push({ factor: factorName, value: point.value });
  });

  // Assign colors to unique factors
  const uniqueFactors = Array.from(new Set(points.map(p => p.factor || "Unknown")));
  const factorColorMap = new Map<string, string>();
  uniqueFactors.forEach((factor, index) => {
    factorColorMap.set(factor, FACTOR_COLORS[index % FACTOR_COLORS.length]);
  });

  // Convert to aggregated points
  const result: AggregatedPoint[] = [];
  timeMap.forEach((factorValues, time) => {
    const totalValue = factorValues.reduce((sum, fv) => sum + fv.value, 0);
    const factorsWithColors = factorValues
      .map(fv => ({
        factor: fv.factor,
        value: fv.value,
        color: factorColorMap.get(fv.factor) || "#999"
      }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value)); // Sort by impact

    result.push({
      time,
      value: totalValue,
      factors: factorsWithColors
    });
  });

  return result.sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));
}

// Get top N most impactful factors across all time periods
function getTopFactors(points: OverlayDataPoint[], topN: number = 5): Array<{ factor: string; avgImpact: number; color: string }> {
  const factorImpactMap = new Map<string, number[]>();

  points.forEach((point) => {
    const factorName = point.factor || "Unknown";
    if (!factorImpactMap.has(factorName)) {
      factorImpactMap.set(factorName, []);
    }
    factorImpactMap.get(factorName)!.push(Math.abs(point.value));
  });

  const uniqueFactors = Array.from(new Set(points.map(p => p.factor || "Unknown")));
  const factorColorMap = new Map<string, string>();
  uniqueFactors.forEach((factor, index) => {
    factorColorMap.set(factor, FACTOR_COLORS[index % FACTOR_COLORS.length]);
  });

  const avgImpacts: Array<{ factor: string; avgImpact: number; color: string }> = [];
  factorImpactMap.forEach((impacts, factor) => {
    const avg = impacts.reduce((sum, val) => sum + val, 0) / impacts.length;
    avgImpacts.push({
      factor,
      avgImpact: avg,
      color: factorColorMap.get(factor) || "#999"
    });
  });

  return avgImpacts.sort((a, b) => b.avgImpact - a.avgImpact).slice(0, topN);
}

export function OilFactorsOverlayChart({
  micro,
  macro,
  className,
  height = 360,
  showAnnotations = true
}: OilFactorsOverlayChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const microHistogramRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const macroLineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const zeroLineRef = useRef<IPriceLine | null>(null);
  const gridLinesRef = useRef<IPriceLine[]>([]);
  const [ready, setReady] = useState(false);
  const [hoveredPoint, setHoveredPoint] = useState<AggregatedPoint | null>(null);
  const [hoveredPosition, setHoveredPosition] = useState<{ x: number; y: number } | null>(null);

  const microAggregated = useMemo(() => aggregateWithDetails(micro), [micro]);
  const macroAggregated = useMemo(() => aggregateWithDetails(macro), [macro]);
  const topMicroFactors = useMemo(() => getTopFactors(micro, 5), [micro]);
  const topMacroFactors = useMemo(() => getTopFactors(macro, 5), [macro]);

  const combinedValues = useMemo(() => {
    return [...micro, ...macro]
      .map((point) => point.value)
      .filter((value) => Number.isFinite(value)) as number[];
  }, [micro, macro]);

  const levelValues = useMemo(() => {
    if (!combinedValues.length) return [];
    const maxAbs = Math.max(...combinedValues.map((value) => Math.abs(value)));
    if (!Number.isFinite(maxAbs) || maxAbs === 0) return [];
    const levelCount = 2;
    const step = maxAbs / levelCount;
    const levels: number[] = [];
    for (let index = 1; index <= levelCount; index += 1) {
      const value = step * index;
      if (!Number.isFinite(value)) continue;
      const rounded = Number(value.toFixed(4));
      if (rounded > 0) levels.push(rounded);
      if (rounded > 0) levels.push(-rounded);
    }
    return Array.from(new Set(levels)).sort((a, b) => a - b);
  }, [combinedValues]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scaleMargins = height < 400
      ? { top: 0.15, bottom: 0.15 }
      : { top: 0.06, bottom: 0.08 };

    const chart = createChart(container, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: TEXT_COLOR,
        fontFamily: "'Noto Sans CJK', Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0)" },
        horzLines: { color: GRID_COLOR, style: LineStyle.Solid }
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins,
        ticksVisible: true
      },
      leftPriceScale: {
        visible: false
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        secondsVisible: false
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "rgba(148, 163, 184, 0.35)", width: 1, style: LineStyle.Dotted },
        horzLine: { color: "rgba(148, 163, 184, 0.5)", width: 1, style: LineStyle.Dotted }
      }
    });

    chartRef.current = chart;

    // Handle crosshair move for tooltip
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.point) {
        setHoveredPoint(null);
        setHoveredPosition(null);
        return;
      }

      const timeStr = param.time as string;
      const microPoint = microAggregated.find(p => p.time === timeStr);
      const macroPoint = macroAggregated.find(p => p.time === timeStr);

      if (microPoint || macroPoint) {
        setHoveredPoint(microPoint || macroPoint || null);
        setHoveredPosition({ x: param.point.x, y: param.point.y });
      } else {
        setHoveredPoint(null);
        setHoveredPosition(null);
      }
    });

    const resize = () => {
      if (!container || !chartRef.current) return;
      chartRef.current.resize(container.clientWidth, height);
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);

    setReady(true);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      microHistogramRef.current = null;
      macroLineRef.current = null;
      gridLinesRef.current = [];
      setReady(false);
    };
  }, [height, microAggregated, macroAggregated]);

  useEffect(() => {
    if (!ready) return;
    const chart = chartRef.current;
    if (!chart) return;

    // Clear existing series
    if (microHistogramRef.current) {
      chart.removeSeries(microHistogramRef.current);
    }
    if (macroLineRef.current) {
      chart.removeSeries(macroLineRef.current);
    }

    // Add Micro Histogram (aggregated)
    const microHistogram = chart.addHistogramSeries({
      base: 0,
      priceLineVisible: false,
      priceFormat: {
        type: "custom",
        minMove: 0.01,
        formatter: (value: number) => `${value.toFixed(2)}%`
      }
    });

    const microHistogramData: HistogramData[] = microAggregated.map(point => ({
      time: point.time as Time,
      value: point.value,
      color: point.value >= 0 ? "rgba(52, 211, 153, 0.6)" : "rgba(248, 113, 113, 0.6)"
    }));
    microHistogram.setData(microHistogramData);
    microHistogramRef.current = microHistogram;

    // Add Macro Line (aggregated)
    const macroLine = chart.addLineSeries({
      color: "#1e40af",
      lineWidth: 3,
      priceLineVisible: false,
      priceFormat: {
        type: "custom",
        minMove: 0.01,
        formatter: (value: number) => `${value.toFixed(2)}%`
      }
    });

    const macroLineData: LineData[] = macroAggregated.map(point => ({
      time: point.time as Time,
      value: point.value
    }));
    macroLine.setData(macroLineData);
    macroLineRef.current = macroLine;

    // Add zero line
    if (zeroLineRef.current) {
      macroLine.removePriceLine(zeroLineRef.current);
    }
    zeroLineRef.current = macroLine.createPriceLine({
      price: 0,
      color: "#111827",
      lineWidth: 2,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: false
    });

    // Add grid lines
    gridLinesRef.current.forEach((line) => macroLine.removePriceLine(line));
    gridLinesRef.current = [];
    levelValues.forEach((value) => {
      if (Math.abs(value) < 1e-6) return;
      const priceLine = macroLine.createPriceLine({
        price: value,
        color: GRID_LINE_COLOR,
        lineWidth: 1,
        lineStyle: LineStyle.Dotted,
        axisLabelVisible: true
      });
      gridLinesRef.current.push(priceLine);
    });

    chart.timeScale().fitContent();
  }, [ready, microAggregated, macroAggregated, levelValues]);

  return (
    <div className={clsx("flex gap-6", className)}>
      {/* Main Chart */}
      <div className="flex-1 flex flex-col gap-4">
        {/* Chart */}
        <div className="relative w-full" style={{ height }}>
          <div ref={containerRef} className="absolute inset-0 rounded-2xl bg-white/85" />

          {/* Tooltip */}
          {hoveredPoint && hoveredPosition && (
            <div
              className="pointer-events-none absolute z-50 rounded-lg border border-slate-200 bg-white p-3 shadow-xl"
              style={{
                left: Math.min(hoveredPosition.x + 10, (containerRef.current?.clientWidth || 0) - 250),
                top: Math.max(hoveredPosition.y - 60, 10)
              }}
            >
              <div className="text-xs font-semibold text-slate-700 mb-2">
                {new Date(hoveredPoint.time).toLocaleDateString()}
              </div>
              <div className="space-y-1">
                {hoveredPoint.factors.slice(0, 5).map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span
                      className="h-2 w-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: f.color }}
                    />
                    <span className="flex-1 truncate max-w-[150px]">{f.factor}</span>
                    <span className={clsx("font-mono font-medium", f.value >= 0 ? "text-emerald-600" : "text-red-600")}>
                      {f.value >= 0 ? "+" : ""}{f.value.toFixed(2)}%
                    </span>
                  </div>
                ))}
                {hoveredPoint.factors.length > 5 && (
                  <div className="text-xs text-slate-400 italic">
                    +{hoveredPoint.factors.length - 5} more...
                  </div>
                )}
              </div>
              <div className="mt-2 pt-2 border-t border-slate-200 flex justify-between items-center">
                <span className="text-xs text-slate-500">Total</span>
                <span className={clsx("text-sm font-bold", hoveredPoint.value >= 0 ? "text-emerald-600" : "text-red-600")}>
                  {hoveredPoint.value >= 0 ? "+" : ""}{hoveredPoint.value.toFixed(2)}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <div className="h-3 w-8 rounded bg-gradient-to-r from-emerald-400/60 to-emerald-400/60" />
            <span className="text-slate-600">Micro (Short-term)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-0.5 w-8 bg-blue-800" />
            <span className="text-slate-600">Macro (Long-term)</span>
          </div>
        </div>
      </div>

      {/* Top Factors Sidebar */}
      <div className="w-64 flex flex-col gap-3 flex-shrink-0">
        {/* Micro Top Factors */}
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <h3 className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Top Micro Factors
          </h3>
          <div className="space-y-1.5">
            {topMicroFactors.map((factor, index) => (
              <div key={index} className="flex items-center gap-1.5">
                <span className="flex-shrink-0 text-[10px] font-bold text-slate-400 w-3">#{index + 1}</span>
                <span
                  className="h-2 w-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: factor.color }}
                />
                <span className="flex-1 text-[11px] truncate min-w-0">{factor.factor}</span>
                <span className="text-[10px] font-mono font-semibold text-slate-700 flex-shrink-0">
                  {factor.avgImpact.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Macro Top Factors */}
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <h3 className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Top Macro Factors
          </h3>
          <div className="space-y-1.5">
            {topMacroFactors.map((factor, index) => (
              <div key={index} className="flex items-center gap-1.5">
                <span className="flex-shrink-0 text-[10px] font-bold text-slate-400 w-3">#{index + 1}</span>
                <span
                  className="h-2 w-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: factor.color }}
                />
                <span className="flex-1 text-[11px] truncate min-w-0">{factor.factor}</span>
                <span className="text-[10px] font-mono font-semibold text-slate-700 flex-shrink-0">
                  {factor.avgImpact.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
