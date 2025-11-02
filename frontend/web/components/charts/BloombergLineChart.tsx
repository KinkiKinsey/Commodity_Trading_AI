"use client";

import { useEffect, useMemo, useRef } from "react";
import clsx from "clsx";
import { ColorType, CrosshairMode, createChart, type IChartApi, type ISeriesApi, type LineData, type Time } from "lightweight-charts";

export type LineSeriesPoint = {
  time: string;
  value: number;
  label?: string;
  meta?: unknown;
};

export type LineSeriesDefinition = {
  id: string;
  name: string;
  color?: string;
  data: LineSeriesPoint[];
};

type BloombergLineChartProps = {
  series: LineSeriesDefinition[];
  className?: string;
  height?: number;
  yAxisTitle?: string;
  valueFormatter?: (value: number) => string;
};

const DEFAULT_HEIGHT = 340;
const DEFAULT_COLORS = ["#2563EB", "#7C3AED", "#14B8A6", "#F97316", "#DC2626", "#6366F1"];

function toLineData(points: LineSeriesPoint[]): LineData[] {
  return points
    .filter((point) => Number.isFinite(point.value))
    .map((point) => ({
      time: point.time as Time,
      value: point.value
    }));
}

export function BloombergLineChart({
  series,
  className,
  height = DEFAULT_HEIGHT,
  yAxisTitle,
  valueFormatter
}: BloombergLineChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRefs = useRef<Map<string, ISeriesApi<"Line">>>(new Map());

  const resolvedFormatter = useMemo(
    () =>
      valueFormatter ??
      ((value: number) => {
        if (!Number.isFinite(value)) return "--";
        return value.toFixed(4);
      }),
    [valueFormatter]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      height,
      width: container.clientWidth,
      layout: {
        background: {
          type: ColorType.Solid,
          color: "#FFFFFF"
        },
        textColor: "#1F2937",
        fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
      },
      grid: {
        vertLines: {
          color: "rgba(148, 163, 184, 0.25)"
        },
        horzLines: {
          color: "rgba(148, 163, 184, 0.2)"
        }
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "rgba(79, 70, 229, 0.45)",
          style: 3
        },
        horzLine: {
          color: "rgba(79, 70, 229, 0.45)",
          labelBackgroundColor: "#111827",
          labelColor: "#F9FAFB"
        }
      },
      timeScale: {
        borderColor: "rgba(148, 163, 184, 0.45)",
        timeVisible: false,
        secondsVisible: false
      },
      rightPriceScale: {
        borderColor: "rgba(148, 163, 184, 0.45)",
        scaleMargins: {
          top: 0.12,
          bottom: 0.08
        }
      }
    });

    chartRef.current = chart;
    const registry = seriesRefs.current;

    return () => {
      registry.forEach((seriesApi) => {
        chart.removeSeries(seriesApi);
      });
      registry.clear();
      chart.remove();
      chartRef.current = null;
    };
  }, [height, yAxisTitle]);

  useEffect(() => {
    const container = containerRef.current;
    const chart = chartRef.current;
    if (!container || !chart) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width } = entry.contentRect;
      chart.resize(width, height);
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, [height]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const currentSeries = seriesRefs.current;
    const incomingIds = new Set(series.map((item) => item.id));

    currentSeries.forEach((seriesApi, id) => {
      if (!incomingIds.has(id)) {
        chart.removeSeries(seriesApi);
        currentSeries.delete(id);
      }
    });

    series.forEach((definition, index) => {
      const color = definition.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length];
      let lineSeries = currentSeries.get(definition.id);

      if (!lineSeries) {
        lineSeries = chart.addLineSeries({
          color,
          lineWidth: 2,
          priceLineVisible: false,
          crosshairMarkerVisible: true,
          lastValueVisible: false,
          pointMarkersVisible: false
        });
        currentSeries.set(definition.id, lineSeries);
      }

      lineSeries.applyOptions({ color });

      lineSeries.applyOptions({
        priceFormat: {
          type: "custom",
          minMove: 0.0001,
          formatter: resolvedFormatter
        }
      });

      lineSeries.setData(toLineData(definition.data));
    });

    if (series.length > 0) {
      chart.timeScale().fitContent();
    }
  }, [series, resolvedFormatter]);

  return (
    <div className={clsx("relative w-full rounded-xl bg-white", className)}>
      <div ref={containerRef} className="h-full w-full" style={{ height }} />
      {yAxisTitle ? (
        <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-full bg-slate-900/90 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-white/80 shadow-sm">
          {yAxisTitle}
        </div>
      ) : null}
    </div>
  );
}
