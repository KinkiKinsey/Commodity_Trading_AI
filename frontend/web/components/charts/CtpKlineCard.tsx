"use client";

import { useMemo, useState } from "react";
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

  const mockData = useMemo(() => generateMockBars(`${selectedSymbol}-${timeframe}`), [selectedSymbol, timeframe]);

  const candles = mockData.map(({ closeLine, ...rest }) => rest);
  const lineSeries = mockData.map(({ closeLine }) => closeLine);

  return (
    <section className="rounded-2xl border border-border-muted bg-white p-6 shadow-[0_8px_20px_rgba(15,23,42,0.08)]">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-text-secondary">CTP Kline (beta)</p>
          <h3 className="text-lg font-semibold text-text-primary">{selectedSymbol}</h3>
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
        <span>{`周期：${timeframe.toUpperCase()}`}</span>
      </footer>
    </section>
  );
}
