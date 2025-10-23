"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { useNewsStream } from "@/lib/hooks/useNewsStream";
import { useNewsStreamStore, NewsStreamEvent } from "@/lib/state/newsStreamStore";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";
import { SentimentDial } from "@/components/news/SentimentDial";
import { LiveStatusBar } from "@/components/news/LiveStatusBar";
import { NewsPreviewModal } from "@/components/news/NewsPreviewModal";
import { ChainOfThoughtDrawer } from "@/components/news/ChainOfThoughtDrawer";
import { IndexSignalChart } from "@/components/news/IndexSignalChart";
import { generatePlaceholderSeries } from "@/lib/mock/generatePlaceholderSeries";
import { usePricingKline } from "@/lib/hooks/usePricingKline";
import { useIntl } from "@/lib/i18n/IntlContext";

const DEFAULT_SYMBOL = "CL=F";
const SYMBOL_OPTIONS = [
  { label: "WTI Crude", value: "CL=F" },
  { label: "Brent Crude", value: "BZ=F" },
  { label: "Gold", value: "GC=F" },
  { label: "DXY Index", value: "DX-Y.NYB" }
];

const TIME_RANGE_OPTIONS: { label: string; value: "1h" | "6h" | "24h" | "all" }[] = [
  { label: "1H", value: "1h" },
  { label: "6H", value: "6h" },
  { label: "24H", value: "24h" },
  { label: "All", value: "all" }
];

const DIRECTION_LABELS_ZH: Record<"all" | "bullish" | "bearish" | "neutral", string> = {
  all: "全部",
  bullish: "利多",
  bearish: "利空",
  neutral: "中性"
};

const DIRECTION_LABELS_EN: Record<"all" | "bullish" | "bearish" | "neutral", string> = {
  all: "All",
  bullish: "Bullish",
  bearish: "Bearish",
  neutral: "Neutral"
};

const SYMBOL_TICKER_MAP: Record<string, string> = {
  "CL=F": "CLZ25.NYM",
  "BZ=F": "BZ=F",
  "GC=F": "GC=F",
  "DX-Y.NYB": "DX-Y.NYB"
};

