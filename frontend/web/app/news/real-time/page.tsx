"use client";







import { useCallback, useEffect, useMemo, useRef, useState } from "react";



import clsx from "clsx";

import Link from "next/link";



import type { PricingKlineResponse } from "@/lib/api/pricing";

import type { OilFactorRecord } from "@/lib/api/oilFactors";



import { AppShell } from "@/components/layout/AppShell";



import { NewsPreviewModal } from "@/components/news/NewsPreviewModal";



import { ChainOfThoughtDrawer } from "@/components/news/ChainOfThoughtDrawer";



import { KLineChart } from "@/components/charts/KLineChart";





import { SentimentDial } from "@/components/news/SentimentDial";



import { SignalList } from "@/components/signals/SignalList";



import { FilterBar } from "@/components/news/FilterBar";

import { SearchInput } from "@/components/common/SearchInput";



import { useNewsStream } from "@/lib/hooks/useNewsStream";



import { usePricingKline } from "@/lib/hooks/usePricingKline";

import { useOilFactors } from "@/lib/hooks/useOilFactors";



import { requestTranslations } from "@/lib/api/translation";

import { analyzeNews } from "@/lib/api/news";



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





type StepTranslation = {

  text?: string;

  evidence?: string;

};



type EventTranslation = {

  headline?: string;

  summary?: string;

  steps?: Record<number, StepTranslation>;

};



