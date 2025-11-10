"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import type {
  CandlestickData,
  DeepPartial,
  LineData,
  LineSeriesPartialOptions,
  SeriesMarker,
  UTCTimestamp
} from "lightweight-charts";
import { ChartShell, type LineSeriesConfig } from "./ChartShell";
import {
  useCtpKline,
  type CtpIndicatorDefinition,
  type CtpIndicatorSeriesLine,
  type CtpInterval,
  type CtpPriceBar,
  type CtpSignal
} from "@/lib/hooks/useCtpKline";
import { useCtpRealtime } from "@/lib/hooks/useCtpRealtime";
import { CtpIndicatorPanel } from "./CtpIndicatorPanel";
import { CtpSignalTimeline } from "./CtpSignalTimeline";

const CONTRACTS = ["CL2512-NYM", "CL2601-NYM", "CL2602-NYM", "CL2603-NYM", "CL2604-NYM", "CL2605-NYM"];
const TIMEFRAMES: Array<{ label: string; value: CtpInterval }> = [
  { label: "1M", value: "1m" },
  { label: "5M", value: "5m" },
  { label: "15M", value: "15m" },
  { label: "1H", value: "1h" }
];
const AUTO_REFRESH_INTERVAL = 15000;
const DEFAULT_BAR_COUNT = 360;

type IndicatorLineConfig = LineSeriesConfig;

type IndicatorFactory = (candles: CandlestickData[]) => IndicatorLineConfig[];

type MockBar = CandlestickData & { closeLine: LineData };
type ChartPoint = { candle: CandlestickData; line: LineData };

function generateMockBars(seed: string, points = 180): MockBar[] {
  let lastClose = 70 + Math.random() * 5;
  let lastTime = Math.floor(Date.now() / 1000) - points * 60;
  const rows: MockBar[] = [];

  for (let i = 0; i < points; i += 1) {
    const volatility = 0.15 + (seed.length % 5) * 0.05;
    const open = lastClose;
    const close = open + (Math.random() - 0.5) * volatility;
    const high = Math.max(open, close) + Math.random() * volatility;
    const low = Math.min(open, close) - Math.random() * volatility;
    const time = (lastTime += 60) as UTCTimestamp;
    lastClose = close;

    rows.push({
      time,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      closeLine: { time, value: Number(close.toFixed(2)) }
    });
  }

  return rows;
}

function convertApiBars(bars: CtpPriceBar[]): ChartPoint[] {
  return bars.map((bar) => {
    const time = Math.floor(new Date(bar.timestamp).getTime() / 1000) as UTCTimestamp;
    const open = Number(bar.open);
    const high = Number(bar.high);
    const low = Number(bar.low);
    const close = Number(bar.close);

    return {
      candle: { time, open, high, low, close },
      line: { time, value: close }
    };
  });
}

function convertMockBars(bars: MockBar[]): ChartPoint[] {
  return bars.map(({ closeLine, ...rest }) => ({
    candle: rest,
    line: closeLine
  }));
}

function buildSmaLine(id: string, candles: CandlestickData[], window = 12, color = "#0ea5e9"): IndicatorLineConfig[] {
  if (!candles.length || window <= 1) {
    return [];
  }
  const buffer: number[] = [];
  let sum = 0;
  const data: LineData[] = [];

  candles.forEach((candle) => {
    const close = candle.close;
    buffer.push(close);
    sum += close;
    if (buffer.length > window) {
      sum -= buffer.shift() ?? 0;
    }
    if (buffer.length === window) {
      data.push({
        time: candle.time,
        value: Number((sum / window).toFixed(2))
      });
    }
  });

  if (!data.length) {
    return [];
  }

  return [
    {
      id,
      data,
      options: { color, lineWidth: 2, priceLineVisible: false } as DeepPartial<LineSeriesPartialOptions>
    }
  ];
}