export default function NewsRealtimePage() {
  const [selectedSymbol, setSelectedSymbol] = useState(DEFAULT_SYMBOL);
  const [directionFilter, setDirectionFilter] = useState<"all" | "bullish" | "bearish" | "neutral">("all");
  const [timeRange, setTimeRange] = useState<"1h" | "6h" | "24h" | "all">("24h");
  const [searchTerm, setSearchTerm] = useState("");

  const { locale, setLocale, t } = useIntl();

  useNewsStream();

  const setStreamStatus = useNewsStreamStore((state) => state.setStreamStatus);
  const streamStatus = useNewsStreamStore((state) => state.streamStatus);

  const allNews = useNewsStreamStore((state) =>
    state.order.map((id) => state.events.get(id)).filter((evt): evt is NewsStreamEvent => Boolean(evt))
  );

  const resolvedTicker = SYMBOL_TICKER_MAP[selectedSymbol] ?? selectedSymbol;
  const { query: pricingQuery, series: fetchedSeries, signals: fetchedSignals } = usePricingKline(resolvedTicker);

  const priceSeries = fetchedSeries.length > 0 ? fetchedSeries : generatePlaceholderSeries();
  const signals = fetchedSignals;
  const signalsLoading = pricingQuery.isLoading || pricingQuery.isFetching;
  const signalsError =
    pricingQuery.isError && pricingQuery.error instanceof Error ? pricingQuery.error.message : undefined;

  const directionLabels = locale === "zh-CN" ? DIRECTION_LABELS_ZH : DIRECTION_LABELS_EN;

  const filteredNews = useMemo(() => {
    const now = Date.now();
    const windowMap = {
      "1h": 60 * 60 * 1000,
      "6h": 6 * 60 * 60 * 1000,
      "24h": 24 * 60 * 60 * 1000
    } as const;

    return allNews
      .filter((evt) => (directionFilter === "all" ? true : evt.direction === directionFilter))
      .filter((evt) => {
        if (timeRange === "all") return true;
        const diff = now - new Date(evt.timestamp).getTime();
        return diff <= windowMap[timeRange];
      })
      .filter((evt) => {
        if (!searchTerm.trim()) return true;
        const keyword = searchTerm.trim().toLowerCase();
        const haystack = [
          evt.headline,
          evt.summary ?? "",
          evt.chain_of_thought.map((step) => step.text).join(" "),
          evt.signalTags.join(" ")
        ]
          .join(" ")
          .toLowerCase();
        return haystack.includes(keyword);
      })
      .slice(0, 20);
  }, [allNews, directionFilter, timeRange, searchTerm]);

  const latestEvent = filteredNews[0] ?? allNews[0];
  const [previewOpen, setPreviewOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeEvent, setActiveEvent] = useState<NewsStreamEvent | undefined>(undefined);

  const handleSignalSelect = useCallback(
    (signal: IndexSignal) => {
      const targetEvent =
        allNews.find((event) => event.eventId === signal.newsId) ||
        allNews.find((event) => event.signal?.signalId === signal.signalId);
      if (targetEvent) {
        setActiveEvent(targetEvent);
        setPreviewOpen(true);
      }
    },
    [allNews, setActiveEvent, setPreviewOpen]
  );

  useEffect(() => {
    setDirectionFilter("all");
    setTimeRange("24h");
    setSearchTerm("");
  }, [selectedSymbol]);

  const statusMessage = useMemo(() => {
    if (streamStatus.state === "connecting") {
      return t("status.connecting");
    }
    if (streamStatus.state === "error") {
      return streamStatus.message ?? t("status.error");
    }
    return t("status.connected");
  }, [streamStatus, t]);

  const lastEventAt = streamStatus.state === "open" ? streamStatus.lastEventAt : undefined;
  const isStale = lastEventAt ? Date.now() - lastEventAt > 120_000 : false;
  const showReconnect = streamStatus.state === "error" || isStale;
  const connectionMessage = streamStatus.state === "error"
    ? streamStatus.message ?? t("banner.error")
    : t("banner.stale");

  const handleManualRefresh = useCallback(() => {
    window.location.reload();
  }, []);

  const localeToggleLabel = locale === "zh-CN" ? "EN" : "中文";

  return (
    <main className="min-h-screen bg-bg-primary px-6 py-10 text-text-primary">
      {showReconnect ? (
        <div className="mx-auto mb-6 flex max-w-7xl flex-wrap items-center justify-between gap-3 rounded-[18px] border-2 border-accent-neutral bg-white px-4 py-3 shadow-[5px_5px_0px_rgba(0,0,0,0.75)]">
          <span className="text-sm text-border-strong">{connectionMessage}</span>
          <button
            onClick={handleManualRefresh}
            className="terminal-text rounded-full border-2 border-border-strong bg-border-strong px-4 py-1 text-[11px] uppercase tracking-[0.2em] text-white transition hover:-translate-y-0.5 hover:bg-accent-blue"
          >
            {t("button.refreshData")}
          </button>
        </div>
      ) : null}

      <div className="mx-auto flex max-w-7xl flex-col gap-8 lg:flex-row">
        <section className="flex w-full flex-col gap-6 lg:w-3/4">
          <header className="flex flex-col gap-4 rounded-[18px] border-2 border-border-strong bg-bg-surface p-6 shadow-[6px_6px_0px_0px_rgba(0,0,0,0.9)]">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="terminal-text text-[11px] uppercase tracking-[0.3em] text-border-strong">{t("header.liveFeed")}</p>
                <h1 className="mt-2 text-2xl font-semibold tracking-tight text-border-strong">{t("header.title")}</h1>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge variant={streamStatus.state}>{statusMessage}</StatusBadge>
                <button
                  onClick={() => setLocale(locale === "zh-CN" ? "en-US" : "zh-CN")}
                  className="terminal-text rounded-full border-2 border-border-strong bg-white px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-border-strong transition hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_rgba(0,0,0,0.6)]"
                >
                  {localeToggleLabel}
                </button>
              </div>
            </div>
            <div className="flex w-full flex-wrap items-center gap-3">
              <select
                className="rounded-full border-2 border-border-strong bg-white px-4 py-2 text-sm font-medium text-border-strong shadow-[3px_3px_0px_0px_rgba(0,0,0,0.8)] transition hover:-translate-y-0.5"
                value={selectedSymbol}
                onChange={(event) => setSelectedSymbol(event.target.value)}
              >
                {SYMBOL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value} className="bg-bg-primary text-text-primary">
                    {option.label}
                  </option>
                ))}
              </select>

              <div className="flex flex-wrap items-center gap-2 text-xs">
                {(["all", "bullish", "bearish", "neutral"] as const).map((value) => (
                  <button
                    key={value}
                    onClick={() => setDirectionFilter(value)}
                    className={clsx(
                      "rounded-full border px-3 py-1 transition-colors",
                      directionFilter === value
                        ? "border-accent-neutral bg-accent-neutral/10 text-accent-neutral"
                        : "border-border-strong text-text-secondary hover:border-accent-neutral/50"
                    )}
                  >
                    {directionLabels[value]}
                  </button>
                ))}

              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {TIME_RANGE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTimeRange(option.value)}
                    className={clsx(
                      "rounded-full border px-3 py-1 transition-colors",
                      timeRange === option.value
                        ? "border-border-strong bg-border-strong text-white"
                        : "border-border-strong text-text-secondary hover:border-accent-neutral/50"
                    )}
                  >
                    {option.label}
                  </button>
                ))}
              </div>

              <div className="min-w-[220px] flex-1">
                <input
                  className="w-full rounded-full border-2 border-border-strong bg-white px-4 py-2 text-sm text-border-strong shadow-[3px_3px_0px_0px_rgba(0,0,0,0.6)] outline-none transition focus:-translate-y-0.5 focus:border-accent-blue"
                  placeholder={t("filters.searchPlaceholder")}
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                />
              </div>
            </div>
          </header>

          <section className="rounded-[18px] border-2 border-border-strong bg-bg-surface p-6 shadow-[6px_6px_0px_0px_rgba(0,0,0,0.9)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="terminal-text text-[11px] uppercase tracking-[0.25em] text-border-strong">{t("panel.signals")}</p>
                <h2 className="text-lg font-semibold text-border-strong">{t("panel.signals")}</h2>
              </div>
              <span className="terminal-text text-[11px] text-text-secondary">symbol / {selectedSymbol}</span>
            </div>
            <div className="mt-4 h-64 w-full overflow-hidden rounded-[14px] border-2 border-border-strong bg-white">
              <IndexSignalChart series={priceSeries} signals={signals} />
            </div>
            <SignalsList
              signals={signals}
              isLoading={signalsLoading}
              error={signalsError}
              t={t}
              onSelect={handleSignalSelect}
            />
          </section>

          <section className="rounded-[18px] border-2 border-border-strong bg-bg-surface p-6 shadow-[6px_6px_0px_0px_rgba(0,0,0,0.9)]">
            <div className="flex items-end justify-between">
              <div>
                <p className="terminal-text text-[11px] uppercase tracking-[0.25em] text-border-strong">{t("panel.latest")}</p>
                <h2 className="text-lg font-semibold text-border-strong">{t("panel.latest")}</h2>
              </div>
              <span className="terminal-text text-[11px] text-text-secondary">
                {filteredNews.length} {t("panel.entries")} · {selectedSymbol} · {directionLabels[directionFilter]}
              </span>
            </div>
            <div className="mt-4 flex flex-col gap-3">
              {filteredNews.length === 0 ? (
                <EmptyState message={t("empty.news")} />
              ) : (
                filteredNews.map((event) => (
                  <NewsListItem
                    key={event.eventId}
                    event={event}
                    directionLabels={directionLabels}
                    locale={locale}
                    t={t}
                    onClick={() => {
                      setActiveEvent(event);
                      setPreviewOpen(true);
                    }}
                  />
                ))
              )}
            </div>
          </section>
        </section>

        <aside className="flex w-full flex-col gap-6 lg:w-1/4">
          <LiveStatusBar status={streamStatus} />
          <SentimentDial
            direction={latestEvent?.direction ?? "neutral"}
            confidence={latestEvent?.confidence ?? 0.5}
          />
          <UpcomingFeatures t={t} />
        </aside>
      </div>

      <NewsPreviewModal
        open={previewOpen}
        event={activeEvent}
        onClose={() => setPreviewOpen(false)}
        onViewChain={(evt) => {
          setActiveEvent(evt);
          setPreviewOpen(false);
          setDrawerOpen(true);
        }}
      />
      <ChainOfThoughtDrawer
        open={drawerOpen}
        steps={activeEvent?.chain_of_thought ?? []}
        citations={activeEvent?.citations ?? []}
        complianceStatus={activeEvent?.complianceStatus ?? "clean"}
        onClose={() => setDrawerOpen(false)}
      />
    </main>
  );
}
type StatusBadgeProps = {
  variant: "connecting" | "open" | "error";
  children: string;
};

