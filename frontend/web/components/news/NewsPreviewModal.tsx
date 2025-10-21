"use client";

import { Fragment, type ReactNode } from "react";
import { createPortal } from "react-dom";
import clsx from "clsx";
import type { NewsStreamEvent } from "@/lib/state/newsStreamStore";

type NewsPreviewModalProps = {
  open: boolean;
  event?: NewsStreamEvent;
  onClose: () => void;
  onViewChain: (event: NewsStreamEvent) => void;
};

export function NewsPreviewModal({ open, event, onClose, onViewChain }: NewsPreviewModalProps) {
  if (!open || !event) return null;

  return createPortal(
    <Fragment>
      <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-x-4 top-16 z-50 mx-auto max-w-3xl rounded-[22px] border-2 border-border-strong bg-white p-8 shadow-[8px_8px_0px_rgba(0,0,0,0.85)]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <span
              className={clsx(
                "terminal-text inline-flex items-center rounded-full border-2 px-3 py-0.5 text-[11px] uppercase tracking-[0.2em]",
                event.direction === "bullish" && "border-accent-bull text-accent-bull",
                event.direction === "bearish" && "border-accent-bear text-accent-bear",
                event.direction === "neutral" && "border-accent-neutral border-dashed text-accent-neutral"
              )}
            >
              {LABELS[event.direction]}
            </span>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-border-strong">{event.headline}</h2>
            <p className="mt-3 text-xs text-text-secondary">
              更新时间 {new Date(event.timestamp).toLocaleString()} · Confidence {(event.confidence * 100).toFixed(0)}%
            </p>
          </div>
          <button
            onClick={onClose}
            className="terminal-text rounded-full border-2 border-border-strong px-4 py-1 text-[11px] uppercase tracking-[0.2em] text-border-strong hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_rgba(0,0,0,0.8)]"
          >
            关闭
          </button>
        </div>

        <div className="mt-5 rounded-xl border-2 border-border-strong bg-bg-surface px-4 py-4 text-sm text-text-secondary">
          {event.summary ?? "暂未提供摘要，可直接查看推理链了解详细信息。"}
        </div>

        <div className="mt-4 flex flex-wrap gap-2 text-[10px] text-text-secondary">
          {event.signalTags.map((tag) => (
            <span key={tag} className="rounded-md border border-border-strong px-2 py-0.5 text-border-strong">
              #{tag}
            </span>
          ))}
        </div>

        {event.complianceStatus !== "clean" ? (
          <p className="mt-3 text-[10px] text-accent-bear">
            注意：该内容已触发合规屏蔽/脱敏，展示文本受到限制。
          </p>
        ) : null}

        <div className="mt-6 flex flex-wrap justify-end gap-3 text-xs">
          <button
            className="rounded-full border-2 border-border-strong bg-white px-5 py-2 text-sm font-medium text-border-strong hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_rgba(0,0,0,0.6)]"
            onClick={onClose}
          >
            稍后再看
          </button>
          <button
            className="rounded-full border-2 border-border-strong bg-border-strong px-5 py-2 text-sm font-medium text-white hover:-translate-y-0.5 hover:bg-accent-blue"
            onClick={() => onViewChain(event)}
          >
            查看推理链
          </button>
        </div>
      </div>
    </Fragment>,
    document.body
  );
}

const LABELS = {
  bullish: "利多",
  bearish: "利空",
  neutral: "中性"
} as const;
