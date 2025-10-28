"use client";



import { useCallback, useEffect, useMemo, useState } from "react";

import clsx from "clsx";

import type { PricingKlineResponse } from "@/lib/api/pricing";

import { AppShell } from "@/components/layout/AppShell";

import { NewsPreviewModal } from "@/components/news/NewsPreviewModal";

import { ChainOfThoughtDrawer } from "@/components/news/ChainOfThoughtDrawer";

import { KLineChart } from "@/components/charts/KLineChart";


import { SentimentDial } from "@/components/news/SentimentDial";

import { SignalList } from "@/components/signals/SignalList";

import { FilterBar } from "@/components/news/FilterBar";

import { useNewsStream } from "@/lib/hooks/useNewsStream";

import { usePricingKline } from "@/lib/hooks/usePricingKline";

import { useIntl } from "@/lib/i18n/IntlContext";

import { useNewsStreamStore, type NewsStreamEvent } from "@/lib/state/newsStreamStore";

import type { IndexSignal } from "@/lib/state/indexSignalsStore";



const DEFAULT_SYMBOL = "CLZ25.NYM";



const SYMBOL_OPTIONS = [

  { label: "WTI Crude (Dec 2025)", value: "CLZ25.NYM" },

  { label: "WTI Crude (Continuous)", value: "CL=F" },

  { label: "Brent Crude", value: "BZ=F" },

  { label: "Gold", value: "GC=F" },

  { label: "DXY Index", value: "DX-Y.NYB" }

] as const;



const SYMBOL_TICKER_MAP: Record<string, string> = {

  "CLZ25.NYM": "CLZ25.NYM",

  "CL=F": "CLZ25.NYM",

  "BZ=F": "BZ=F",

  "GC=F": "GC=F",

  "DX-Y.NYB": "DX-Y.NYB"

};



type TimeRangeValue = "1h" | "6h" | "24h" | "all";

type DirectionValue = "all" | "bullish" | "bearish" | "neutral";



const TIME_RANGE_OPTIONS: { label: string; value: TimeRangeValue }[] = [

  { label: "1H", value: "1h" },

  { label: "6H", value: "6h" },

  { label: "24H", value: "24h" },

  { label: "All", value: "all" }

];



const TIME_LABELS_ZH: Record<TimeRangeValue, string> = {

  "1h": "1小时",

  "6h": "6小时",

  "24h": "24小时",

  all: "全部"

};



type PriceStats = {

  lastPrice: number;

  openPrice?: number;

  prevClose?: number;

  dayHigh?: number;

  dayLow?: number;

  rangeHigh?: number;

  rangeLow?: number;

  lastUpdated?: string;

};



const DIRECTION_LABELS_ZH: Record<"all" | "bullish" | "bearish" | "neutral", string> = {

  all: "\u5168\u90e8",

  bullish: "\u770b\u591a",

  bearish: "\u770b\u7a7a",

  neutral: "\u4e2d\u6027"

};



const DIRECTION_LABELS_EN: Record<"all" | "bullish" | "bearish" | "neutral", string> = {

  all: "All",

  bullish: "Bullish",

  bearish: "Bearish",

  neutral: "Neutral"

};



