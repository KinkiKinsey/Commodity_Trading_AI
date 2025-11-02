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
  type SeriesMarkerPosition,
  type Time
} from "lightweight-charts";

import type { OverlayDataPoint } from "@/lib/utils/oilFactors";

const MICRO_POSITIVE = "#ff7f0e";
const MICRO_NEGATIVE = "#d4550b";
const MACRO_LINE_COLOR = "#003366";
const GRID_COLOR = "rgba(148, 163, 184, 0.2)";
const TEXT_COLOR = "#1f2937";
const GRID_LINE_COLOR = "rgba(148, 163, 184, 0.35)";

export type OilFactorsOverlayChartProps = {
  micro: OverlayDataPoint[];
  macro: OverlayDataPoint[];
  className?: string;
  height?: number;
  showAnnotations?: boolean;
};

function toLine(points: OverlayDataPoint[]): LineData[] {
  return points.map((point) => ({
    time: point.time as Time,
    value: point.value
  }));
}

function toHistogram(points: OverlayDataPoint[]): HistogramData[] {
  return points.map((point) => ({
    time: point.time as Time,
    value: point.value,
    color: point.value >= 0 ? MICRO_POSITIVE : MICRO_NEGATIVE
  }));
}

function truncateFactor(factor?: string | null): string {
  if (!factor) return "Factor";
  const trimmed = factor.trim();
  if (!trimmed) return "Factor";
  return trimmed.length > 10 ? `${trimmed.slice(0, 10)}…` : trimmed;
}

function buildMicroMarkers(points: OverlayDataPoint[]): SeriesMarker<Time>[] {
  if (!points.length) return [];
  return points
    .filter((point) => point.factor && point.factor.trim())
    .map((point) => ({
      time: point.time as Time,
      position: (point.value >= 0 ? "aboveBar" : "belowBar") as SeriesMarkerPosition,
      color: "#0f172a",
      shape: "circle" as const,
      text: truncateFactor(point.factor)
    }));
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
        position: "right",
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
        formatter: (value) => `${value.toFixed(2)}%`
      }
    } as HistogramSeriesPartialOptions);

    const macroLine = chart.addLineSeries({
      color: MACRO_LINE_COLOR,
      lineWidth: 2,
      priceLineVisible: false,
      priceFormat: {
        type: "custom",
        minMove: 0.01,
        formatter: (value) => `${value.toFixed(2)}%`
      }
    });

    chartRef.current = chart;
    microSeriesRef.current = histogram;
    macroSeriesRef.current = macroLine;

    const resize = () => {
      if (!container || !chartRef.current) return;
      chartRef.current.resize(container.clientWidth, height);
      updateLabelPositions();
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    setReady(true);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      microSeriesRef.current = null;
      macroSeriesRef.current = null;
      gridLinesRef.current = [];
      setLabelPositions(null);
      setReady(false);
    };
  }, [height, updateLabelPositions]);

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
        axisLabelVisible: true,
        axisLabelColor: "#cbd5f5",
        axisLabelBackgroundColor: "#ffffff",
        axisLabelTextColor: "#475569"
      });
      gridLinesRef.current.push(priceLine);
    });

    if (showAnnotations) {
      histogram.setMarkers(buildMicroMarkers(micro));
      macroLine.setMarkers(buildMacroMarkers(macro));
    } else {
      histogram.setMarkers([]);
      macroLine.setMarkers([]);
    }

    chart.timeScale().fitContent();
    updateLabelPositions();
  }, [ready, micro, macro, levelValues, showAnnotations, updateLabelPositions]);

  const labelHeight = 22;
  const clamp = (value: number) => Math.max(6, Math.min(height - labelHeight - 6, value));

  return (
    <div className={clsx("relative w-full", className)} style={{ height }}>
      <div ref={containerRef} className="absolute inset-0 rounded-2xl bg-white/85" />
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