const CJK_REGEX = /[\u3400-\u9FFF]/;





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



  const [timeRange, setTimeRange] = useState<TimeRangeValue>("all");



  const [searchTerm, setSearchTerm] = useState("");

  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [analysisError, setAnalysisError] = useState<string | null>(null);



  useEffect(() => {

    setAnalysisError(null);

  }, [searchTerm]);



  const [previewOpen, setPreviewOpen] = useState(false);



  const [drawerOpen, setDrawerOpen] = useState(false);



  const [activeEvent, setActiveEvent] = useState<NewsStreamEvent | undefined>(undefined);
  const [regeneratingEventId, setRegeneratingEventId] = useState<string | null>(null);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);


  const [recentSymbols, setRecentSymbols] = useState<string[]>([DEFAULT_SYMBOL]);



  const [eventTranslations, setEventTranslations] = useState<Record<string, EventTranslation>>({});



  const pendingTranslationIds = useRef<Set<string>>(new Set());







  const { locale, setLocale, t } = useIntl();



  const translationEnabled = locale.startsWith("zh");







  useNewsStream();







  const streamStatus = useNewsStreamStore((state) => state.streamStatus);
  const setEvent = useNewsStreamStore((state) => state.setEvent);


  const allNews = useNewsStreamStore((state) =>



    state.order.map((id) => state.events.get(id)).filter((evt): evt is NewsStreamEvent => Boolean(evt))



  );



  const newsById = useMemo(() => {

    const map = new Map<string, NewsStreamEvent>();

    for (const event of allNews) {

      map.set(event.eventId, event);

    }

    return map;

  }, [allNews]);



  const localizeEvent = useCallback(

    (event: NewsStreamEvent): NewsStreamEvent => {

      if (!translationEnabled || event.language?.startsWith("zh")) {

        return event;

      }

      const translation = eventTranslations[event.eventId];

      if (!translation) {

        return event;

      }



      let changed = false;

      let headline = event.headline;

      let summary = event.summary;



      if (translation.headline) {

        headline = translation.headline;

        changed = true;

      }

      if (translation.summary !== undefined) {

        summary = translation.summary;

        changed = true;

      }



      let stepsChanged = false;

      const localizedSteps = event.chain_of_thought.map((step, index) => {

        const stepTranslation = translation.steps?.[index];

        if (!stepTranslation) {

          return step;

        }

        let updatedStep = step;

        if (stepTranslation.text) {

          updatedStep = { ...updatedStep, text: stepTranslation.text };

          stepsChanged = true;

        }

        if (stepTranslation.evidence) {

          if (updatedStep === step) {

            updatedStep = { ...updatedStep };

          }

          updatedStep.evidence = stepTranslation.evidence;

          stepsChanged = true;

        }

        return updatedStep;

      });



      if (stepsChanged) {

        changed = true;

      }



      if (!changed) {

        return event;

      }



      return {

        ...event,

        headline,

        summary,

        chain_of_thought: stepsChanged ? localizedSteps : event.chain_of_thought,

        language: "zh-CN"

      };

    },

    [translationEnabled, eventTranslations]

  );



  const selectEventById = useCallback(

    (eventId: string, fallback?: NewsStreamEvent) => {

      const original = newsById.get(eventId) ?? fallback;

      if (original) {

        setActiveEvent(original);

      }

    },

    [newsById]

  );



  const localizedActiveEvent = useMemo(
    () => (activeEvent ? localizeEvent(activeEvent) : undefined),
    [activeEvent, localizeEvent]
  );

  useEffect(() => {
    setRegenerateError(null);
    setRegeneratingEventId(null);
  }, [localizedActiveEvent?.eventId]);

  const handleSearchSubmit = useCallback(
    async (term: string) => {
      const query = term.trim();
      if (!query) {
        return;
      }

      if (query.length < 20) {

        setAnalysisError(

          locale.startsWith("zh")

            ? "请输入不少于 20 个字符的新闻内容。"

            : "Please enter at least 20 characters of news content."

        );

        return;

      }

      if (query.length > 8000) {

        setAnalysisError(

          locale.startsWith("zh")

            ? "输入内容不能超过 8000 个字符。"

            : "Please keep the input under 8000 characters."

        );

        return;

      }

      setAnalysisError(null);

      setIsAnalyzing(true);

      try {

        const event = await analyzeNews({ text: query });

        selectEventById(event.eventId, event);

        setDrawerOpen(false);

        setPreviewOpen(true);

      } catch (error) {

        console.error("Failed to analyze custom news", error);

        setAnalysisError(

          locale.startsWith("zh")

            ? "无法完成分析，请稍后重试。"

            : "Unable to analyze the news. Please try again."

        );

      } finally {

        setIsAnalyzing(false);

      }

    },

    [locale, selectEventById, setDrawerOpen, setPreviewOpen]
  );

  const handleRegenerateChain = useCallback(
    async (event: NewsStreamEvent) => {
      const contentParts = [event.headline, event.summary ?? ""].filter((part) => part && part.trim().length > 0);
      const composed = contentParts.join("\n\n").trim();
      const payloadText =
        composed.length >= 20 ? composed : `${event.headline}\n\n${event.summary ?? ""}\n${event.timestamp}`.trim();

      setRegenerateError(null);
      setRegeneratingEventId(event.eventId);

      try {
        const regenerated = await analyzeNews({
          text: payloadText,
          headline: event.headline,
          summary: event.summary ?? undefined,
        });

        const updated: NewsStreamEvent = {
          ...event,
          direction: regenerated.direction,
          confidence: regenerated.confidence,
          chain_of_thought: regenerated.chain_of_thought ?? [],
          citations: regenerated.citations ?? [],
          signalTags:
            regenerated.signalTags && regenerated.signalTags.length > 0
              ? regenerated.signalTags
              : [regenerated.direction],
          complianceStatus: regenerated.complianceStatus ?? event.complianceStatus,
        };

        setEvent(updated, { updateStatus: false });
        setActiveEvent(updated);
      } catch (error) {
        console.error("Failed to regenerate reasoning chain", error);
        setRegenerateError(
          locale.startsWith("zh")
            ? "生成推理链失败，请稍后再试。"
            : "Failed to regenerate reasoning chain. Please try again."
        );
      } finally {
        setRegeneratingEventId(null);
      }
    },
    [locale, setEvent, setActiveEvent]
  );

  const drawerEvent = localizedActiveEvent ?? activeEvent;







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



  const oilLanguage = locale.startsWith("zh") ? "Chinese" : "English";

  const {

    query: oilFactorsQuery,

    topFactors: oilTopFactors

  } = useOilFactors({

    ticker: resolvedTicker,

    language: oilLanguage

  });







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



    setTimeRange("all");



    setSearchTerm("");



  }, [selectedSymbol]);







  useEffect(() => {



    setRecentSymbols((prev) => {



      const next = [selectedSymbol, ...prev.filter((item) => item !== selectedSymbol)];



      return next.slice(0, 6);



    });



  }, [selectedSymbol]);



  useEffect(() => {



    if (!translationEnabled) {

      return;

    }



    const pendingSet = pendingTranslationIds.current;

    const translationItems: { id: string; text: string }[] = [];

    const queuedIds: string[] = [];



    const queueItem = (id: string, rawText?: string, existing?: string) => {

      if (!rawText || existing) {

        return;

      }

      const trimmed = rawText.trim();

      if (!trimmed || CJK_REGEX.test(trimmed) || pendingSet.has(id)) {

        return;

      }

      translationItems.push({ id, text: trimmed });

      queuedIds.push(id);

      pendingSet.add(id);

    };



    for (const event of allNews) {

      if (event.language?.startsWith("zh")) {

        continue;

      }

      const translation = eventTranslations[event.eventId];

      queueItem(`${event.eventId}::headline`, event.headline, translation?.headline);

      queueItem(`${event.eventId}::summary`, event.summary ?? undefined, translation?.summary);

      event.chain_of_thought.forEach((step, index) => {

        const stepTranslation = translation?.steps?.[index];

        queueItem(`${event.eventId}::chain::${index}::text`, step.text, stepTranslation?.text);

        if (step.evidence) {

          queueItem(`${event.eventId}::chain::${index}::evidence`, step.evidence, stepTranslation?.evidence);

        }

      });

    }



    if (!translationItems.length) {

      queuedIds.forEach((id) => pendingSet.delete(id));

      return;

    }



    let cancelled = false;



    (async () => {

      try {

        const response = await requestTranslations(translationItems, "zh-CN");

        if (cancelled) {

          return;

        }

        const updates = translationItems.map((item) => ({

          id: item.id,

          text: response[item.id] ?? item.text

        }));

        setEventTranslations((prev) => {

          const next = { ...prev };

          for (const update of updates) {

            const [eventId, section, indexMaybe, attrMaybe] = update.id.split("::");

            if (!eventId || !section) {

              continue;

            }

            const current: EventTranslation = { ...(next[eventId] ?? {}) };

            if (section === "headline") {

              current.headline = update.text;

            } else if (section === "summary") {

              current.summary = update.text;

            } else if (section === "chain") {

              const index = Number(indexMaybe);

              if (!Number.isNaN(index)) {

                const steps = { ...(current.steps ?? {}) };

                const step = { ...(steps[index] ?? {}) };

                if (attrMaybe === "evidence") {

                  step.evidence = update.text;

                } else {

                  step.text = update.text;

                }

                steps[index] = step;

                current.steps = steps;

              }

            }

            next[eventId] = current;

          }

          return next;

        });

      } catch (error) {

        console.error("Failed to translate news content", error);

        if (!cancelled) {

          setEventTranslations((prev) => {

            const next = { ...prev };

            for (const item of translationItems) {

              const [eventId, section, indexMaybe, attrMaybe] = item.id.split("::");

              if (!eventId || !section) {

                continue;

              }

              const current: EventTranslation = { ...(next[eventId] ?? {}) };

              if (section === "headline") {

                current.headline = current.headline ?? item.text;

              } else if (section === "summary") {

                current.summary = current.summary ?? item.text;

              } else if (section === "chain") {

                const index = Number(indexMaybe);

                if (!Number.isNaN(index)) {

                  const steps = { ...(current.steps ?? {}) };

                  const step = { ...(steps[index] ?? {}) };

                  if (attrMaybe === "evidence") {

                    step.evidence = step.evidence ?? item.text;

                  } else {

                    step.text = step.text ?? item.text;

                  }

                  steps[index] = step;

                  current.steps = steps;

                }

              }

              next[eventId] = current;

            }

            return next;

          });

        }

      } finally {

        queuedIds.forEach((id) => pendingSet.delete(id));

      }

    })();



    return () => {

      cancelled = true;

      queuedIds.forEach((id) => pendingSet.delete(id));

    };

  }, [translationEnabled, allNews, eventTranslations]);



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

      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());



    return filteredList.slice(0, 40);

  }, [allNews, directionFilter, timeRange]);

  const displayNews = useMemo(() => {

    if (!translationEnabled) {

      return filteredNews;

    }

    return filteredNews.map((event) => localizeEvent(event));

  }, [translationEnabled, filteredNews, localizeEvent]);







  const localizedDirectionLabels = useMemo(() => (locale === "zh-CN" ? DIRECTION_LABELS_ZH : DIRECTION_LABELS_EN), [locale]);



  const timeOptions = useMemo(



    () =>



      TIME_RANGE_OPTIONS.map((option) => ({



        value: option.value,



        label: locale === "zh-CN" ? TIME_LABELS_ZH[option.value] : option.label



      })),



    [locale]



  );



    const latestSectionTitle = t("news.latestTitle");

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



  const displayLatestEvent = useMemo(

    () => (latestEvent ? localizeEvent(latestEvent) : latestEvent),

    [latestEvent, localizeEvent]

  );







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







    const localeToggleLabel = locale === "zh-CN" ? t("news.localeToggle.en") : t("news.localeToggle.zh");



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



      sentimentDirection={displayLatestEvent?.direction}



      sentimentConfidence={displayLatestEvent?.confidence ?? 0.5}



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



        <OilFactorsThumbnail

          factors={oilTopFactors}

          isLoading={oilFactorsQuery.isLoading || oilFactorsQuery.isFetching}

          hasError={oilFactorsQuery.isError ?? false}

          href="/oil-factors"

          t={t}

        />



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

        <div className="flex flex-col gap-3">

          <div className="flex flex-wrap items-center justify-between gap-3">

            <h3 className="text-base font-semibold text-text-primary">{latestSectionTitle}</h3>

            <span className="text-[11px] uppercase tracking-[0.18em] text-text-secondary">

              {newsTimeFormatter.resolvedOptions().timeZone ?? "UTC"}

            </span>

          </div>

          <div className="flex w-full flex-col gap-2">

            <SearchInput

              value={searchTerm}

              onChange={setSearchTerm}

              onSubmit={handleSearchSubmit}

              isLoading={isAnalyzing}

              placeholder={t("filters.searchPlaceholder")}

              className="w-full"

            />

            {analysisError ? (

              <p className="text-xs text-market-negative">{analysisError}</p>

            ) : isAnalyzing ? (

              <p className="text-xs text-text-secondary">

                {locale.startsWith("zh") ? "正在生成推理链，请稍候…" : "Generating reasoning chain..."}

              </p>

            ) : null}

          </div>

        </div>

        {displayNews.length === 0 ? (

          <div className="mt-4">

            <EmptyState message={t("empty.news")} />

          </div>

        ) : (

          <ul className="mt-4 space-y-3">

            {displayNews.slice(0, 12).map((event) => {

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

                      selectEventById(event.eventId, event);

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



        news={localizedActiveEvent}



        onClose={() => setPreviewOpen(false)}
        onRegenerateChain={handleRegenerateChain}
        isRegenerating={regeneratingEventId === localizedActiveEvent?.eventId}
        regenerateError={regeneratingEventId === localizedActiveEvent?.eventId ? regenerateError : null}



        onViewChain={(evt) => {



          selectEventById(evt.eventId, evt);



          setPreviewOpen(false);



          setDrawerOpen(true);



        }}



      />



      <ChainOfThoughtDrawer



        isOpen={drawerOpen}



        steps={drawerEvent?.chain_of_thought ?? []}



        citations={drawerEvent?.citations ?? []}



        complianceStatus={drawerEvent?.complianceStatus ?? "clean"}



        title={drawerEvent?.headline}



        publishedAt={drawerEvent?.timestamp}



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

    watchlist: isZh ? "\u5e02\u573a\u89c2\u5bdf" : "Market Watch",

    lastUpdate: isZh ? "\u6700\u540e\u66f4\u65b0\u65f6\u95f4" : "Last Updated",

    symbol: isZh ? "\u6807\u7684" : "Symbol",

    lastPrice: isZh ? "\u6700\u65b0\u4ef7" : "Last Price",

    change: isZh ? "\u6da8\u8dcc\u5e45" : "Change",

    latency: isZh ? "\u5ef6\u8fdf" : "Latency",

    currency: isZh ? "\u8ba1\u4ef7\u8d27\u5e01" : "Currency",

    exchange: isZh ? "\u4ea4\u6613\u6240" : "Exchange",

    keyStats: isZh ? "\u5173\u952e\u6307\u6807" : "Key Stats",

    open: isZh ? "\u5f00\u76d8\u4ef7" : "Open",

    prevClose: isZh ? "\u524d\u6536\u76d8" : "Prev Close",

    dayRange: isZh ? "\u65e5\u5185\u533a\u95f4" : "Day Range",

    dayHigh: isZh ? "\u6700\u9ad8" : "High",

    dayLow: isZh ? "\u6700\u4f4e" : "Low",

    trendTitle: isZh ? "\u8d8b\u52bf\u89e3\u8bfb" : "Trend Narrative",

    trendIntervalsTitle: isZh ? "\u89c2\u6d4b\u533a\u95f4" : "Observed Intervals",

    dataSource: isZh ? "\u6570\u636e\u6765\u6e90" : "Data Source",

    instrumentType: isZh ? "\u8d44\u4ea7\u7c7b\u578b" : "Instrument Type",

    timezone: isZh ? "\u65f6\u533a" : "Timezone",

    latencySource: isZh ? "\u6e90\u5934\u5ef6\u8fdf" : "Source Latency",

    notes: isZh ? "\u5907\u6ce8" : "Notes",

    recent: isZh ? "\u6700\u8fd1\u9009\u62e9" : "Recent Symbols"

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



                {labels.symbol} · {selectedSymbol}



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



            {source?.exchange ? <span>{labels.exchange} · {source.exchange}</span> : null}



            {source?.currency ? <span>{labels.currency} · {source.currency}</span> : null}



          </div>



          {sentimentDirection ? (



            <div className="mt-4">



              <SentimentDial



                direction={sentimentDirection}



                confidence={Math.max(0, Math.min(1, sentimentConfidence ?? 0.5))}







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



            label={`${labels.dayRange} · ${labels.dayLow}`}



            value={priceStats?.dayLow}



            formatter={priceFormatter}



          />



          <StatCell



            label={`${labels.dayRange} · ${labels.dayHigh}`}



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



              {labels.notes} · {metadata.notes}



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







type OilFactorsThumbnailProps = {



  factors: OilFactorRecord[];



  isLoading: boolean;



  hasError: boolean;



  href: string;



  t: (key: string, fallback?: string) => string;



};







function OilFactorsThumbnail({ factors, isLoading, hasError, href, t }: OilFactorsThumbnailProps) {



  return (



    <Link



      href={href}



      className="mt-4 block rounded-2xl border border-border-muted bg-bg-panel/80 p-4 shadow-[0_8px_20px_rgba(15,23,42,0.08)] transition hover:border-accent-primary/60 hover:shadow-[0_12px_28px_rgba(15,23,42,0.12)]"



    >



      <div className="flex items-center justify-between">



        <div>



          <h3 className="text-sm font-semibold text-text-primary">



            {t("oilFactors.thumbnail.title", "AI Oil Factors")}



          </h3>



          <p className="text-xs text-text-secondary">



            {t("oilFactors.thumbnail.subtitle", "Top ranked macro & micro drivers for this contract")}



          </p>



        </div>



        <span className="text-[10px] uppercase tracking-[0.18em] text-accent-primary">



          {t("oilFactors.thumbnail.cta", "View All")}



        </span>



      </div>







      <div className="mt-3 space-y-2">



        {isLoading ? (



          <p className="text-xs text-text-secondary">{t("oilFactors.thumbnail.loading", "Loading factors…")}</p>



        ) : hasError ? (



          <p className="text-xs text-error">{t("oilFactors.thumbnail.error", "Unable to load factors right now.")}</p>



        ) : factors.length === 0 ? (



          <p className="text-xs text-text-secondary">



            {t("oilFactors.thumbnail.empty", "No recent drivers detected – check back soon.")}



          </p>



        ) : (



          factors.map((factor) => (



            <div key={`${factor.factor}-${factor.start_date}-${factor.end_date}`} className="flex items-start gap-3">



              <div className="mt-1 h-2 w-2 flex-none rounded-full bg-accent-primary" />



              <div>



                <p className="text-xs font-medium text-text-primary">{factor.factor}</p>



                <p className="text-[11px] text-text-secondary">



                  {factor.driver_type || t("oilFactors.thumbnail.unknownDriver", "Driver unknown")}



                </p>



              </div>



            </div>



          ))



        )}



      </div>







    </Link>



  );



}







function MarketColumnPlaceholder() {

  const { locale } = useIntl();

  const isZh = locale.startsWith("zh");

  const title = isZh ? "市场观察" : "Market Watch";

  const description = isZh

    ? "市场模块即将展示自选列表、要闻摘要与精选资产的实时信号。使用筛选器即可获取最新动向与 AI 洞察。"

    : "The market column will soon showcase watchlists, key headlines, and real-time signals for selected assets. Use the filters to surface the latest moves and AI insights.";

  return (

    <div className="rounded-2xl border border-border-muted bg-bg-panel/80 p-6 text-sm text-text-secondary shadow-[0_12px_32px_rgba(0,0,0,0.35)]">

      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>

      <p className="mt-3 leading-relaxed">{description}</p>

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





