function StatusBadge({ variant, children }: StatusBadgeProps) {
  const styles: Record<StatusBadgeProps["variant"], string> = {
    connecting: "border-accent-neutral text-accent-neutral",
    open: "border-accent-bull text-accent-bull",
    error: "border-accent-bear text-accent-bear"
  };

  return (
    <span className={clsx("terminal-text rounded-full border-2 px-4 py-1 text-[11px] uppercase tracking-[0.2em]", styles[variant])}>
      {children}
    </span>
  );
}

type SignalsListProps = {
  signals: IndexSignal[];
  isLoading: boolean;
  error?: string;
  t: (key: string) => string;
  onSelect?: (signal: IndexSignal) => void;
};

function SignalsList({ signals, isLoading, error, t, onSelect }: SignalsListProps) {
  if (isLoading) {
    return <div className="mt-4 rounded-lg border-2 border-dashed border-border-strong px-4 py-6 text-xs text-text-secondary">{t("signals.loading")}</div>;
  }

  if (error) {
    return (
      <div className="mt-4 rounded-lg border-2 border-accent-bear bg-white px-4 py-3 text-xs text-accent-bear">
        {t("signals.error")}: {error}
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="mt-4 rounded-lg border-2 border-dashed border-border-strong px-4 py-6 text-xs text-text-secondary">
        {t("empty.signals")}
      </div>
    );
  }

  return (
    <div className="mt-4 flex flex-col gap-2">
      {signals.slice(0, 5).map((signal) => (
        <button
          type="button"
          key={signal.signalId}
          onClick={() => {
            if (signal.newsId && onSelect) {
              onSelect(signal);
            }
          }}
          disabled={!signal.newsId || !onSelect}
          className={clsx(
            "flex items-center justify-between rounded-lg border-2 border-border-strong bg-white px-4 py-3 text-left text-xs shadow-[3px_3px_0px_0px_rgba(0,0,0,0.8)] transition",
            signal.newsId && onSelect
              ? "cursor-pointer hover:-translate-y-0.5 hover:shadow-[5px_5px_0px_rgba(0,0,0,0.9)]"
              : "cursor-default opacity-80"
          )}
        >
          <span className="terminal-text text-[12px] uppercase tracking-[0.18em] text-border-strong">
            {signal.signalType === "buy" ? "Buy" : "Sell"} - {signal.reasonTag ?? "Pending"}
          </span>
          <span className="text-text-secondary">
            {signal.price.toFixed(2)} - {new Date(signal.createdAt).toLocaleTimeString()}
          </span>
        </button>
      ))}
    </div>
  );
}

