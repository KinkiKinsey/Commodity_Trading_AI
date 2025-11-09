"use client";

import { useEffect, useMemo, useRef } from "react";
import clsx from "clsx";
import {
  ColorType,
  type CandlestickData,
  type DeepPartial,
  type IChartApi,
  type LineData,
  type SeriesMarker,
  type CandlestickSeriesPartialOptions,
  type LineSeriesPartialOptions,
  createChart
} from "lightweight-charts";

type CandleSeriesConfig = {
  data: CandlestickData[];
  options?: DeepPartial<CandlestickSeriesPartialOptions>;
};

type LineSeriesConfig = {
  id: string;
  data: LineData[];
  options?: DeepPartial<LineSeriesPartialOptions>;
};

type ChartShellProps = {
  candles?: CandleSeriesConfig;
  lines?: LineSeriesConfig[];
  markers?: SeriesMarker<CandlestickData["time"]>[];
  height?: number;
  className?: string;
  watermark?: string;
};

const DEFAULT_LAYOUT = {
  background: { color: "#ffffff" },
  textColor: "#1e293b"
} as const;

export function ChartShell({
  candles,
  lines,
  markers,
  height = 320,
  className,
  watermark = "Ringshell · CTP"
}: ChartShellProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const chart = createChart(containerRef.current, {
      layout: DEFAULT_LAYOUT,
      width: containerRef.current.clientWidth,
      height,
      grid: {
        vertLines: { color: "rgba(148,163,184,0.2)" },
        horzLines: { color: "rgba(148,163,184,0.2)" }
      },
      crosshair: { mode: 0 },
      timeScale: { borderColor: "rgba(148,163,184,0.4)" },
      rightPriceScale: { borderColor: "rgba(148,163,184,0.4)" },
      watermark: {
        color: "rgba(15,23,42,0.08)",
        visible: true,
        text: watermark,
        fontSize: 18,
        vertAlign: "bottom",
        horzAlign: "left"
      }
    });
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver((entries) => {
      if (!entries.length) return;
      const { width } = entries[0].contentRect;
      chart.applyOptions({ width });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [height, watermark]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || !candles) {
      return;
    }

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#16a34a",
      downColor: "#dc2626",
      borderDownColor: "#dc2626",
      borderUpColor: "#16a34a",
      wickDownColor: "#dc2626",
      wickUpColor: "#16a34a",
      ...candles.options
    });
    candleSeries.setData(candles.data);
    if (markers?.length) {
      candleSeries.setMarkers(markers);
    }

    return () => {
      if (!chart || typeof chart.removeSeries !== "function") {
        return;
      }
      try {
        chart.removeSeries(candleSeries);
      } catch {
        // ignore chart disposal race
      }
    };
  }, [candles, markers]);

  useEffect(() => {
    const chart = chartRef.current;
    const seriesConfigs = lines?.filter((line): line is LineSeriesConfig => Boolean(line && line.data?.length));
    if (!chart || !seriesConfigs?.length) {
      return;
    }

    const created = seriesConfigs.map((seriesConfig) => {
      const series = chart.addLineSeries({
        color: "#2563eb",
        lineWidth: 2,
        priceLineVisible: false,
        crosshairMarkerVisible: false,
        ...seriesConfig.options
      });
      series.setData(seriesConfig.data);
      return series;
    });

    return () => {
      if (!chart || typeof chart.removeSeries !== "function") {
        return;
      }
      created.forEach((series) => {
        if (!series) {
          return;
        }
        try {
          chart.removeSeries(series);
        } catch {
          // ignore if chart already disposed
        }
      });
    };
  }, [lines]);

  return <div ref={containerRef} className={clsx("relative w-full", className)} style={{ height }} />;
}
