"use client";







import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";



import clsx from "clsx";
import { Dialog, Transition } from "@headlessui/react";





import type { PricingKlineResponse } from "@/lib/api/pricing";

import { AppShell } from "@/components/layout/AppShell";
import { CtpContractsPanel } from "@/components/ctp/CtpContractsPanel";



import { NewsPreviewModal } from "@/components/news/NewsPreviewModal";



import { ChainOfThoughtDrawer } from "@/components/news/ChainOfThoughtDrawer";



import { TradingViewWidget } from "@/components/charts/TradingViewWidget";
import { OilFactorsOverlayChart } from "@/components/charts/OilFactorsOverlayChart";
import { OilFactorsHeatmap } from "@/components/oil/OilFactorsHeatmap";









import { FilterBar } from "@/components/news/FilterBar";

import { SearchInput } from "@/components/common/SearchInput";



import { useNewsStream } from "@/lib/hooks/useNewsStream";



import { usePricingKline } from "@/lib/hooks/usePricingKline";

import { useOilFactors } from "@/lib/hooks/useOilFactors";
import { buildOverlayData } from "@/lib/utils/oilFactors";
import type { OverlayDataPoint } from "@/lib/utils/oilFactors";
import type { OilFactorRecord } from "@/lib/api/oilFactors";

import { requestTranslations } from "@/lib/api/translation";

import { analyzeNews } from "@/lib/api/news";



import { useIntl } from "@/lib/i18n/IntlContext";



import { useNewsStreamStore, type NewsStreamEvent } from "@/lib/state/newsStreamStore";



import type { IndexSignal } from "@/lib/state/indexSignalsStore";
import { usePricingTicks } from "@/lib/hooks/usePricingTicks";
import { DEFAULT_TV_STUDIES, DEFAULT_TV_STUDY_OVERRIDES } from "@/lib/config/tradingViewStudies";







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

const TRADINGVIEW_SYMBOL_MAP: Record<string, string> = {
  "CLZ25.NYM": "NYMEX:CLZ2025",
  "CL=F": "NYMEX:CL1!",
  "BZ=F": "ICEEUR:BRN1!",
  "GC=F": "COMEX:GC1!",
  "DX-Y.NYB": "TVC:DXY"
};

const TRADINGVIEW_WATCHLIST = ["NYMEX:CL1!", "ICEEUR:BRN1!", "COMEX:GC1!", "TVC:DXY"];

const TRADINGVIEW_COMPARE = [{ symbol: "COMEX:GC1!", position: "SameScale" as const }];

const TRADINGVIEW_STUDIES = DEFAULT_TV_STUDIES;

const WATCHED_TICK_INSTRUMENTS = ["CL2512-NYM", "CL2601-NYM", "CL2602-NYM", "CL2603-NYM", "CL2604-NYM", "CL2605-NYM"];

