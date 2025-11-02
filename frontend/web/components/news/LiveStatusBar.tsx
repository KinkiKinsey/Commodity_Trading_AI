"use client";

import clsx from "clsx";
import type { StreamStatus } from "@/lib/state/newsStreamStore";
import { useIntl, type TranslationKey } from "@/lib/i18n/IntlContext";

type LiveStatusBarProps = {
  status: StreamStatus;
  className?: string;
};

type ToneConfig = {
  text: string;
  background: string;
  border: string;
  indicatorBorder: string;
  indicatorDot: string;
};

type StatusDescriptor = {
  label: string;
  tone: ToneConfig;
};

export function LiveStatusBar({ status, className }: LiveStatusBarProps) {
  const { t } = useIntl();
  const { label, tone } = deriveStatus(status, t);

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
            {t("status.lastEventPrefix")}：{new Date(status.lastEventAt).toLocaleTimeString()}
          </span>
        ) : null}
        {status.state === "error" ? (
          <span className="text-[10px] text-text-secondary">{t("status.retryHint")}</span>
        ) : null}
      </div>
      <div
        className={clsx(
          "flex h-9 w-9 items-center justify-center rounded-full border",
          tone.indicatorBorder
        )}
      >
        <div className={clsx("h-2 w-2 rounded-full", tone.indicatorDot)} />
      </div>
    </div>
  );
}

function deriveStatus(status: StreamStatus, t: (key: TranslationKey) => string): StatusDescriptor {
  switch (status.state) {
    case "connecting":
      return {
        label: t("status.connecting"),
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
        label: t("status.connected"),
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
        label: status.message ?? t("status.error"),
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
