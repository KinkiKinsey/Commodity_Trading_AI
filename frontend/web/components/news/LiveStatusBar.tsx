"use client";

import clsx from "clsx";
import type { StreamStatus } from "@/lib/state/newsStreamStore";

type LiveStatusBarProps = {
  status: StreamStatus;
  className?: string;
};

export function LiveStatusBar({ status, className }: LiveStatusBarProps) {
  const { label, tone } = deriveStatus(status);

  return (
    <div
      className={clsx(
        "flex items-center justify-between rounded-[18px] border-2 px-5 py-4 text-xs transition-colors shadow-[6px_6px_0px_rgba(0,0,0,0.85)]",
        tone.background,
        tone.border,
        className
      )}
    >
      <div className="flex flex-col gap-1">
        <span className={clsx("font-medium", tone.text)}>{label}</span>
        {status.state === "open" && status.lastEventAt ? (
          <span className="text-[10px] text-text-secondary">
            最近事件：{new Date(status.lastEventAt).toLocaleTimeString()}
          </span>
        ) : null}
        {status.state === "error" ? (
          <span className="text-[10px] text-text-secondary">
            系统将自动重试，请检查网络或刷新页面。
          </span>
        ) : null}
      </div>
      <div className={clsx("flex h-9 w-9 items-center justify-center rounded-full border", tone.indicatorBorder)}>
        <div className={clsx("h-2 w-2 rounded-full", tone.indicatorDot)} />
      </div>
    </div>
  );
}

function deriveStatus(status: StreamStatus) {
  switch (status.state) {
    case "connecting":
      return {
        label: "正在连接实时数据…",
        tone: {
          text: "text-border-strong",
          background: "bg-bg-surface",
          border: "border-border-strong",
          indicatorBorder: "border-border-strong",
          indicatorDot: "bg-accent-neutral animate-pulse"
        }
      };
    case "open":
      return {
        label: "实时连接正常",
        tone: {
          text: "text-border-strong",
          background: "bg-bg-surface",
          border: "border-border-strong",
          indicatorBorder: "border-accent-bull/70",
          indicatorDot: "bg-accent-bull"
        }
      };
    case "error":
    default:
      return {
        label: status.message ?? "连接异常，正在重试…",
        tone: {
          text: "text-border-strong",
          background: "bg-bg-surface",
          border: "border-accent-bear/60",
          indicatorBorder: "border-accent-bear",
          indicatorDot: "bg-accent-bear animate-ping"
        }
      };
  }
}