function buildBollingerLines(candles: CandlestickData[], window = 20, multiplier = 2): IndicatorLineConfig[] {
  if (!candles.length || window <= 1) {
    return [];
  }
  const buffer: number[] = [];
  let sum = 0;
  let sumSquares = 0;
  const upper: LineData[] = [];
  const lower: LineData[] = [];

  candles.forEach((candle) => {
    const close = candle.close;
    buffer.push(close);
    sum += close;
    sumSquares += close * close;
    if (buffer.length > window) {
      const removed = buffer.shift() ?? 0;
      sum -= removed;
      sumSquares -= removed * removed;
    }
    if (buffer.length === window) {
      const mean = sum / window;
      const variance = Math.max(sumSquares / window - mean * mean, 0);
      const std = Math.sqrt(variance);
      upper.push({ time: candle.time, value: Number((mean + multiplier * std).toFixed(2)) });
      lower.push({ time: candle.time, value: Number((mean - multiplier * std).toFixed(2)) });
    }
  });

  return [
    {
      id: "indicator-bband-upper",
      data: upper,
      options: { color: "#38bdf8", lineStyle: 2, lineWidth: 1 } as DeepPartial<LineSeriesPartialOptions>
    },
    {
      id: "indicator-bband-lower",
      data: lower,
      options: { color: "#38bdf8", lineStyle: 2, lineWidth: 1 } as DeepPartial<LineSeriesPartialOptions>
    }
  ].filter((line) => line.data.length);
}

function buildChannelLines(
  candles: CandlestickData[],
  idPrefix: string,
  color: string,
  multiplier = 0.25
): IndicatorLineConfig[] {
  if (!candles.length) {
    return [];
  }
  const upper: LineData[] = [];
  const lower: LineData[] = [];

  candles.forEach((candle) => {
    const range = Math.max(candle.high - candle.low, 0.01);
    upper.push({
      time: candle.time,
      value: Number((candle.high + range * multiplier).toFixed(2))
    });
    lower.push({
      time: candle.time,
      value: Number((candle.low - range * multiplier).toFixed(2))
    });
  });

  return [
    {
      id: `${idPrefix}-upper`,
      data: upper,
      options: { color, lineStyle: 1, lineWidth: 1 } as DeepPartial<LineSeriesPartialOptions>
    },
    {
      id: `${idPrefix}-lower`,
      data: lower,
      options: { color, lineStyle: 1, lineWidth: 1 } as DeepPartial<LineSeriesPartialOptions>
    }
  ];
}

const INDICATOR_LINE_FACTORIES: Record<string, IndicatorFactory> = {
  MLMA: (candles) => buildSmaLine("indicator-mlma", candles, 12, "#0ea5e9"),
  LONGTERM: (candles) => buildSmaLine("indicator-longterm", candles, 26, "#f97316"),
  BBAND: (candles) => buildBollingerLines(candles),
  BSSIDE: (candles) => buildChannelLines(candles, "indicator-bsside", "#f97316", 0.35),
  SMC: (candles) => buildChannelLines(candles, "indicator-smc", "#22c55e", 0.18)
};

const DEFAULT_INDICATOR_COLORS: Record<string, string> = {
  MLMA: "#0ea5e9",
  LONGTERM: "#f97316",
  BBAND: "#38bdf8",
  BSSIDE: "#f97316",
  SMC: "#22c55e"
};

function toUtcTimestamp(value: string): UTCTimestamp | null {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return Math.floor(date.getTime() / 1000) as UTCTimestamp;
}

function convertSeriesToLineData(series: CtpIndicatorSeriesLine["series"]): LineData[] {
  const data: LineData[] = [];
  series.forEach((point) => {
    const time = toUtcTimestamp(point.timestamp);
    if (!time) {
      return;
    }
    data.push({
      time,
      value: point.value
    });
  });
  return data;
}