export default function NewsRealtimePage() {

  const [selectedSymbol, setSelectedSymbol] = useState<string>(DEFAULT_SYMBOL);

  const [directionFilter, setDirectionFilter] = useState<DirectionValue>("all");

  const [timeRange, setTimeRange] = useState<TimeRangeValue>("24h");

  const [searchTerm, setSearchTerm] = useState("");

  const [previewOpen, setPreviewOpen] = useState(false);

  const [drawerOpen, setDrawerOpen] = useState(false);

  const [activeEvent, setActiveEvent] = useState<NewsStreamEvent | undefined>(undefined);

  const [recentSymbols, setRecentSymbols] = useState<string[]>([DEFAULT_SYMBOL]);



  const { locale, setLocale, t } = useIntl();



  useNewsStream();



  const streamStatus = useNewsStreamStore((state) => state.streamStatus);

  const allNews = useNewsStreamStore((state) =>

    state.order.map((id) => state.events.get(id)).filter((evt): evt is NewsStreamEvent => Boolean(evt))

  );



  const resolvedTicker = SYMBOL_TICKER_MAP[selectedSymbol] ?? selectedSymbol;



  const {

    ohlcSeries,

    movingAverageLine,

    movingAverageUpper,

    movingAverageLower,
    volumeSeries,

    signals: fetchedSignals,

    query: pricingQuery

  } = usePricingKline(resolvedTicker);



  const signals = fetchedSignals;

  const pricingData = pricingQuery.data;



  const priceStats = useMemo<PriceStats | null>(() => {

    const series = pricingData?.series;

    if (!series || series.length === 0) {

      return null;

    }

    const lastBar = series[series.length - 1];

    const prevBar = series.length > 1 ? series[series.length - 2] : undefined;



    const { dayHigh, dayLow } = series.reduce(

      (acc, bar) => {

        return {

          dayHigh: Math.max(acc.dayHigh, bar.high ?? bar.close),

          dayLow: Math.min(acc.dayLow, bar.low ?? bar.close)

        };

      },

      { dayHigh: -Infinity, dayLow: Infinity }

    );



    return {

      lastPrice: lastBar.close,

      openPrice: lastBar.open,

      prevClose: prevBar?.close ?? lastBar.open,

      dayHigh: Number.isFinite(dayHigh) ? dayHigh : undefined,

      dayLow: Number.isFinite(dayLow) ? dayLow : undefined,

      rangeHigh: Number.isFinite(dayHigh) ? dayHigh : undefined,

      rangeLow: Number.isFinite(dayLow) ? dayLow : undefined,

      lastUpdated: pricingData?.metadata?.fetched_at ?? pricingData?.range?.end

    };

  }, [pricingData]);



  useEffect(() => {

    setDirectionFilter("all");

    setTimeRange("24h");

    setSearchTerm("");

  }, [selectedSymbol]);



  useEffect(() => {

    setRecentSymbols((prev) => {

      const next = [selectedSymbol, ...prev.filter((item) => item !== selectedSymbol)];

      return next.slice(0, 6);

    });

  }, [selectedSymbol]);



  const filteredNews = useMemo(() => {
    const now = Date.now();
    const windowMap: Record<"1h" | "6h" | "24h", number> = {
      "1h": 60 * 60 * 1000,
      "6h": 6 * 60 * 60 * 1000,
      "24h": 24 * 60 * 60 * 1000
    };

    const filteredList = allNews
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
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    return filteredList.slice(0, 40);
  }, [allNews, directionFilter, timeRange, searchTerm]);



  const localizedDirectionLabels = useMemo(() => (locale === "zh-CN" ? DIRECTION_LABELS_ZH : DIRECTION_LABELS_EN), [locale]);

  const timeOptions = useMemo(

    () =>

      TIME_RANGE_OPTIONS.map((option) => ({

        value: option.value,

        label: locale === "zh-CN" ? TIME_LABELS_ZH[option.value] : option.label

      })),

    [locale]

  );

  const latestSectionTitle = locale.startsWith("zh") ? "最新资讯" : "Latest Updates";
  const newsTimeFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: pricingData?.timezone ?? "UTC"
      }),
    [locale, pricingData?.timezone]
  );


  const latestEvent = filteredNews[0] ?? allNews[0];



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

  const connectionMessage =

    streamStatus.state === "error" ? streamStatus.message ?? t("banner.error") : t("banner.stale");



  const handleManualRefresh = useCallback(() => {

    window.location.reload();

  }, []);



  const localeToggleLabel = locale === "zh-CN" ? "EN" : "涓枃";

  const trendSummary = pricingData?.ml_moving_average.summary;

  const trendIntervals = pricingData?.ml_moving_average.time_intervals ?? [];

  const leftColumn = (

    <MarketColumn

      locale={locale}

      selectedSymbol={selectedSymbol}

      onSelectSymbol={setSelectedSymbol}

      recentSymbols={recentSymbols}

      symbolOptions={SYMBOL_OPTIONS}

      priceStats={priceStats}

      displayName={pricingData?.display_name}

      timezone={pricingData?.timezone}

      metadata={pricingData?.metadata}

      source={pricingData?.source}

      trendSummary={trendSummary}

      sentimentDirection={latestEvent?.direction}

      sentimentConfidence={latestEvent?.confidence ?? 0.5}

      trendIntervals={trendIntervals}

    />

  );



  const mainContent = (

    <div className="flex flex-col gap-4">

      {showReconnect ? (

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-accent-neutral/70 bg-white/80 px-4 py-3 text-sm text-text-primary">

          <span>{connectionMessage}</span>

          <button

            onClick={handleManualRefresh}

            className="terminal-text rounded-full border border-border-active bg-border-active px-4 py-1 text-[11px] uppercase tracking-[0.2em] text-bg-base transition hover:bg-border-active/90"

          >

            {t("button.refreshData")}

          </button>

        </div>

      ) : null}



      <section className="flex flex-col gap-4 border-b border-border-muted/40 pb-4">

        <div className="flex flex-wrap items-center justify-between gap-3">

          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">{t("header.title")}</h1>

          <div className="flex items-center gap-2">

            <StatusBadge variant={streamStatus.state}>{statusMessage}</StatusBadge>

            <button

              onClick={() => setLocale(locale === "zh-CN" ? "en-US" : "zh-CN")}

              className="terminal-text rounded-full border border-border-muted bg-bg-alt px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-text-primary transition hover:border-border-active"

            >

              {localeToggleLabel}

            </button>

          </div>

        </div>



        <PriceSummaryBar

          locale={locale}

          displayName={pricingData?.display_name}

          ticker={resolvedTicker}

          currency={pricingData?.source?.currency}

          marketStatus={pricingData?.source?.instrument_type}

          priceStats={priceStats}

          timezone={pricingData?.timezone}

          metadata={pricingData?.metadata}

        />



        <FilterBar

          symbolOptions={SYMBOL_OPTIONS}

          selectedSymbol={selectedSymbol}

          onSelectSymbol={setSelectedSymbol}

          directionFilter={directionFilter}

          onDirectionFilterChange={setDirectionFilter}

          directionLabels={localizedDirectionLabels}

          timeRange={timeRange}

          onTimeRangeChange={setTimeRange}

          timeOptions={timeOptions}

          searchTerm={searchTerm}

          onSearchTermChange={setSearchTerm}

          searchPlaceholder={t("filters.searchPlaceholder")}

          locale={locale}

        />

      </section>



      <section className="border-b border-border-muted/40 pb-4">

        <div className="flex items-center justify-between">

          <h2 className="text-lg font-semibold text-text-primary">{t("panel.signals")}</h2>

          <span className="terminal-text text-[11px] text-text-secondary">symbol / {selectedSymbol}</span>

        </div>

        <div className="mt-4 h-[20rem] w-full overflow-hidden rounded-2xl border border-border-muted bg-white shadow-[0_8px_20px_rgba(15,23,42,0.08)]">

          <KLineChart
            candles={ohlcSeries}
            movingAverageLine={movingAverageLine}
            movingAverageUpper={movingAverageUpper}
            movingAverageLower={movingAverageLower}
            volumes={volumeSeries}
            signals={signals}
            height={320}
            isLoading={pricingQuery.isLoading || pricingQuery.isFetching}
            onSelectSignal={(signal) => handleSignalSelect(signal, allNews, setActiveEvent, setPreviewOpen)}
          />
        </div>

        <SignalList

          signals={signals}

          isLoading={pricingQuery.isLoading || pricingQuery.isFetching}

          error={pricingQuery.isError && pricingQuery.error instanceof Error ? pricingQuery.error.message : undefined}

          locale={locale === "zh-CN" ? "zh-CN" : "en-US"}

          t={t}

          onSelect={(signal) => handleSignalSelect(signal, allNews, setActiveEvent, setPreviewOpen)}

          className="mt-3"

        />

      </section>





    </div>

  );



  const rightRail = (
    <div className="flex flex-col gap-6">
      <section className="rounded-2xl border border-border-muted bg-white px-4 py-4 shadow-[0_6px_18px_rgba(15,23,42,0.06)]">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-text-primary">{latestSectionTitle}</h3>
          <span className="text-[11px] uppercase tracking-[0.18em] text-text-secondary">
            {newsTimeFormatter.resolvedOptions().timeZone ?? "UTC"}
          </span>
        </div>
        {filteredNews.length === 0 ? (
          <div className="mt-4">
            <EmptyState message={t("empty.news")} />
          </div>
        ) : (
          <ul className="mt-4 space-y-3">
            {filteredNews.slice(0, 12).map((event) => {
              const directionTone =
                event.direction === "bullish"
                  ? "bg-accent-bull/15 text-accent-bull"
                  : event.direction === "bearish"
                    ? "bg-accent-bear/15 text-accent-bear"
                    : "bg-slate-200 text-slate-600";
              const displayTime = newsTimeFormatter.format(new Date(event.timestamp));
              return (
                <li key={event.eventId}>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveEvent(event);
                      setPreviewOpen(true);
                    }}
                    className="w-full text-left transition hover:bg-bg-alt/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-active"
                  >
                    <div className="flex items-center justify-between gap-2 px-3 py-2">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 text-[11px] text-text-secondary">
                          <span className={clsx("rounded-full px-2 py-0.5 font-medium", directionTone)}>
                            {localizedDirectionLabels[event.direction]}
                          </span>
                          <span className="text-text-secondary/80">{displayTime}</span>
                        </div>
                        <p className="line-clamp-2 text-sm font-semibold leading-snug text-text-primary">{event.headline}</p>
                      </div>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );



  return (

    <>

      <AppShell

        leftColumn={<MarketColumnPlaceholder />}

        mainColumn={mainContent}

        rightColumn={rightRail}

      />

      <NewsPreviewModal

        isOpen={previewOpen}

        news={activeEvent}

        onClose={() => setPreviewOpen(false)}

        onViewChain={(evt) => {

          setActiveEvent(evt);

          setPreviewOpen(false);

          setDrawerOpen(true);

        }}

      />

      <ChainOfThoughtDrawer

        isOpen={drawerOpen}

        steps={activeEvent?.chain_of_thought ?? []}

        citations={activeEvent?.citations ?? []}

        complianceStatus={activeEvent?.complianceStatus ?? "clean"}

        title={activeEvent?.headline}

        publishedAt={activeEvent?.timestamp}

        onClose={() => setDrawerOpen(false)}

      />

    </>

  );

}



function handleSignalSelect(

  signal: IndexSignal,

  allNews: NewsStreamEvent[],

  setActiveEvent: (event: NewsStreamEvent | undefined) => void,

  setPreviewOpen: (open: boolean) => void

) {

  const targetEvent =

    allNews.find((event) => event.eventId === signal.newsId) ||

    allNews.find((event) => event.signal?.signalId === signal.signalId);

  if (targetEvent) {

    setActiveEvent(targetEvent);

    setPreviewOpen(true);

  }

}



type StatusBadgeProps = {

  variant: "connecting" | "open" | "error";

  children: string;

};



function StatusBadge({ variant, children }: StatusBadgeProps) {

  const styles: Record<StatusBadgeProps["variant"], string> = {

    connecting: "border-state-warning text-state-warning",

    open: "border-accent-bull text-accent-bull",

    error: "border-accent-bear text-accent-bear"

  };



  return (

    <span className={clsx("terminal-text rounded-full border px-4 py-1 text-[11px] uppercase tracking-[0.2em]", styles[variant])}>

      {children}

    </span>

  );

}



type EmptyStateProps = {

  message: string;

};



function EmptyState({ message }: EmptyStateProps) {

  return (

    <div className="rounded-xl border border-border-muted bg-bg-alt/40 px-6 py-16 text-center text-sm text-text-secondary">

      {message}

    </div>

  );

}



type MarketColumnProps = {

  locale: string;

  selectedSymbol: string;

  onSelectSymbol: (symbol: string) => void;

  recentSymbols: string[];

  symbolOptions: readonly { label: string; value: string }[];

  priceStats: PriceStats | null;

  displayName?: string;

  timezone?: string;

  metadata?: PricingKlineResponse["metadata"];

  source?: PricingKlineResponse["source"];

  trendSummary?: string;

  trendIntervals: PricingKlineResponse["ml_moving_average"]["time_intervals"];

  sentimentDirection?: "bullish" | "bearish" | "neutral";

  sentimentConfidence?: number;

};



function MarketColumn({

  locale,

  selectedSymbol,

  onSelectSymbol,

  recentSymbols,

  symbolOptions,

  priceStats,

  displayName,

  timezone,

  metadata,

  source,

  trendSummary,

  sentimentDirection,

  sentimentConfidence,

  trendIntervals

}: MarketColumnProps) {

  const isZh = locale.startsWith("zh");

  const localeKey: "zh-CN" | "en-US" = isZh ? "zh-CN" : "en-US";

  const optionLabelMap = useMemo(() => {

    const map: Record<string, string> = {};

    symbolOptions.forEach((option) => {

      map[option.value] = option.label;

    });

    return map;

  }, [symbolOptions]);



  const priceFormatter = useMemo(

    () =>

      new Intl.NumberFormat(locale, {

        minimumFractionDigits: 2,

        maximumFractionDigits: 2

      }),

    [locale]

  );



  const percentFormatter = useMemo(

    () =>

      new Intl.NumberFormat(locale, {

        minimumFractionDigits: 2,

        maximumFractionDigits: 2

      }),

    [locale]

  );



  const timeFormatter = useMemo(

    () =>

      new Intl.DateTimeFormat(locale, {

        hour: "2-digit",

        minute: "2-digit",

        second: "2-digit",

        hour12: false,

        timeZone: timezone ?? "UTC"

      }),

    [locale, timezone]

  );



  const rangeFormatter = useMemo(

    () =>

      new Intl.DateTimeFormat(locale, {

        month: "short",

        day: "2-digit",

        timeZone: timezone ?? "UTC"

      }),

    [locale, timezone]

  );



  const resolvedLabel = displayName ?? optionLabelMap[selectedSymbol] ?? selectedSymbol;

  const changeValue =

    priceStats && typeof priceStats.prevClose === "number"

      ? priceStats.lastPrice - priceStats.prevClose

      : undefined;

  const changePercent =

    changeValue !== undefined && priceStats?.prevClose

      ? priceStats.prevClose !== 0

        ? (changeValue / priceStats.prevClose) * 100

        : undefined

      : undefined;

  const changeTone =

    changeValue === undefined

      ? "text-text-secondary"

      : changeValue > 0

        ? "text-accent-bull"

        : changeValue < 0

          ? "text-accent-bear"

          : "text-text-secondary";





const labels = {

    watchlist: isZh ? "市场观察" : "Market Watch",

    lastUpdate: isZh ? "最后更新时间" : "Last Updated",

    symbol: isZh ? "标的" : "Symbol",

    lastPrice: isZh ? "最新价" : "Last Price",

    change: isZh ? "涨跌幅" : "Change",

    latency: isZh ? "延迟" : "Latency",

    currency: isZh ? "计价货币" : "Currency",

    exchange: isZh ? "交易所" : "Exchange",

    keyStats: isZh ? "关键指标" : "Key Stats",

    open: isZh ? "开盘价" : "Open",

    prevClose: isZh ? "前收盘" : "Prev Close",

    dayRange: isZh ? "日内区间" : "Day Range",

    dayHigh: isZh ? "高点" : "High",

    dayLow: isZh ? "低点" : "Low",

    trendTitle: isZh ? "趋势解读" : "Trend Narrative",

    trendIntervalsTitle: isZh ? "观测区间" : "Observed Intervals",

    dataSource: isZh ? "数据来源" : "Data Source",

    instrumentType: isZh ? "资产类型" : "Instrument Type",

    timezone: isZh ? "时区" : "Timezone",

    latencySource: isZh ? "源头延迟" : "Source Latency",

    notes: isZh ? "备注" : "Notes",

    recent: isZh ? "最近选择" : "Recent Symbols"

  };

  const recentList = recentSymbols.filter((symbol) => symbol !== selectedSymbol);



  return (

    <div className="flex flex-col gap-6">

      <section className="rounded-2xl border border-border-muted bg-white p-6 shadow-[0_4px_12px_rgba(15,23,42,0.08)]">

        <div className="flex flex-col gap-4">

          <div className="flex items-start justify-between gap-3">

            <div>

                            <h2 className="mt-2 text-lg font-semibold text-text-primary">{resolvedLabel}</h2>

              <p className="mt-1 text-xs text-text-secondary">

                {labels.symbol} 路 {selectedSymbol}

              </p>

            </div>

            {metadata?.fetched_at ? (

              <div className="text-right text-xs text-text-secondary">

                <p className="terminal-text text-[10px] uppercase tracking-[0.2em]">{labels.lastUpdate}</p>

                <p className="mt-1 tabular-nums">{timeFormatter.format(new Date(metadata.fetched_at))}</p>

              </div>

            ) : null}

          </div>



          <div className="flex flex-wrap gap-2">

            {symbolOptions.map((option) => (

              <button

                key={option.value}

                type="button"

                onClick={() => onSelectSymbol(option.value)}

                className={clsx(

                  "rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] transition",

                  option.value === selectedSymbol

                    ? "border-black bg-black text-white shadow-[0_4px_12px_rgba(0,0,0,0.25)]"

                    : "border-border-muted text-text-secondary hover:border-border-active hover:text-text-primary"

                )}

              >

                {option.label}

              </button>

            ))}

          </div>



          {recentList.length ? (

            <div>

                            <div className="mt-2 flex flex-wrap gap-2">

                {recentList.map((symbol) => (

                  <button

                    key={symbol}

                    type="button"

                    onClick={() => onSelectSymbol(symbol)}

                    className="rounded-full border border-border-muted px-3 py-1 text-xs text-text-secondary transition hover:border-border-active hover:text-text-primary"

                  >

                    {optionLabelMap[symbol] ?? symbol}

                  </button>

                ))}

              </div>

            </div>

          ) : null}

        </div>

      </section>



      <section className="rounded-2xl border border-border-muted bg-white p-6 shadow-[0_4px_12px_rgba(15,23,42,0.08)]">

        <div className="flex flex-col gap-4">

          <div className="flex flex-wrap items-end justify-between gap-4">

            <div>

              <p className="terminal-text text-[11px] uppercase tracking-[0.25em] text-text-secondary">

                {labels.lastPrice}

              </p>

              <p className="mt-2 text-3xl font-semibold tabular-nums text-text-primary">

                {priceStats ? priceFormatter.format(priceStats.lastPrice) : "--"}

              </p>

            </div>

            <div className={clsx("text-right text-sm tabular-nums", changeTone)}>

              {changeValue !== undefined ? (

                <>

                  <p>

                    {changeValue > 0 ? "+" : ""}

                    {priceFormatter.format(changeValue)}

                  </p>

                  {changePercent !== undefined ? (

                    <p>

                      {changePercent > 0 ? "+" : ""}

                      {percentFormatter.format(changePercent)}%

                    </p>

                  ) : null}

                </>

              ) : (

                <p className="text-text-secondary">--</p>

              )}

            </div>

          </div>



          <div className="flex flex-wrap items-center gap-3 text-xs text-text-secondary">

            {metadata?.data_latency_seconds !== undefined ? (

              <span className="rounded-full border border-border-muted px-3 py-1 tabular-nums">

                {labels.latency} {metadata.data_latency_seconds}s

              </span>

            ) : null}

            {source?.exchange ? <span>{labels.exchange} 路 {source.exchange}</span> : null}

            {source?.currency ? <span>{labels.currency} 路 {source.currency}</span> : null}

          </div>

          {sentimentDirection ? (

            <div className="mt-4">

              <SentimentDial

                direction={sentimentDirection}

                confidence={Math.max(0, Math.min(1, sentimentConfidence ?? 0.5))}

                locale={localeKey}

              />

            </div>

          ) : null}

        </div>

      </section>



      <section className="rounded-2xl border border-border-muted bg-white p-6 shadow-[0_4px_12px_rgba(15,23,42,0.08)]">

        <h3 className="text-sm font-semibold text-text-primary">{labels.keyStats}</h3>

        <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-text-secondary">

          <StatCell label={labels.open} value={priceStats?.openPrice} formatter={priceFormatter} />

          <StatCell label={labels.prevClose} value={priceStats?.prevClose} formatter={priceFormatter} />

          <StatCell

            label={`${labels.dayRange} 路 ${labels.dayLow}`}

            value={priceStats?.dayLow}

            formatter={priceFormatter}

          />

          <StatCell

            label={`${labels.dayRange} 路 ${labels.dayHigh}`}

            value={priceStats?.dayHigh}

            formatter={priceFormatter}

          />

        </div>

      </section>



      {trendSummary || (trendIntervals?.length ?? 0) > 0 ? (

        <section className="rounded-2xl border border-border-muted bg-white p-6 shadow-[0_4px_12px_rgba(15,23,42,0.08)]">

          <h3 className="text-sm font-semibold text-text-primary">{labels.trendTitle}</h3>

          {trendSummary ? (

            <p className="mt-3 text-xs leading-relaxed text-text-secondary">{trendSummary}</p>

          ) : null}

          {trendIntervals && trendIntervals.length > 0 ? (

            <div className="mt-4 space-y-2">

                            {trendIntervals.slice(0, 6).map((interval) => (

                <div

                  key={`${interval.start_date}-${interval.end_date}`}

                  className="flex items-center justify-between rounded-lg border border-border-muted px-3 py-2 text-xs text-text-secondary"

                >

                  <span className="tabular-nums">

                    {rangeFormatter.format(new Date(interval.start_date))} -{" "}

                    {rangeFormatter.format(new Date(interval.end_date))}

                  </span>

                  <span

                    className={clsx(

                      "terminal-text text-[10px] uppercase tracking-[0.2em]",

                      interval.trend === "BULLISH" ? "text-accent-bull" : "text-accent-bear"

                    )}

                  >

                    {interval.trend === "BULLISH" ? (isZh ? "看多" : "Bullish") : isZh ? "看空" : "Bearish"}

                  </span>

                </div>

              ))}

            </div>

          ) : null}

        </section>

      ) : null}



      {source || metadata ? (

        <section className="rounded-2xl border border-border-muted bg-white p-6 shadow-[0_4px_12px_rgba(15,23,42,0.08)]">

          <h3 className="text-sm font-semibold text-text-primary">{labels.dataSource}</h3>

          <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-text-secondary">

            <StatLine label={labels.symbol} value={selectedSymbol} />

            {source?.instrument_type ? <StatLine label={labels.instrumentType} value={source.instrument_type} /> : null}

            {source?.exchange ? <StatLine label={labels.exchange} value={source.exchange} /> : null}

            {source?.currency ? <StatLine label={labels.currency} value={source.currency} /> : null}

            {metadata?.data_latency_seconds !== undefined ? (

              <StatLine label={labels.latency} value={`${metadata.data_latency_seconds}s`} />

            ) : null}

            {metadata?.source_latency_seconds !== undefined ? (

              <StatLine label={labels.latencySource} value={`${metadata.source_latency_seconds}s`} />

            ) : null}

            {timezone ? <StatLine label={labels.timezone} value={timezone} /> : null}

          </dl>

          {metadata?.notes ? (

            <p className="mt-3 rounded-lg border border-border-muted bg-bg-alt/50 px-3 py-2 text-xs text-text-secondary">

              {labels.notes} 路 {metadata.notes}

            </p>

          ) : null}

        </section>

      ) : null}

    </div>

  );

}





type PriceSummaryBarProps = {
  locale: string;
  displayName?: string;
  ticker: string;
  currency?: string;
  marketStatus?: string;
  priceStats: PriceStats | null;
  timezone?: string;
  metadata?: PricingKlineResponse["metadata"];
};

function PriceSummaryBar({
  locale,
  displayName,
  ticker,
  currency,
  marketStatus,
  priceStats,
  timezone,
  metadata,
}: PriceSummaryBarProps) {
  const isZh = locale.startsWith("zh");
  const priceFormatter = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const changeFormatter = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const percentFormatter = changeFormatter;
  const timeFormatter = new Intl.DateTimeFormat(locale, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: timezone ?? "UTC",
  });

  const changeValue =
    priceStats && typeof priceStats.prevClose === "number"
      ? priceStats.lastPrice - priceStats.prevClose
      : undefined;
  const changePercent =
    changeValue !== undefined && priceStats?.prevClose
      ? priceStats.prevClose !== 0
        ? (changeValue / priceStats.prevClose) * 100
        : undefined
      : undefined;

  const priceText = priceStats ? priceFormatter.format(priceStats.lastPrice) : "--";
  const changeClass =
    changeValue === undefined
      ? "bg-slate-100 text-text-secondary"
      : changeValue >= 0
        ? "bg-accent-bull/15 text-accent-bull"
        : "bg-accent-bear/15 text-accent-bear";
  const arrow = changeValue === undefined ? "" : changeValue >= 0 ? "+" : "-";

  const infoLineParts: string[] = [ticker];
  if (currency) infoLineParts.push("(" + currency + ")");
  if (marketStatus) infoLineParts.push(marketStatus);
  const infoLine = infoLineParts.join(" · ");

  const fetchedAt = metadata?.fetched_at ? new Date(metadata.fetched_at) : undefined;
  const formattedTime = fetchedAt ? timeFormatter.format(fetchedAt) : null;
  const updateLabel = formattedTime
    ? (isZh ? "更新时间 " + formattedTime : "As of " + formattedTime)
    : null;

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-border-muted bg-white px-5 py-4 shadow-[0_6px_18px_rgba(15,23,42,0.07)]">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <p className="text-sm font-semibold text-text-primary">{displayName ?? ticker}</p>
          <p className="text-xs text-text-secondary">{infoLine}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-2xl font-semibold tabular-nums text-text-primary">{priceText}</span>
          {changeValue !== undefined ? (
            <span className={clsx("flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium tabular-nums", changeClass)}>
              {arrow} {changeFormatter.format(Math.abs(changeValue))}
              {changePercent !== undefined ? (
                <span className="ml-1">({percentFormatter.format(Math.abs(changePercent))}%)</span>
              ) : null}
            </span>
          ) : null}
        </div>
      </div>
      {updateLabel ? <p className="text-xs text-text-secondary">{updateLabel}</p> : null}
    </div>
  );
}


type StatCellProps = {

  label: string;

  value?: number;

  formatter: Intl.NumberFormat;

};



function StatCell({ label, value, formatter }: StatCellProps) {

  return (

    <div className="flex flex-col gap-1 rounded-lg border border-border-muted/60 bg-bg-alt/30 p-3">

      <span className="terminal-text text-[10px] uppercase tracking-[0.2em] text-text-secondary">{label}</span>

      <span className="text-sm font-medium tabular-nums text-text-primary">

        {typeof value === "number" ? formatter.format(value) : "--"}

      </span>

    </div>

  );

}



type StatLineProps = {

  label: string;

  value?: string;

};



function StatLine({ label, value }: StatLineProps) {

  if (!value) return null;

  return (

    <div className="flex flex-col">

      <span className="terminal-text text-[10px] uppercase tracking-[0.2em] text-text-secondary">{label}</span>

      <span className="mt-1 text-xs text-text-primary">{value}</span>

    </div>

  );

}



function MarketColumnPlaceholder() {

  return (

    <div className="rounded-2xl border border-border-muted bg-bg-panel/80 p-6 text-sm text-text-secondary shadow-[0_12px_32px_rgba(0,0,0,0.35)]">

      <h3 className="text-sm font-semibold text-text-primary">市场观察</h3>

      <p className="mt-3 leading-relaxed">

        市场模块即将展示自选列表、要闻摘要与精选资产的实时信号。使用筛选器即可获取最新动向与 AI 洞察。

      </p>

    </div>

  );

}




type UpcomingFeaturesProps = {

  t: (key: string) => string;

};



function UpcomingFeatures({ t }: UpcomingFeaturesProps) {

  return (

    <div className="rounded-2xl border border-border-muted bg-bg-panel/80 p-6 shadow-[0_12px_32px_rgba(0,0,0,0.35)]">

      <h3 className="text-sm font-semibold text-text-primary">{t("comingSoon.title")}</h3>

      <ul className="mt-3 list-disc space-y-2 pl-5 text-xs text-text-secondary">

        <li>{t("comingSoon.signalLegend")}</li>

        <li>{t("comingSoon.hypothesis")}</li>

        <li>{t("comingSoon.indicators")}</li>

      </ul>

    </div>

  );

}

















