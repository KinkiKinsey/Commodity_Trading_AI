"use client";

import { useEffect, useMemo, useRef } from "react";
import clsx from "clsx";
import {
  createChart,
  ColorType,
  type BusinessDay,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type LineData,
  type Time,
  type MouseEventParams,
} from "lightweight-charts";
import type { CandlestickPoint, LinePoint, VolumePoint } from "@/lib/hooks/usePricingKline";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";
import { useIntl, type Locale } from "@/lib/i18n/IntlContext";

type MarkerPosition = "aboveBar" | "belowBar";

const CHART_HEIGHT = 300;
const BACKGROUND_COLOR = "#ffffff";
const GRID_LINE_COLOR = "rgba(148, 163, 184, 0.2)";
const TEXT_COLOR = "rgba(30, 41, 59, 0.88)";

type KLineChartProps = {
  candles: CandlestickPoint[];
  movingAverageLine: LinePoint[];
  movingAverageUpper: LinePoint[];
  movingAverageLower: LinePoint[];
  volumes: VolumePoint[];
  signals: IndexSignal[];
  className?: string;
  height?: number;
  isLoading?: boolean;
  onSelectSignal?: (signal: IndexSignal) => void;
  locale?: Locale;
};

function toCandlestickData(points: CandlestickPoint[]): CandlestickData[] {
  return points.map((point) => ({
    time: point.time as Time,
    open: point.open,
    high: point.high,
    low: point.low,
    close: point.close,
  }));
}

function toLineData(points: LinePoint[]): LineData[] {
  return points.map((point) => ({
    time: point.time as Time,
    value: point.value,
  }));
}

function toHistogramData(points: VolumePoint[]): HistogramData[] {
  return points.map((point) => ({
    time: point.time as Time,
    value: point.value,
    color: point.color,
  }));
}

function toMarker(signal: IndexSignal) {
  const timestamp = Math.floor(new Date(signal.createdAt).getTime() / 1000);
  return {
    time: timestamp as Time,
    position: (signal.signalType === "buy" ? "belowBar" : "aboveBar") as MarkerPosition,
    color: signal.signalType === "buy" ? "#0EAD69" : "#F25F5C",
    shape: signal.signalType === "buy" ? "arrowUp" : "arrowDown",
    text: signal.reasonTag ?? "",
  } as const;
}

