"use client";

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import type { CandlestickData, LineData, UTCTimestamp } from "lightweight-charts";
import { ChartShell } from "./ChartShell";
import { useCtpKline, type CtpInterval, type CtpPriceBar } from "@/lib/hooks/useCtpKline";

const CONTRACTS = ["CL2512-NYM", "CL2601-NYM", "CL2602-NYM", "CL2603-NYM", "CL2604-NYM", "CL2605-NYM"];
const TIMEFRAMES: Array<{ label: string; value: CtpInterval }> = [
  { label: "1M", value: "1m" },
  { label: "5M", value: "5m" },
  { label: "15M", value: "15m" },
  { label: "1H", value: "1h" }
];
const AUTO_REFRESH_INTERVAL = 15000;
const DEFAULT_BAR_COUNT = 360;

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

export function CtpKlineCard() {
  const [selectedSymbol, setSelectedSymbol] = useState(CONTRACTS[0]);
  const [timeframe, setTimeframe] = useState<CtpInterval>(TIMEFRAMES[1]!.value);

  const { data, isFetching, isError, refetch } = useCtpKline({
    symbol: selectedSymbol,
    interval: timeframe,
    count: DEFAULT_BAR_COUNT
  });

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      refetch();
    }, AUTO_REFRESH_INTERVAL);
    return () => window.clearInterval(intervalId);
  }, [refetch, selectedSymbol, timeframe]);

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
  const footerSource = data?.bars?.length
    ? "数据源：CTP 实时行情（ClickHouse）"
    : "数据源：CTP 实时行情（演示数据）";

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
        <ChartShell
          candles={{ data: candles }}
          lines={[
            {
              id: "close",
              data: lineSeries,
              options: {
                color: "#0f172a",
                priceLineVisible: false,
                lineWidth: 1
              }
            }
          ]}
          height={360}
        />
      </div>

      <footer className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-text-secondary">
        <span>{footerSource}</span>
        <span>{`周期：${timeframe.toUpperCase()} · ${AUTO_REFRESH_INTERVAL / 1000}s 自动刷新`}</span>
      </footer>
    </section>
  );
}
