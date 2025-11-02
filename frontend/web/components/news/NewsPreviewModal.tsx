"use client";

import { Fragment, useMemo } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { ChevronRight, Clock, ExternalLink, Loader2, TrendingDown, TrendingUp, X } from "lucide-react";
import clsx from "clsx";
import type { NewsStreamEvent } from "@/lib/state/newsStreamStore";
import { useIntl, type TranslationKey } from "@/lib/i18n/IntlContext";
import { CitationsList } from "./CitationsList";

type NewsPreviewModalProps = {
  isOpen: boolean;
  news?: NewsStreamEvent;
  onClose: () => void;
  onViewChain?: (event: NewsStreamEvent) => void;
  onRegenerateChain?: (event: NewsStreamEvent) => void;
  isRegenerating?: boolean;
  regenerateError?: string | null;
};

const DIRECTION_KEY_MAP: Record<NewsStreamEvent["direction"], TranslationKey> = {
  bullish: "sentiment.direction.bullish",
  bearish: "sentiment.direction.bearish",
  neutral: "sentiment.direction.neutral"
};

export function NewsPreviewModal({
  isOpen,
  news,
  onClose,
  onViewChain,
  onRegenerateChain,
  isRegenerating = false,
  regenerateError = null,
}: NewsPreviewModalProps) {
  const { t, locale } = useIntl();
  const headline = news?.headline ?? "";

  const formattedTimestamp = useMemo(() => {
    if (!news) return "";
    try {
      return new Intl.DateTimeFormat(locale, {
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
  }, [locale, news]);

  const directionColor = news
    ? {
        bullish: "text-market-positive border-market-positive/40 bg-market-positive/10",
        bearish: "text-market-negative border-market-negative/40 bg-market-negative/10",
        neutral: "text-text-secondary border-border-secondary bg-background-tertiary/60"
      }[news.direction]
    : "";

  const confidenceLabel = news
    ? `${t("modal.confidenceLabel")} ${Math.round((news.confidence ?? 0) * 100)}%`
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
          <Dialog.Panel className="fixed inset-0 flex items-start justify-center overflow-y-auto px-4 py-10 sm:px-6 lg:px-10">
            <div className="w-full max-w-5xl rounded-2xl border border-border-primary bg-white shadow-[0_20px_50px_rgba(0,0,0,0.45)]">
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
                        {t(DIRECTION_KEY_MAP[news.direction])}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock size={12} aria-hidden />
                        {formattedTimestamp}
                      </span>
                      <span>{confidenceLabel}</span>
                    </div>
                  ) : null}
                </div>

                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-lg border border-border-secondary p-2 text-text-secondary transition hover:border-border-primary hover:text-text-primary"
                  aria-label={t("button.close")}
                >
                  <X size={18} />
                </button>
              </header>

              {news ? (
                <div className="space-y-6 px-6 py-6">
                  {news.summary ? (
                    <p className="text-sm leading-relaxed text-text-secondary">{news.summary}</p>
                  ) : (
                    <p className="text-sm text-text-tertiary">{t("modal.noSummary")}</p>
                  )}

                  {news.complianceStatus !== "clean" ? (
                    <div className="rounded-lg border border-market-negative/30 bg-market-negative/10 px-4 py-3 text-xs text-market-negative">
                      {news.complianceStatus === "blocked"
                        ? t("modal.compliance.blocked")
                        : t("modal.compliance.masked")}
                    </div>
                  ) : null}

                  {news.chain_of_thought && news.chain_of_thought.length > 0 ? (
                    <div className="space-y-4">
                      <h3 className="text-sm font-semibold text-text-primary">{t("modal.chainTitle")}</h3>
                      <ol className="relative space-y-0">
                        {news.chain_of_thought.map((step, index) => (
                          <li key={step.id} className="relative flex items-start gap-3 pb-6 last:pb-0">
                            <div
                              className="relative shrink-0"
                              style={{ width: "6px", paddingTop: "6px", minHeight: "24px" }}
                            >
                              <div
                                className="absolute left-1/2 top-[6px] z-10 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-gray-900"
                                aria-hidden
                              />
                              {index < news.chain_of_thought.length - 1 ? (
                                <div
                                  className="absolute left-1/2 top-[12px] w-[1px] -translate-x-1/2 bg-gray-300"
                                  style={{ height: "calc(100% + 24px)" }}
                                  aria-hidden
                                />
                              ) : null}
                            </div>

                            <div className="min-w-0 flex-1 space-y-2" style={{ paddingTop: "2px" }}>
                              <div className="flex items-start justify-between gap-3">
                                <p className="text-sm leading-relaxed text-text-secondary">{step.text}</p>
                                {step.url ? (
                                  <a
                                    href={ensureHttp(step.url)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 rounded border border-border-secondary px-2 py-1 text-[11px] text-text-secondary transition hover:border-border-primary hover:text-text-primary"
                                  >
                                    {t("modal.linkLabel")}
                                    <ExternalLink size={12} aria-hidden />
                                  </a>
                                ) : null}
                              </div>

                              {step.evidence ? (
                                <div className="flex items-center gap-2 text-xs text-text-tertiary">
                                  <ChevronRight size={14} aria-hidden />
                                  <span>{step.evidence}</span>
                                </div>
                              ) : null}
                            </div>
                          </li>
                        ))}
                      </ol>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <h3 className="text-sm font-semibold text-text-primary">{t("modal.chainTitle")}</h3>
                      <p className="text-sm text-text-tertiary">{t("modal.generateChainHint")}</p>
                      {onRegenerateChain ? (
                        <div className="relative inline-flex">
                          <div
                            aria-hidden
                            className="pointer-events-none absolute inset-0 rounded-xl opacity-90"
                            style={{
                              background: "linear-gradient(120deg, #60a5fa, #a855f7, #f97316, #22d3ee, #60a5fa)",
                              backgroundSize: "300% 300%",
                              animation: "gradientGlow 6s ease-in-out infinite",
                              filter: "blur(0.4px) drop-shadow(0 0 12px rgba(99,102,241,0.25))",
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => news && onRegenerateChain(news)}
                            disabled={isRegenerating}
                            className="relative z-10 inline-flex items-center gap-2 rounded-xl bg-white/95 px-4 py-2 text-sm font-medium text-text-primary shadow-[0_10px_24px_rgba(15,23,42,0.12)] backdrop-blur transition hover:bg-background-tertiary/60 disabled:cursor-not-allowed disabled:opacity-70"
                          >
                            {isRegenerating ? <Loader2 size={16} className="animate-spin" aria-hidden /> : null}
                            {t("modal.generateChain")}
                          </button>
                        </div>
                      ) : null}
                      {regenerateError ? (
                        <p className="text-xs text-market-negative">{regenerateError}</p>
                      ) : null}
                    </div>
                  )}

                  <CitationsList items={news.citations} heading={t("modal.citationsHeading")} />
                </div>
              ) : null}
            </div>
          </Dialog.Panel>
        </Transition.Child>
      </Dialog>
    </Transition>
  );
}

function ensureHttp(url: string): string {
  return url.startsWith("http") ? url : `https://${url}`;
}