export function KLineChart({
  candles,
  movingAverageLine,
  movingAverageUpper,
  movingAverageLower,
  volumes,
  signals,
  className,
  height = CHART_HEIGHT,
  isLoading,
  onSelectSignal,
  locale: localeOverride,
}: KLineChartProps) {
  const { locale: intlLocale, t } = useIntl();
  const resolvedLocale = localeOverride ?? intlLocale;

  const axisTickFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(resolvedLocale, {
        month: "2-digit",
        day: "2-digit",
      }),
    [resolvedLocale]
  );

  const tooltipFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(resolvedLocale, {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      }),
    [resolvedLocale]
  );

  const priceFormatter = useMemo(
    () =>
      new Intl.NumberFormat(resolvedLocale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
    [resolvedLocale]
  );

  const volumeFormatter = useMemo(
    () =>
      new Intl.NumberFormat(resolvedLocale, {
        notation: "compact",
        maximumFractionDigits: 1,
      }),
    [resolvedLocale]
  );

  const volumeLabel = resolvedLocale === "zh-CN" ? "成交量" : "Vol";

  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const maLineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const maUpperRef = useRef<ISeriesApi<"Line"> | null>(null);
  const maLowerRef = useRef<ISeriesApi<"Line"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const priceLineRef = useRef<IPriceLine | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  const candlesRef = useRef<CandlestickPoint[]>([]);
  const maLineDataRef = useRef<LinePoint[]>([]);
  const maUpperDataRef = useRef<LinePoint[]>([]);
  const maLowerDataRef = useRef<LinePoint[]>([]);
  const volumeDataRef = useRef<VolumePoint[]>([]);
  const signalsRef = useRef<IndexSignal[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      height,
      layout: {
        background: { type: ColorType.Solid, color: BACKGROUND_COLOR },
        textColor: TEXT_COLOR,
      },
      grid: {
        vertLines: { color: GRID_LINE_COLOR },
        horzLines: { color: GRID_LINE_COLOR },
      },
      rightPriceScale: {
        borderColor: "rgba(148, 163, 184, 0.28)",
        scaleMargins: {
          top: 0.12,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderColor: "rgba(148, 163, 184, 0.28)",
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: (time: Time) => formatAxisTick(time, axisTickFormatter),
      },
      crosshair: {
        mode: 0,
        vertLine: {
          color: "rgba(148, 163, 184, 0.45)",
          width: 1,
          style: 3,
        },
        horzLine: {
          color: "rgba(148, 163, 184, 0.45)",
          width: 1,
          style: 3,
        },
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#0EAD69",
      downColor: "#F25F5C",
      borderUpColor: "#0EAD69",
      borderDownColor: "#F25F5C",
      wickUpColor: "#0EAD69",
      wickDownColor: "#F25F5C",
      priceLineVisible: false,
    });

    const maLineSeries = chart.addLineSeries({
      color: "#2563EB",
      lineWidth: 2,
      priceLineVisible: false,
    });

    const maUpperSeries = chart.addLineSeries({
      color: "rgba(37, 99, 235, 0.45)",
      lineWidth: 2,
      lineStyle: 2,
      priceLineVisible: false,
    });

    const maLowerSeries = chart.addLineSeries({
      color: "rgba(37, 99, 235, 0.45)",
      lineWidth: 2,
      lineStyle: 2,
      priceLineVisible: false,
    });

    const volumeSeries = chart.addHistogramSeries({
      color: "rgba(148, 163, 184, 0.35)",
      priceFormat: { type: "volume" },
      priceScaleId: "left",
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
      borderColor: "rgba(148, 163, 184, 0.18)",
    });

    priceLineRef.current = candleSeries.createPriceLine({
      price: 0,
      color: "#f97316",
      lineStyle: 2,
      lineWidth: 2,
      axisLabelVisible: true,
      title: "latest",
    });

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target === container) {
          const { width } = entry.contentRect;
          chart.applyOptions({ width });
          chart.timeScale().fitContent();
        }
      }
    });

    resizeObserver.observe(container);

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    maLineRef.current = maLineSeries;
    maUpperRef.current = maUpperSeries;
    maLowerRef.current = maLowerSeries;
    volumeSeriesRef.current = volumeSeries;
    resizeObserverRef.current = resizeObserver;

    if (candlesRef.current.length) {
      candleSeries.setData(toCandlestickData(candlesRef.current));
      chart.timeScale().fitContent();
    }

    if (maLineDataRef.current.length) {
      maLineSeries.setData(toLineData(maLineDataRef.current));
    }

    if (maUpperDataRef.current.length) {
      maUpperSeries.setData(toLineData(maUpperDataRef.current));
    }

    if (maLowerDataRef.current.length) {
      maLowerSeries.setData(toLineData(maLowerDataRef.current));
    }

    if (volumeDataRef.current.length) {
      volumeSeries.setData(toHistogramData(volumeDataRef.current));
    }

    if (signalsRef.current.length) {
      candleSeries.setMarkers(signalsRef.current.map(toMarker));
    }

    return () => {
      resizeObserver.disconnect();
      resizeObserverRef.current = null;
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      maLineRef.current = null;
      maUpperRef.current = null;
      maLowerRef.current = null;
      volumeSeriesRef.current = null;
      priceLineRef.current = null;
    };
  }, [height, axisTickFormatter]);

  useEffect(() => {
    candlesRef.current = candles;
    if (!candleSeriesRef.current) return;
    candleSeriesRef.current.setData(toCandlestickData(candles));
    chartRef.current?.timeScale().fitContent();
    if (priceLineRef.current && candles.length) {
      priceLineRef.current.applyOptions({ price: candles[candles.length - 1].close });
    }
  }, [candles]);

  useEffect(() => {
    maLineDataRef.current = movingAverageLine;
    if (!maLineRef.current) return;
    maLineRef.current.setData(toLineData(movingAverageLine));
  }, [movingAverageLine]);

  useEffect(() => {
    maUpperDataRef.current = movingAverageUpper;
    if (!maUpperRef.current) return;
    maUpperRef.current.setData(toLineData(movingAverageUpper));
  }, [movingAverageUpper]);

  useEffect(() => {
    maLowerDataRef.current = movingAverageLower;
    if (!maLowerRef.current) return;
    maLowerRef.current.setData(toLineData(movingAverageLower));
  }, [movingAverageLower]);

  useEffect(() => {
    volumeDataRef.current = volumes;
    if (!volumeSeriesRef.current) return;
    volumeSeriesRef.current.setData(toHistogramData(volumes));
  }, [volumes]);

  useEffect(() => {
    signalsRef.current = signals;
    if (!candleSeriesRef.current) return;
    candleSeriesRef.current.setMarkers(signals.map(toMarker));
  }, [signals]);

  useEffect(() => {
    if (!chartRef.current || !onSelectSignal) return;

    const handler = (param: MouseEventParams<Time>) => {
      const unix = toUnixTime(param.time);
      if (!unix) return;
      const matchedSignal = signalsRef.current.find((signal) => {
        const signalTime = Math.floor(new Date(signal.createdAt).getTime() / 1000);
        return signalTime === unix;
      });
      if (matchedSignal) {
        onSelectSignal(matchedSignal);
      }
    };

    chartRef.current.subscribeClick(handler);
    return () => {
      chartRef.current?.unsubscribeClick(handler);
    };
  }, [onSelectSignal]);

  const statusText = useMemo(() => {
    if (isLoading) return t("chart.status.loading");
    if (!candles.length) return t("chart.status.empty");
    return null;
  }, [candles.length, isLoading, t]);

  const lastCandle = useMemo(() => (candles.length ? candles[candles.length - 1] : undefined), [candles]);
  const lastVolume = useMemo(() => (volumes.length ? volumes[volumes.length - 1] : undefined), [volumes]);
  const lastUpdate = useMemo(() => {
    if (!lastCandle) return null;
    const date = timeToDate(lastCandle.time as Time);
    return date ? tooltipFormatter.format(date) : null;
  }, [lastCandle, tooltipFormatter]);

  return (
    <div className={clsx("relative overflow-hidden rounded-xl bg-white", className)}>
      <div ref={containerRef} style={{ height, width: "100%" }} />
      {!statusText && lastCandle ? (
        <div className="pointer-events-none absolute left-4 top-4 z-10 flex flex-wrap items-center gap-3 text-[11px] text-slate-600">
          <span className="rounded-full bg-slate-900/90 px-3 py-1 text-xs font-semibold text-white">
            {priceFormatter.format(lastCandle.close)}
          </span>
          <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-slate-500">
            {lastUpdate}
          </span>
          {lastVolume ? (
            <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-slate-500">
              {volumeLabel} {volumeFormatter.format(lastVolume.value)}
            </span>
          ) : null}
        </div>
      ) : null}
      {statusText ? (
        <div className="absolute inset-0 flex items-center justify-center bg-white/85 text-xs text-slate-500 backdrop-blur">
          {statusText}
        </div>
      ) : null}
    </div>
  );
}

function formatAxisTick(time: Time, formatter: Intl.DateTimeFormat): string {
  const date = timeToDate(time);
  return date ? formatter.format(date) : "";
}

function timeToDate(time: Time | undefined): Date | null {
  if (time === undefined || time === null) return null;
  if (typeof time === "number") return new Date(time * 1000);
  const businessDay = time as BusinessDay;
  if (
    typeof businessDay.year === "number" &&
    typeof businessDay.month === "number" &&
    typeof businessDay.day === "number"
  ) {
    return new Date(Date.UTC(businessDay.year, businessDay.month - 1, businessDay.day));
  }
  return null;
}

function toUnixTime(time: Time | undefined): number | null {
  if (time === undefined || time === null) return null;
  if (typeof time === "number") return time;
  const businessDay = time as BusinessDay;
  if (
    typeof businessDay.year === "number" &&
    typeof businessDay.month === "number" &&
    typeof businessDay.day === "number"
  ) {
    return Math.floor(Date.UTC(businessDay.year, businessDay.month - 1, businessDay.day) / 1000);
  }
  return null;
}
