"use client";

import { Fragment, useMemo } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { Clock, TrendingDown, TrendingUp, X } from "lucide-react";
import clsx from "clsx";
import type { NewsStreamEvent } from "@/lib/state/newsStreamStore";
import { CitationsList } from "./CitationsList";

type NewsPreviewModalProps = {
  isOpen: boolean;
  news?: NewsStreamEvent;
  onClose: () => void;
  onViewChain?: (event: NewsStreamEvent) => void;
};

export function NewsPreviewModal({ isOpen, news, onClose, onViewChain }: NewsPreviewModalProps) {
  const headline = news?.headline ?? "";

  const formattedTimestamp = useMemo(() => {
    if (!news) return "";
    try {
      return new Intl.DateTimeFormat("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }).format(new Date(news.timestamp));
    } catch {
      return news.timestamp;
    }
  }, [news]);

  const directionColor = news
    ? {
        bullish: "text-market-positive border-market-positive/40 bg-market-positive/10",
        bearish: "text-market-negative border-market-negative/40 bg-market-negative/10",
        neutral: "text-text-secondary border-border-secondary bg-background-tertiary/60"
      }[news.direction]
    : "";

  return (
    <Transition show={isOpen && Boolean(news)} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-[70]">
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" aria-hidden />
        </Transition.Child>

        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0 scale-95"
          enterTo="opacity-100 scale-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100 scale-100"
          leaveTo="opacity-0 scale-95"
        >
          <Dialog.Panel className="fixed inset-0 flex items-start justify-center overflow-y-auto px-4 py-10 sm:px-6 lg:px-8">
            <div className="w-full max-w-3xl rounded-2xl border border-border-primary bg-white shadow-[0_20px_50px_rgba(0,0,0,0.45)]">
              <header className="flex items-start justify-between gap-4 border-b border-border-primary px-6 py-5">
                <div className="space-y-2">
                  <Dialog.Title className="text-xl font-semibold text-text-primary">{headline}</Dialog.Title>
                  {news ? (
                    <div className="flex flex-wrap items-center gap-3 text-xs text-text-tertiary">
                      <span
                        className={clsx(
                          "inline-flex items-center gap-1 rounded-full border px-3 py-1 font-medium",
                          directionColor
                        )}
                      >
                        {news.direction === "bullish" ? (
                          <TrendingUp size={14} aria-hidden />
                        ) : news.direction === "bearish" ? (
                          <TrendingDown size={14} aria-hidden />
                        ) : null}
                        {directionLabel(news.direction)}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock size={12} aria-hidden />
                        {formattedTimestamp}
                      </span>
                      <span>置信度 {Math.round(news.confidence * 100)}%</span>
                    </div>
                  ) : null}
                </div>

                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-lg border border-border-secondary p-2 text-text-secondary transition hover:border-border-primary hover:text-text-primary"
                  aria-label="关闭新闻预览"
                >
                  <X size={18} />
                </button>
              </header>

              {news ? (
                <div className="space-y-6 px-6 py-6">
                  {news.summary ? (
                    <p className="text-sm leading-relaxed text-text-secondary">{news.summary}</p>
                  ) : (
                    <p className="text-sm text-text-tertiary">暂时没有摘要，您可以直接查看推理链获取详细分析。</p>
                  )}

                  {news.signalTags.length ? (
                    <div className="flex flex-wrap gap-2">
                      {news.signalTags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full border border-border-secondary px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-text-secondary"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  ) : null}

                  <CitationsList items={news.citations} heading="相关新闻引用" />

                  <div className="flex flex-wrap justify-end gap-3">
                    <button
                      type="button"
                      onClick={onClose}
                      className="btn btn-secondary"
                    >
                      关闭
                    </button>
                    {onViewChain ? (
                      <button
                        type="button"
                        onClick={() => onViewChain(news)}
                        className="btn btn-primary"
                      >
                        查看推理链
                      </button>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </div>
          </Dialog.Panel>
        </Transition.Child>
      </Dialog>
    </Transition>
  );
}

function directionLabel(direction: NewsStreamEvent["direction"]): string {
  switch (direction) {
    case "bullish":
      return "看多";
    case "bearish":
      return "看空";
    default:
      return "中性";
  }
}
