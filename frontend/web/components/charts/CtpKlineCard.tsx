"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import type { CandlestickData, LineData, UTCTimestamp } from "lightweight-charts";
import { ChartShell } from "./ChartShell";

const CONTRACTS = ["CL2512-NYM", "CL2601-NYM", "CL2602-NYM", "CL2603-NYM", "CL2604-NYM", "CL2605-NYM"];
const TIMEFRAMES = [
  { label: "1M", value: "1m" },
  { label: "5M", value: "5m" },
  { label: "15M", value: "15m" },
  { label: "1H", value: "1h" }
];
const AUTO_REFRESH_INTERVAL = 15000;

type MockBar = CandlestickData & { closeLine: LineData };

function generateMockBars(seed: string, points = 120): MockBar[] {
  let lastClose = 70 + Math.random() * 5;
  let lastTime = Math.floor(Date.now() / 1000) - points * 60;
  const rows: MockBar[] = [];

  for (let i = 0; i < points; i += 1) {
    const volatility = 0.2 + (seed.length % 5) * 0.05;
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

export function CtpKlineCard() {
  const [selectedSymbol, setSelectedSymbol] = useState(CONTRACTS[0]);
  const [timeframe, setTimeframe] = useState(TIMEFRAMES[1].value);
  const [refreshToken, setRefreshToken] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const refreshTimeoutRef = useRef<number | null>(null);
  const dateFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }),
    []
  );

  const handleRefresh = useCallback(() => {
    if (refreshTimeoutRef.current) {
      window.clearTimeout(refreshTimeoutRef.current);
    }
    setIsRefreshing(true);
    refreshTimeoutRef.current = window.setTimeout(() => {
      setRefreshToken((token) => token + 1);
      setLastUpdated(new Date());
      setIsRefreshing(false);
      refreshTimeoutRef.current = null;
    }, 450);
  }, []);

  useEffect(() => {
    handleRefresh();
    const intervalId = window.setInterval(() => {
      handleRefresh();
    }, AUTO_REFRESH_INTERVAL);
    return () => {
      window.clearInterval(intervalId);
      if (refreshTimeoutRef.current) {
        window.clearTimeout(refreshTimeoutRef.current);
      }
    };
  }, [handleRefresh]);

  const mockData = useMemo(
    () => generateMockBars(`${selectedSymbol}-${timeframe}-${refreshToken}`),
    [selectedSymbol, timeframe, refreshToken]
  );

  const candles = mockData.map(({ closeLine, ...rest }) => rest);
  const lineSeries = mockData.map(({ closeLine }) => closeLine);
  const lastUpdatedLabel = lastUpdated ? dateFormatter.format(lastUpdated) : "--";

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
          <span
            className={clsx(
              "rounded-full px-3 py-1 font-semibold tracking-wide",
              isRefreshing ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"
            )}
          >
            {isRefreshing ? "刷新中…" : "LIVE"}
          </span>
          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={clsx(
              "rounded-full border px-3 py-1 font-semibold transition",
              isRefreshing
                ? "border-border-muted text-text-secondary"
                : "border-border-active text-text-primary hover:border-text-primary"
            )}
          >
            手动刷新
          </button>
        </div>
        <div className="flex items-center gap-1 text-xs text-text-secondary">
          <span>最后更新</span>
          <span className="font-semibold text-text-primary">{lastUpdatedLabel}</span>
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
        <span>数据源：CTP 实时行情（演示数据）</span>
        <span>{`周期：${timeframe.toUpperCase()} · ${AUTO_REFRESH_INTERVAL / 1000}s 自动刷新`}</span>
      </footer>
    </section>
  );
}
