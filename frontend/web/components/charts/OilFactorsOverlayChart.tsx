"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import {
  ColorType,
  createChart,
  CrosshairMode,
  LineStyle,
  type HistogramData,
  type HistogramSeriesPartialOptions,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type LineData,
  type SeriesMarker,
  type Time
} from "lightweight-charts";

import type { OverlayDataPoint } from "@/lib/utils/oilFactors";

const MICRO_POSITIVE = "#ff7f0e";
const MICRO_NEGATIVE = "#d4550b";
const MACRO_LINE_COLOR = "#003366";
const GRID_COLOR = "rgba(148, 163, 184, 0.2)";
const TEXT_COLOR = "#1f2937";
const GRID_LINE_COLOR = "rgba(148, 163, 184, 0.35)";

type MicroBadge = {
  id: string;
  x: number;
  y: number;
  title: string;
  value: number;
  time: string;
  label: string;
};

export type OilFactorsOverlayChartProps = {
  micro: OverlayDataPoint[];
  macro: OverlayDataPoint[];
  className?: string;
  height?: number;
  showAnnotations?: boolean;
};

function toLine(points: OverlayDataPoint[]): LineData[] {
  if (!points || points.length === 0) return [];

  // Use Map to ensure unique timestamps, keeping the last value for duplicates
  const uniqueMap = new Map<number, number>();
  points.forEach(point => {
    const timeNum = Number(point.time);
    uniqueMap.set(timeNum, point.value);
  });

  // Convert to array and sort by time
  const result = Array.from(uniqueMap.entries())
    .map(([time, value]) => ({ time: time as Time, value }))
    .sort((a, b) => Number(a.time) - Number(b.time));

  return result;
}

function toHistogram(points: OverlayDataPoint[]): HistogramData[] {
  if (!points || points.length === 0) return [];

  // Use Map to ensure unique timestamps, keeping the last value for duplicates
  const uniqueMap = new Map<number, { value: number }>();
  points.forEach(point => {
    const timeNum = Number(point.time);
    uniqueMap.set(timeNum, { value: point.value });
  });

  // Convert to array and sort by time
  const result = Array.from(uniqueMap.entries())
    .map(([time, data]) => ({
      time: time as Time,
      value: data.value,
      color: data.value >= 0 ? MICRO_POSITIVE : MICRO_NEGATIVE
    }))
    .sort((a, b) => Number(a.time) - Number(b.time));

  return result;
}