const TICK_LABELS: Record<string, string> = {
  "CL2512-NYM": "WTI Dec 2025",
  "CL2601-NYM": "WTI Jan 2026",
  "CL2602-NYM": "WTI Feb 2026",
  "CL2603-NYM": "WTI Mar 2026",
  "CL2604-NYM": "WTI Apr 2026",
  "CL2605-NYM": "WTI May 2026"
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


type RealtimeTickEntry = {
  instrumentId: string;
  label: string;
  lastPrice?: number;
  bidPrice?: number;
  bidVolume?: number;
  askPrice?: number;
  askVolume?: number;
  volume?: number;
  updatedAt?: string;
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
  const [isOilFactorsModalOpen, setOilFactorsModalOpen] = useState(false);



  const [drawerOpen, setDrawerOpen] = useState(false);



  const [activeEvent, setActiveEvent] = useState<NewsStreamEvent | undefined>(undefined);
  const [regeneratingEventId, setRegeneratingEventId] = useState<string | null>(null);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);


  const [eventTranslations, setEventTranslations] = useState<Record<string, EventTranslation>>({});



  const pendingTranslationIds = useRef<Set<string>>(new Set());







  const { locale, setLocale, t } = useIntl();

  const translationEnabled = locale.startsWith("zh");
  const tradingViewSymbol = TRADINGVIEW_SYMBOL_MAP[selectedSymbol] ?? "NYMEX:CL1!";

  const { tickMap, isLoading: ticksLoading, isFetching: ticksFetching } = usePricingTicks(
    WATCHED_TICK_INSTRUMENTS,
    5000
  );

  const watchedTicks = useMemo<RealtimeTickEntry[]>(
    () =>
      WATCHED_TICK_INSTRUMENTS.map((instrumentId) => {
        const tick = tickMap[instrumentId];
        return {
          instrumentId,
          label: TICK_LABELS[instrumentId] ?? instrumentId,
          lastPrice: tick?.last_price,
          bidPrice: tick?.bid?.price,
          bidVolume: tick?.bid?.volume,
          askPrice: tick?.ask?.price,
          askVolume: tick?.ask?.volume,
          volume: tick?.volume,
          updatedAt: tick?.updated_at,
        };
      }),
    [tickMap]
  );

  






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
    factors: oilFactors
  } = useOilFactors({

    ticker: resolvedTicker,

    language: oilLanguage

  });

  const overlayData = useMemo(() => buildOverlayData(oilFactors), [oilFactors]);
  const oilMicroPoints = overlayData.micro;
  const oilMacroPoints = overlayData.macro;

  const oilThumbnailSubtitle = t("Micro/Macro");







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
    <div className="flex flex-col gap-6">
      <CtpContractsPanel locale={locale} />
    </div>
  );







  const mainContent = (



    <div className="flex flex-col gap-6">



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







      <section className="flex flex-col gap-4 pb-2">



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

          source={pricingData?.source}

          sentimentDirection={displayLatestEvent?.direction}

          sentimentConfidence={displayLatestEvent?.confidence}

          trendSummary={trendSummary}



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






      

      <section className="pb-3">



        <div className="mt-2 h-[32rem] w-full overflow-hidden rounded-2xl border border-border-muted bg-white shadow-[0_8px_20px_rgba(15,23,42,0.08)]">
          <TradingViewWidget
            symbol={tradingViewSymbol}
            locale={locale}
            watchlist={TRADINGVIEW_WATCHLIST}
            compareSymbols={TRADINGVIEW_COMPARE}
            studies={TRADINGVIEW_STUDIES}
            studiesOverrides={DEFAULT_TV_STUDY_OVERRIDES}
            autosize
          />
        </div>



        <OilFactorsThumbnail
          micro={oilMicroPoints}
          macro={oilMacroPoints}
          isLoading={oilFactorsQuery.isLoading || oilFactorsQuery.isFetching}
          hasError={oilFactorsQuery.isError ?? false}
          onOpen={() => setOilFactorsModalOpen(true)}
          t={t}
          subtitle={oilThumbnailSubtitle}
        />

      </section>











    </div>



  );







  const rightRail = (

    <div className="flex h-full flex-col gap-6 xl:sticky xl:top-8">

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



        leftColumn={leftColumn}



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

      <OilFactorsModal
        isOpen={isOilFactorsModalOpen}
        onClose={() => setOilFactorsModalOpen(false)}
        factors={oilFactors}
        isLoading={oilFactorsQuery.isLoading || oilFactorsQuery.isFetching}
        hasError={oilFactorsQuery.isError ?? false}
        subtitle={oilThumbnailSubtitle}
        t={t}
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








type PriceSummaryBarProps = {

  locale: string;

  displayName?: string;

  ticker: string;

  currency?: string;

  marketStatus?: string;

  priceStats: PriceStats | null;

  timezone?: string;

  metadata?: PricingKlineResponse["metadata"];

  source?: PricingKlineResponse["source"];

  sentimentDirection?: "bullish" | "bearish" | "neutral";

  sentimentConfidence?: number;

  trendSummary?: string;

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
  source,
  sentimentDirection,
  sentimentConfidence,
  trendSummary,
}: PriceSummaryBarProps) {
  const isZh = locale.startsWith("zh");
  const priceFormatter = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
  const changeFormatter = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
  const percentFormatter = changeFormatter;
  const timeFormatter = new Intl.DateTimeFormat(locale, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: timezone ?? "UTC"
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
  const infoLine = infoLineParts.join(" �� ");

  const fetchedAt = metadata?.fetched_at ? new Date(metadata.fetched_at) : undefined;
  const formattedTime = fetchedAt ? timeFormatter.format(fetchedAt) : null;
  const updateLabel = formattedTime
    ? (isZh ? "����ʱ�� " + formattedTime : "As of " + formattedTime)
    : null;

  const labels = {
    latency: isZh ? "延迟" : "Latency",
    exchange: isZh ? "交易所" : "Exchange",
    currency: isZh ? "计价货币" : "Currency",
    sentiment: isZh ? "情绪指示" : "Sentiment",
    aiInsight: isZh ? "AI 结论" : "AI Insight",
    confidence: isZh ? "置信度" : "Confidence"
  };

  const metaBadges: string[] = [];
  if (metadata?.data_latency_seconds !== undefined) {
    metaBadges.push(`${labels.latency} - ${metadata.data_latency_seconds}s`);
  }
  if (source?.exchange) {
    metaBadges.push(`${labels.exchange} - ${source.exchange}`);
  }
  if (source?.currency) {
    metaBadges.push(`${labels.currency} - ${source.currency}`);
  }

  const sentimentMap = isZh
    ? { bullish: "看多", bearish: "看空", neutral: "中性" }
    : { bullish: "Bullish", bearish: "Bearish", neutral: "Neutral" };
  const sentimentText = sentimentDirection ? sentimentMap[sentimentDirection] : null;
  const confidencePercent = Math.round(
    Math.max(0, Math.min(1, sentimentConfidence ?? 0.5)) * 100
  );
  const sentimentTone =
    sentimentDirection === "bullish"
      ? "text-accent-bull"
      : sentimentDirection === "bearish"
        ? "text-accent-bear"
        : "text-text-primary";

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-border-muted bg-white px-5 py-4 shadow-[0_6px_18px_rgba(15,23,42,0.07)]">
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

      {metaBadges.length ? (
        <div className="flex flex-wrap gap-2 text-xs text-text-secondary">
          {metaBadges.map((badge) => (
            <span key={badge} className="rounded-full border border-border-muted px-3 py-1">
              {badge}
            </span>
          ))}
        </div>
      ) : null}

      {sentimentText ? (
        <div className="rounded-2xl border border-border-muted/80 bg-bg-alt/40 px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="terminal-text text-[11px] uppercase tracking-[0.25em] text-text-secondary">
              {labels.sentiment}
            </p>
            <span className="text-[11px] text-text-secondary">
              {labels.confidence} - {confidencePercent}%
            </span>
          </div>
          <p className="mt-1 text-sm font-semibold text-text-primary">{labels.aiInsight}</p>
          <p className={clsx("text-lg font-semibold", sentimentTone)}>{sentimentText}</p>
          {trendSummary ? (
            <p className="mt-2 text-xs leading-relaxed text-text-secondary">{trendSummary}</p>
          ) : null}
        </div>
      ) : null}

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







type OilFactorsModalProps = {
  isOpen: boolean;
  onClose: () => void;
  factors: OilFactorRecord[];
  isLoading: boolean;
  hasError: boolean;
  subtitle: string;
  t: (key: string, fallback?: string) => string;
};

type OilFactorsThumbnailProps = {
  micro?: OverlayDataPoint[];
  macro?: OverlayDataPoint[];
  isLoading: boolean;
  hasError: boolean;
  onOpen: () => void;
  t: (key: string, fallback?: string) => string;
  subtitle: string;
};

function OilFactorsModal({
  isOpen,
  onClose,
  factors,
  isLoading,
  hasError,
  subtitle,
  t
}: OilFactorsModalProps) {
  let modalContent: JSX.Element;

  if (isLoading) {
    modalContent = (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        {t("oilFactors.thumbnail.loading", "Loading oil factors...")}
      </div>
    );
  } else if (hasError) {
    modalContent = (
      <div className="flex h-72 items-center justify-center text-sm text-red-500">
        {t("oilFactors.thumbnail.error", "Failed to load oil factors.")}
      </div>
    );
  } else if (!factors.length) {
    modalContent = (
      <div className="flex h-72 items-center justify-center text-sm text-slate-500">
        {t("oilFactors.thumbnail.empty", "No micro factor data yet.")}
      </div>
    );
  } else {
    modalContent = <OilFactorsHeatmap factors={factors} />;
  }

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-[80]">
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" aria-hidden />
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
          <Dialog.Panel className="fixed inset-0 flex items-center justify-center overflow-y-auto px-4 py-10 sm:px-6 lg:px-10">
            <div className="w-full max-w-5xl rounded-3xl border border-slate-200 bg-white shadow-[0_24px_55px_rgba(15,23,42,0.18)]">
              <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-5">
                <div>
                  <Dialog.Title className="text-lg font-semibold text-slate-900">
                    {t("oilFactors.title", "Oil Factors")}
                  </Dialog.Title>
                  <p className="text-sm text-slate-600">{subtitle}</p>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/40"
                  aria-label={t("modal.close", "Close")}
                >
                  <span aria-hidden="true">&times;</span>
                </button>
              </header>

              <div className="space-y-6 px-6 py-6">{modalContent}</div>
            </div>
          </Dialog.Panel>
        </Transition.Child>
      </Dialog>
    </Transition>
  );
}

function OilFactorsThumbnail({
  micro = [],
  macro = [],
  isLoading,
  hasError,
  onOpen,
  t,
  subtitle
}: OilFactorsThumbnailProps) {
  let chartContent: JSX.Element;

  if (isLoading) {
    chartContent = (
      <div className="flex h-56 items-center justify-center text-xs text-slate-500">
        {t("oilFactors.thumbnail.loading", "Loading oil factors...")}
      </div>
    );
  } else if (hasError) {
    chartContent = (
      <div className="flex h-56 items-center justify-center text-xs text-red-500">
        {t("oilFactors.thumbnail.error", "Failed to load oil factors.")}
      </div>
    );
  } else if (!micro.length && !macro.length) {
    chartContent = (
      <div className="flex h-56 items-center justify-center text-xs text-slate-500">
        {t("oilFactors.thumbnail.empty", "No micro factor data yet.")}
      </div>
    );
  } else {
    chartContent = (
      <div className="h-[20rem]">
        <OilFactorsOverlayChart
          micro={micro}
          macro={macro}
          height={320}
          showAnnotations={false}
          className="h-full"
        />
      </div>
    );
  }

  return (
    <button
      type="button"
      onDoubleClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          onOpen();
        }
      }}
      className="mt-4 w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary/40"
    >
      <div className="flex items-center justify-between gap-4 px-1">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            {t("oilFactors.thumbnail.title", "Oil Factors")}
          </h3>
          <p className="text-xs text-slate-600">{subtitle}</p>
        </div>
        <span className="text-[10px] uppercase tracking-[0.18em] text-accent-primary">
          {t("oilFactors.thumbnail.cta", "View details")}
        </span>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_14px_35px_rgba(15,23,42,0.12)]">
        {chartContent}
      </div>
    </button>
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




