export function CtpKlineCard() {
  const [selectedSymbol, setSelectedSymbol] = useState(CONTRACTS[0]);
  const [timeframe, setTimeframe] = useState<CtpInterval>(TIMEFRAMES[1]!.value);

  const { data, isFetching, isError, refetch } = useCtpKline({
    symbol: selectedSymbol,
    interval: timeframe,
    count: DEFAULT_BAR_COUNT
  });
  const realtimeQuery = useCtpRealtime(selectedSymbol);
  const realtimePriceFormatter = useMemo(
    () =>
      new Intl.NumberFormat(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }),
    []
  );
  const indicatorDefinitions = useMemo(() => data?.indicators ?? [], [data?.indicators]);
  const indicatorSeriesFromApi = useMemo(() => data?.indicator_series ?? [], [data?.indicator_series]);
  const signalPayload = useMemo(() => data?.signals ?? [], [data?.signals]);
  const indicatorSignature = useMemo(
    () => indicatorDefinitions.map((indicator) => indicator.key.toUpperCase()).join("|"),
    [indicatorDefinitions]
  );
  const [indicatorSelection, setIndicatorSelection] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      refetch();
    }, AUTO_REFRESH_INTERVAL);
    return () => window.clearInterval(intervalId);
  }, [refetch, selectedSymbol, timeframe]);

  useEffect(() => {
    if (!indicatorDefinitions.length) {
      setIndicatorSelection({});
      return;
    }
    setIndicatorSelection((prev) => {
      const next: Record<string, boolean> = {};
      indicatorDefinitions.forEach((indicator, index) => {
        const normalizedKey = indicator.key.toUpperCase();
        next[normalizedKey] = prev[normalizedKey] ?? index === 0;
      });
      return next;
    });
  }, [indicatorSignature, indicatorDefinitions]);

  const mockBars = useMemo(
    () => generateMockBars(`${selectedSymbol}-${timeframe}`),
    [selectedSymbol, timeframe]
  );
  const mockChartPoints = useMemo(() => convertMockBars(mockBars), [mockBars]);

  const apiChartPoints = useMemo(() => {
    if (!data?.bars?.length) {
      return null;
    }
    return convertApiBars(data.bars);
  }, [data?.bars]);

  const chartPoints = apiChartPoints ?? mockChartPoints;
  const candles = chartPoints.map((point) => point.candle);
  const lineSeries = chartPoints.map((point) => point.line);
  const fallbackIndicatorSupportMap = useMemo(() => {
    const map: Record<string, boolean> = {};
    Object.keys(INDICATOR_LINE_FACTORIES).forEach((key) => {
      map[key] = true;
    });
    return map;
  }, []);
  const indicatorSupportMap = useMemo(() => {
    if (indicatorSeriesFromApi.length) {
      return indicatorSeriesFromApi.reduce((acc, series) => {
        acc[series.indicator_key.toUpperCase()] = true;
        return acc;
      }, {} as Record<string, boolean>);
    }
    return fallbackIndicatorSupportMap;
  }, [indicatorSeriesFromApi, fallbackIndicatorSupportMap]);
  const indicatorLinesFromApi = useMemo<IndicatorLineConfig[]>(() => {
    if (!indicatorSeriesFromApi.length) {
      return [];
    }
    const lines: IndicatorLineConfig[] = [];
    indicatorSeriesFromApi.forEach((series) => {
      const normalizedKey = series.indicator_key.toUpperCase();
      if (!indicatorSelection[normalizedKey]) {
        return;
      }
      const lineData = convertSeriesToLineData(series.series);
      if (!lineData.length) {
        return;
      }
      const color = series.color ?? DEFAULT_INDICATOR_COLORS[normalizedKey] ?? "#7c3aed";
      lines.push({
        id: `${series.indicator_key}-${series.line_id}`,
        data: lineData,
        options: {
          color,
          lineWidth: 2,
          priceLineVisible: false
        } as DeepPartial<LineSeriesPartialOptions>
      });
    });
    return lines;
  }, [indicatorSeriesFromApi, indicatorSelection]);
  const indicatorFallbackLines = useMemo(() => {
    if (indicatorLinesFromApi.length || !candles.length || !indicatorDefinitions.length) {
      return [];
    }
    return indicatorDefinitions.flatMap((indicator) => {
      const normalizedKey = indicator.key.toUpperCase();
      if (!indicatorSelection[normalizedKey]) {
        return [];
      }
      const factory = INDICATOR_LINE_FACTORIES[normalizedKey];
      if (!factory) {
        return [];
      }
      return factory(candles);
    });
  }, [candles, indicatorDefinitions, indicatorSelection, indicatorLinesFromApi.length]);
  const indicatorLines = indicatorLinesFromApi.length ? indicatorLinesFromApi : indicatorFallbackLines;
  const signalMarkers = useMemo<SeriesMarker<CandlestickData["time"]>[]>(() => {
    if (!signalPayload.length) {
      return [];
    }
    const markers: SeriesMarker<CandlestickData["time"]>[] = [];
    signalPayload.forEach((signal) => {
      const time = toUtcTimestamp(signal.timestamp);
      if (!time) {
        return;
      }
      const isBuy = signal.signal_type === "buy";
      markers.push({
        time,
        position: isBuy ? "belowBar" : "aboveBar",
        color: isBuy ? "#16a34a" : "#dc2626",
        shape: isBuy ? "arrowUp" : "arrowDown",
        text: isBuy ? "BUY" : "SELL"
      });
    });
    return markers;
  }, [signalPayload]);
  const chartLines = useMemo<LineSeriesConfig[]>(
    () => [
      {
        id: "close",
        data: lineSeries,
        options: {
          color: "#0f172a",
          priceLineVisible: false,
          lineWidth: 1
        } as DeepPartial<LineSeriesPartialOptions>
      },
      ...indicatorLines
    ],
    [lineSeries, indicatorLines]
  );

  const dateFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }),
    []
  );

  const lastUpdatedLabel = useMemo(() => {
    if (data?.metadata?.fetched_at) {
      return dateFormatter.format(new Date(data.metadata.fetched_at));
    }
    return "--";
  }, [data?.metadata?.fetched_at, dateFormatter]);

  const badgeLabel = isFetching ? "刷新中…" : data?.bars?.length ? "LIVE" : "演示数据";
  const badgeTone = isFetching
    ? "bg-amber-100 text-amber-700"
    : data?.bars?.length
      ? "bg-emerald-100 text-emerald-700"
      : "bg-slate-200 text-slate-600";
  const realtimeLatency =
    typeof realtimeQuery.data?.metadata?.data_latency_seconds === "number"
      ? Math.round(realtimeQuery.data.metadata.data_latency_seconds)
      : null;
  const footerSource = data?.bars?.length
    ? "数据源：CTP 实时行情（ClickHouse）"
    : "数据源：CTP 实时行情（演示数据）";
  const handleIndicatorToggle = useCallback((key: string) => {
    setIndicatorSelection((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  }, []);

  return (
    <section className="rounded-2xl border border-border-muted bg-white p-6 shadow-[0_8px_20px_rgba(15,23,42,0.08)]">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-[0.2em] text-text-secondary">CTP Kline (beta)</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-lg font-semibold text-text-primary">{selectedSymbol}</h3>
            <span className="text-[11px] uppercase tracking-[0.25em] text-text-secondary">{timeframe}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className={clsx("rounded-full px-3 py-1 font-semibold tracking-wide", badgeTone)}>{badgeLabel}</span>
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className={clsx(
              "rounded-full border px-3 py-1 font-semibold transition",
              isFetching
                ? "border-border-muted text-text-secondary"
                : "border-border-active text-text-primary hover:border-text-primary"
            )}
          >
            手动刷新
          </button>
        </div>
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <span>最后更新</span>
          <span className="font-semibold text-text-primary">{lastUpdatedLabel}</span>
          {data?.metadata?.data_latency_seconds !== undefined ? (
            <span className="rounded-full bg-bg-alt px-2 py-[2px] text-[10px] text-text-secondary">
              延迟 {Math.round(data.metadata.data_latency_seconds)}s
            </span>
          ) : null}
        </div>
        {realtimeQuery.data ? (
          <div className="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
            <span>CTP Tick</span>
            <span className="font-semibold text-text-primary">
              {realtimePriceFormatter.format(realtimeQuery.data.last_price ?? 0)}
            </span>
            {realtimeLatency !== null ? (
              <span className="rounded-full bg-bg-alt px-2 py-[2px] text-[10px]">{`RT 延迟 ${realtimeLatency}s`}</span>
            ) : null}
          </div>
        ) : null}
        <div className="flex items-center gap-2 text-xs">
          {TIMEFRAMES.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setTimeframe(option.value)}
              className={clsx(
                "rounded-full border px-2 py-1 font-semibold",
                timeframe === option.value
                  ? "border-text-primary bg-text-primary text-white"
                  : "border-border-muted text-text-secondary hover:text-text-primary"
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </header>

      {isError ? (
        <p className="mt-3 text-xs text-market-negative">接口暂不可用，已使用演示数据。</p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2 text-sm text-text-secondary">
        {CONTRACTS.map((contract) => (
          <button
            key={contract}
            type="button"
            onClick={() => setSelectedSymbol(contract)}
            className={clsx(
              "rounded-full border px-3 py-1 text-xs uppercase tracking-[0.1em]",
              selectedSymbol === contract
                ? "border-black bg-black text-white"
                : "border-border-muted text-text-secondary hover:border-border-active"
            )}
          >
            {contract}
          </button>
        ))}
      </div>

      <div className="mt-6">
        <ChartShell candles={{ data: candles }} lines={chartLines} markers={signalMarkers} height={360} />
      </div>

      {data?.indicators?.length ? (
        <div className="mt-6">
          <CtpIndicatorPanel
            indicators={data.indicators}
            selection={indicatorSelection}
            onToggle={handleIndicatorToggle}
            supportedMap={indicatorSupportMap}
          />
        </div>
      ) : null}
      {data?.signals?.length ? (
        <div className="mt-6">
          <CtpSignalTimeline signals={data.signals} />
        </div>
      ) : null}

      <footer className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-text-secondary">
        <span>{footerSource}</span>
        <span>{`周期：${timeframe.toUpperCase()} · ${AUTO_REFRESH_INTERVAL / 1000}s 自动刷新`}</span>
      </footer>
    </section>
  );
}