function buildMacroMarkers(points: OverlayDataPoint[]): SeriesMarker<Time>[] {
  if (!points.length) return [];
  let highest = points[0];
  let lowest = points[0];
  points.forEach((point) => {
    if (point.value > highest.value) highest = point;
    if (point.value < lowest.value) lowest = point;
  });
  return [
    {
      time: highest.time as Time,
      position: "aboveBar",
      color: "#2563eb",
      shape: "arrowUp",
      text: highest.factor ? highest.factor.slice(0, 12) : "Macro"
    },
    {
      time: lowest.time as Time,
      position: "belowBar",
      color: "#2563eb",
      shape: "arrowDown",
      text: lowest.factor ? lowest.factor.slice(0, 12) : "Macro"
    }
  ];
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
  const microSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const macroSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const microZeroLineRef = useRef<IPriceLine | null>(null);
  const macroZeroLineRef = useRef<IPriceLine | null>(null);
  const gridLinesRef = useRef<IPriceLine[]>([]);
  const [labelPositions, setLabelPositions] = useState<{ micro: number; macro: number } | null>(null);
  const [microBadges, setMicroBadges] = useState<MicroBadge[]>([]);
  const [hoveredBadgeId, setHoveredBadgeId] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

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

  const updateLabelPositions = useCallback(() => {
    const chart = chartRef.current;
    const macroSeries = macroSeriesRef.current;
    if (!chart || !macroSeries) return;
    const coordinate = macroSeries.priceToCoordinate(0);
    if (coordinate === null || coordinate === undefined) return;
    setLabelPositions({
      micro: coordinate - 12,
      macro: coordinate + 12
    });
  }, []);

  const updateMicroBadges = useCallback(() => {
    const chart = chartRef.current;
    const histogram = microSeriesRef.current;
    const container = containerRef.current;
    if (!chart || !histogram || !container) {
      setMicroBadges([]);
      return;
    }

    const timeScale = chart.timeScale();
    const topMicro = [...micro].sort((a, b) => Math.abs(b.value) - Math.abs(a.value)).slice(0, 8);
    const badges: MicroBadge[] = [];

    topMicro.forEach((point) => {
      if (!point.factor?.trim()) return;
      const x = timeScale.timeToCoordinate(point.time as Time);
      const y = histogram.priceToCoordinate(point.value);
      if (x === null || x === undefined || y === null || y === undefined) return;
      if (x < 12 || x > container.clientWidth - 12) return;
      const adjustedY = point.value >= 0 ? y - 28 : y + 12;
      badges.push({
        id: `${point.time}-${point.factor}-${point.value}`,
        x,
        y: adjustedY,
        title: point.factor.trim(),
        value: point.value,
        time: point.time,
        label: point.label
      });
    });

    setMicroBadges(badges);
    setHoveredBadgeId((prev) => (prev && badges.some((badge) => badge.id === prev) ? prev : null));
  }, [micro]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

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
        scaleMargins: { top: 0.06, bottom: 0.08 },
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

    const histogram = chart.addHistogramSeries({
      base: 0,
      priceLineVisible: false,
      priceFormat: {
        type: "custom",
        minMove: 0.01,
        formatter: (value: number) => `${value.toFixed(2)}%`
      }
    } as HistogramSeriesPartialOptions);

    const macroLine = chart.addLineSeries({
      color: MACRO_LINE_COLOR,
      lineWidth: 2,
      priceLineVisible: false,
      priceFormat: {
        type: "custom",
        minMove: 0.01,
        formatter: (value: number) => `${value.toFixed(2)}%`
      }
    });

    chartRef.current = chart;
    microSeriesRef.current = histogram;
    macroSeriesRef.current = macroLine;

    const resize = () => {
      if (!container || !chartRef.current) return;
      chartRef.current.resize(container.clientWidth, height);
      updateLabelPositions();
      updateMicroBadges();
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);

    const timeScale = chart.timeScale();
    const handleVisibleRange = () => {
      updateLabelPositions();
      updateMicroBadges();
    };
    timeScale.subscribeVisibleTimeRangeChange(handleVisibleRange);

    setReady(true);

    return () => {
      resizeObserver.disconnect();
      timeScale.unsubscribeVisibleTimeRangeChange(handleVisibleRange);
      chart.remove();
      chartRef.current = null;
      microSeriesRef.current = null;
      macroSeriesRef.current = null;
      gridLinesRef.current = [];
      setLabelPositions(null);
      setMicroBadges([]);
      setReady(false);
    };
  }, [height, updateLabelPositions, updateMicroBadges]);

  useEffect(() => {
    if (!ready) return;
    const chart = chartRef.current;
    const histogram = microSeriesRef.current;
    const macroLine = macroSeriesRef.current;
    if (!chart || !histogram || !macroLine) {
      setLabelPositions(null);
      return;
    }

    if (microZeroLineRef.current) {
      histogram.removePriceLine(microZeroLineRef.current);
    }
    microZeroLineRef.current = histogram.createPriceLine({
      price: 0,
      color: "#111827",
      lineWidth: 3,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: false
    });

    if (macroZeroLineRef.current) {
      macroLine.removePriceLine(macroZeroLineRef.current);
    }
    macroZeroLineRef.current = macroLine.createPriceLine({
      price: 0,
      color: "#111827",
      lineWidth: 3,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: false
    });

    histogram.setData(toHistogram(micro));
    macroLine.setData(toLine(macro));

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

    if (showAnnotations) {
      histogram.setMarkers([]);
      macroLine.setMarkers(buildMacroMarkers(macro));
    } else {
      histogram.setMarkers([]);
      macroLine.setMarkers([]);
    }

    chart.timeScale().fitContent();
    updateLabelPositions();
    updateMicroBadges();
  }, [ready, micro, macro, levelValues, showAnnotations, updateLabelPositions, updateMicroBadges]);

  const labelHeight = 22;
  const clamp = (value: number) => Math.max(6, Math.min(height - labelHeight - 6, value));
  const clampBadgeY = (value: number) => Math.max(6, Math.min(height - 28, value));
  const hoveredBadge = hoveredBadgeId ? microBadges.find((badge) => badge.id === hoveredBadgeId) ?? null : null;
  const tooltipTop = hoveredBadge ? clampBadgeY(hoveredBadge.y - 40) : 0;
  const tooltipLeft = hoveredBadge
    ? Math.max(24, Math.min((containerRef.current?.clientWidth ?? 0) - 24, hoveredBadge.x))
    : 0;

  return (
    <div className={clsx("relative w-full", className)} style={{ height }}>
      <div ref={containerRef} className="absolute inset-0 rounded-2xl bg-white/85" />
      {microBadges.map((badge) => (
        <div
          key={badge.id}
          className="absolute z-20 flex h-4 w-4 -translate-x-1/2 items-center justify-center"
          style={{ left: badge.x, top: clampBadgeY(badge.y) }}
          title={badge.title}
          aria-label={badge.title}
          onMouseEnter={() => setHoveredBadgeId(badge.id)}
          onMouseLeave={() => setHoveredBadgeId((prev) => (prev === badge.id ? null : prev))}
        >
          <span
            className="relative block h-3 w-3 rounded-full shadow-[0_0_18px_rgba(99,102,241,0.45)] transition-transform hover:scale-125"
            style={{
              background: "linear-gradient(120deg, #60a5fa, #a855f7, #f97316, #22d3ee, #60a5fa)",
              backgroundSize: "300% 300%",
              animation: "gradientGlow 4.5s ease-in-out infinite"
            }}
          >
            <span
              className="pointer-events-none absolute inset-0 rounded-full opacity-70 blur-[4px]"
              style={{
                background: "inherit",
                backgroundSize: "inherit",
                animation: "gradientGlow 4.5s ease-in-out infinite"
              }}
            />
          </span>
        </div>
      ))}
      {hoveredBadge ? (
        <div
          className="pointer-events-none absolute z-30 -translate-x-1/2"
          style={{ left: tooltipLeft, top: tooltipTop }}
        >
          <div className="relative max-w-[240px] rounded-2xl">
            <div
              aria-hidden
              className="pointer-events-none absolute -inset-[1.5px] rounded-2xl opacity-90"
              style={{
                background: "linear-gradient(120deg, #60a5fa, #a855f7, #f97316, #22d3ee, #60a5fa)",
                backgroundSize: "300% 300%",
                animation: "gradientGlow 5.2s ease-in-out infinite",
                filter: "blur(0.6px)"
              }}
            />
            <div className="relative rounded-2xl border border-white bg-white px-4 py-3 text-xs shadow-[0_18px_32px_rgba(15,23,42,0.18)]">
              <div className="flex items-center justify-between gap-3">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-600">Micro Factor</span>
                <span className="rounded-full bg-slate-900 px-2 py-[2px] text-[10px] font-semibold text-white shadow-[0_0_10px_rgba(15,23,42,0.35)]">
                  {hoveredBadge.value > 0 ? "+" : ""}
                  {hoveredBadge.value.toFixed(2)}%
                </span>
              </div>
              <p className="mt-1 text-sm font-semibold leading-tight text-slate-900">{hoveredBadge.title}</p>
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                <span>{new Date(hoveredBadge.time).toLocaleDateString()}</span>
                <span className="truncate">{hoveredBadge.label}</span>
              </div>
            </div>
          </div>
        </div>
      ) : null}
      {labelPositions ? (
        <>
          <div
            className="pointer-events-none absolute right-4 flex items-center justify-center rounded-full bg-black px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-white"
            style={{ top: clamp(labelPositions.micro) }}
          >
            Micro
          </div>
          <div
            className="pointer-events-none absolute right-4 flex items-center justify-center rounded-full bg-black px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-white"
            style={{ top: clamp(labelPositions.macro) }}
          >
            Macro
          </div>
        </>
      ) : null}
    </div>
  );
}