type EmptyStateProps = {
  message: string;
};

function EmptyState({ message }: EmptyStateProps) {
  return (
    <div className="rounded-xl border-2 border-dashed border-border-strong bg-white px-6 py-16 text-center text-sm text-text-secondary shadow-[4px_4px_0px_rgba(0,0,0,0.1)]">
      {message}
    </div>
  );
}

type NewsListItemProps = {
  event: NewsStreamEvent;
  directionLabels: Record<"all" | "bullish" | "bearish" | "neutral", string>;
  locale: string;
  t: (key: string) => string;
  onClick: () => void;
};

function NewsListItem({ event, directionLabels, locale, t, onClick }: NewsListItemProps) {
  const confidenceLabel = locale === "zh-CN"
    ? `置信度 ${(event.confidence * 100).toFixed(0)}%`
    : `Confidence ${(event.confidence * 100).toFixed(0)}%`;

  return (
    <article
      className="flex cursor-pointer flex-col gap-3 rounded-xl border-2 border-border-strong bg-white px-4 py-4 transition-transform hover:-translate-y-1 hover:shadow-[6px_6px_0px_rgba(0,0,0,0.8)]"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(eventKeyboard) => {
        if (eventKeyboard.key === "Enter" || eventKeyboard.key === " ") {
          eventKeyboard.preventDefault();
          onClick();
        }
      }}
    >
      <div className="flex flex-wrap items中心 justify-between gap-2">
        <h3 className="text-sm font-semibold text-border-strong">{event.headline}</h3>
        <span
          className={clsx(
            "terminal-text rounded-full border-2 px-3 py-0.5 text-[10px] uppercase tracking-[0.18em]",
            event.direction === "bullish" && "border-accent-bull text-accent-bull",
            event.direction === "bearish" && "border-accent-bear text-accent-bear",
            event.direction === "neutral" && "border-accent-neutral text-accent-neutral border-dashed"
          )}
        >
          {directionLabels[event.direction]}
        </span>
      </div>
      <p className="text-xs text-text-secondary">
        {event.summary ?? t("modal.summaryFallback")}
      </p>
      <div className="flex flex-wrap items-center gap-2 text-[10px] text-text-secondary">
        <span className="terminal-text text-[10px] uppercase tracking-[0.2em] text-border-strong">{confidenceLabel}</span>
        <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
        {event.signalTags.map((tag) => (
          <span key={tag} className="rounded-md border border-border-strong px-2 py-0.5 text-text-secondary">
            #{tag}
          </span>
        ))}
      </div>
    </article>
  );
}

type UpcomingFeaturesProps = {
  t: (key: string) => string;
};

function UpcomingFeatures({ t }: UpcomingFeaturesProps) {
  return (
    <div className="rounded-xl border border-border-strong bg-bg-surface p-4">
      <h3 className="text-sm font-medium text-text-secondary">{t("comingSoon.title")}</h3>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-text-secondary">
        <li>{t("comingSoon.signalLegend")}</li>
        <li>{t("comingSoon.hypothesis")}</li>
        <li>{t("comingSoon.indicators")}</li>
      </ul>
    </div>
  );
}

