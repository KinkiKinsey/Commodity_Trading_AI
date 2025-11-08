import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { PricingKlineResponse, PricingSignal, PricingBar } from "@/lib/api/pricing";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";
import { useNewsStreamStore, NewsStreamEvent } from "@/lib/state/newsStreamStore";
import { PRICING_KLINE_ENDPOINT } from "@/lib/config/env";
import { resolveApiUrl } from "@/lib/utils/url";

export type CandlestickPoint = {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
};

export type LinePoint = {
  time: number;
  value: number;
};

export type VolumePoint = {
  time: number;
  value: number;
  color: string;
};

type TimestampValue = {
  timestamp: string;
  value: number;
};

async function fetchPricingKline(ticker: string, days: number): Promise<PricingKlineResponse> {
  const url = resolveApiUrl(PRICING_KLINE_ENDPOINT);
  url.searchParams.set("ticker", ticker);
  url.searchParams.set("days", String(days));
  url.searchParams.set("include_indicators", "true");

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`Failed to load pricing data (${response.status})`);
  }

  return (await response.json()) as PricingKlineResponse;
}

function toUnix(timestamp: string): number {
  return Math.floor(new Date(timestamp).getTime() / 1000);
}

function createOhlcSeries(bars: PricingBar[]): CandlestickPoint[] {
  return bars.map((bar) => ({
    time: toUnix(bar.timestamp),
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
  }));
}

function createLineSeries(points: TimestampValue[] | undefined): LinePoint[] {
  if (!points) return [];
  return points
    .filter((point) => point.timestamp && typeof point.value === "number")
    .map((point) => ({
      time: toUnix(point.timestamp),
      value: point.value,
    }));
}

function resolveNewsId(signal: PricingSignal, events: NewsStreamEvent[]): string | undefined {
  if (signal.linked_news_ids && signal.linked_news_ids.length > 0) {
    return signal.linked_news_ids[0];
  }

  const match = events.find((event) => event.signal?.signalId === signal.signal_id);
  return match?.eventId;
}

function toIndexSignals(signals: PricingSignal[], events: NewsStreamEvent[]): IndexSignal[] {
  return signals.map((signal) => {
    const newsId = resolveNewsId(signal, events);
    return {
      signalId: signal.signal_id,
      signalType: signal.signal_type,
      price: signal.price,
      createdAt: signal.timestamp,
      reasonTag: signal.trend === "BULLISH" ? "Bullish" : "Bearish",
      newsId,
    };
  });
}

export function usePricingKline(ticker: string | undefined, days = 180) {
  const newsEvents = useNewsStreamStore((state) => Array.from(state.events.values()));

  const query = useQuery({
    queryKey: ["pricing-kline", ticker, days],
    queryFn: () => fetchPricingKline(ticker!, days),
    enabled: Boolean(ticker),
    staleTime: 60_000,
  });

  const ohlcSeries = useMemo<CandlestickPoint[]>(() => {
    if (!query.data) return [];
    return createOhlcSeries(query.data.series);
  }, [query.data]);

  const movingAverageLine = useMemo<LinePoint[]>(() => {
    if (!query.data) return [];
    return createLineSeries(query.data.ml_moving_average.line);
  }, [query.data]);

  const movingAverageUpper = useMemo<LinePoint[]>(() => {
    if (!query.data) return [];
    return createLineSeries(query.data.ml_moving_average.upper_band);
  }, [query.data]);

  const movingAverageLower = useMemo<LinePoint[]>(() => {
    if (!query.data) return [];
    return createLineSeries(query.data.ml_moving_average.lower_band);
  }, [query.data]);

  const volumeSeries = useMemo<VolumePoint[]>(() => {
    if (!query.data) return [];
    return query.data.series.map((bar) => ({
      time: toUnix(bar.timestamp),
      value: typeof bar.volume === "number" ? bar.volume : 0,
      color: bar.close >= bar.open ? "#0EAD69" : "#F25F5C",
    }));
  }, [query.data]);

  const signals = useMemo<IndexSignal[]>(() => {
    if (!query.data) return [];
    return toIndexSignals(query.data.signals, newsEvents);
  }, [query.data, newsEvents]);

  return {
    query,
    ohlcSeries,
    movingAverageLine,
    movingAverageUpper,
    movingAverageLower,
    volumeSeries,
    signals,
    metadata: query.data?.metadata,
    range: query.data?.range,
    movingAverage: query.data?.ml_moving_average,
  };
}
