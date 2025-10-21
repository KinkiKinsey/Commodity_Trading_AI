"use client";

import clsx from "clsx";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";
import type { PlaceholderPoint } from "@/lib/mock/generatePlaceholderSeries";

type IndexSignalChartProps = {
  series: PlaceholderPoint[];
  signals: IndexSignal[];
  className?: string;
};

export function IndexSignalChart({ series, signals, className }: IndexSignalChartProps) {
  if (!series.length) {
    return (
      <div className={clsx("flex h-full items-center justify-center text-xs text-text-secondary", className)}>
        暂无行情数据，等待刷新。
      </div>
    );
  }

  const width = 640;
  const height = 200;
  const paddingX = 24;
  const paddingY = 24;

  const values = series.map((point) => point.close);
  const min = Math.min(...values);
  const max = Math.max(...values);

  const scaleX = (index: number) =>
    paddingX + (index / Math.max(1, series.length - 1)) * (width - paddingX * 2);

  const scaleY = (value: number) => {
    if (max === min) return height / 2;
    const normalized = (value - min) / (max - min);
    return height - paddingY - normalized * (height - paddingY * 2);
  };

  const path = series
    .map((point, index) => `${index === 0 ? "M" : "L"}${scaleX(index).toFixed(2)},${scaleY(point.close).toFixed(2)}`)
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={clsx("h-full w-full text-text-secondary", className)}
      role="img"
      aria-label="指数价格曲线"
    >
      <defs>
        <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="rgba(0, 178, 169, 0.35)" />
          <stop offset="100%" stopColor="rgba(0, 178, 169, 0.05)" />
        </linearGradient>
      </defs>

      <rect
        x={1}
        y={1}
        width={width - 2}
        height={height - 2}
        fill="rgba(255,255,255,0.02)"
        stroke="rgba(255,255,255,0.05)"
        strokeWidth={1}
        rx={12}
      />

      <path d={path} fill="none" stroke="#00B2A9" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

      <path
        d={`${path} L${scaleX(series.length - 1)},${height - paddingY} L${scaleX(0)},${height - paddingY} Z`}
        fill="url(#chartGradient)"
        opacity={0.6}
      />

      {signals.map((signal) => {
        const index = findClosestIndex(series, signal.createdAt);
        if (index === -1) return null;
        const x = scaleX(index);
        const y = scaleY(series[index].close);
        const color = signal.signalType === "buy" ? "#00B2A9" : "#FF5C5C";
        return (
          <g key={signal.signalId} transform={`translate(${x}, ${y})`}>
            <circle r={5} fill={color} opacity={0.9} />
            <circle r={10} fill={color} opacity={0.12} />
          </g>
        );
      })}

      <text x={paddingX} y={paddingY - 6} fontSize={10} fill="rgba(229,234,245,0.6)">
        最新价：{series[series.length - 1].close.toFixed(2)}
      </text>
      <text x={width - paddingX} y={paddingY - 6} fontSize={10} fill="rgba(229,234,245,0.4)" textAnchor="end">
        范围：{min.toFixed(2)} - {max.toFixed(2)}
      </text>
    </svg>
  );
}

function findClosestIndex(series: PlaceholderPoint[], timestamp: string) {
  const target = new Date(timestamp).getTime();
  let minDiff = Number.POSITIVE_INFINITY;
  let minIndex = -1;

  series.forEach((point, index) => {
    const diff = Math.abs(new Date(point.timestamp).getTime() - target);
    if (diff < minDiff) {
      minDiff = diff;
      minIndex = index;
    }
  });

  return minIndex;
}
