import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { PricingKlineResponse, PricingSignal, PricingBar } from "@/lib/api/pricing";
import type { PlaceholderPoint } from "@/lib/mock/generatePlaceholderSeries";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";
import { useNewsStreamStore, NewsStreamEvent } from "@/lib/state/newsStreamStore";

const DEFAULT_ENDPOINT =
  process.env.NEXT_PUBLIC_PRICING_KLINE_ENDPOINT ?? "http://localhost:8000/api/pricing/kline";

async function fetchPricingKline(ticker: string, days: number): Promise<PricingKlineResponse> {
  const url = new URL(DEFAULT_ENDPOINT);
  url.searchParams.set("ticker", ticker);
  url.searchParams.set("days", String(days));
  url.searchParams.set("include_indicators", "true");

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`Failed to load pricing data (${response.status})`);
  }

  const payload = (await response.json()) as PricingKlineResponse;
  return payload;
}

function createSeries(bars: PricingBar[]): PlaceholderPoint[] {
  return bars.map((bar) => ({
    timestamp: bar.timestamp,
    close: bar.close,
    volume: bar.volume ?? undefined
  }));
}

function resolveNewsId(signal: PricingSignal, events: NewsStreamEvent[]): string | undefined {
  if (signal.linked_news_ids && signal.linked_news_ids.length > 0) {
    return signal.linked_news_ids[0];
  }

  const match = events.find((event) => event.signal?.signalId === signal.signal_id);
  return match?.eventId;
}

function toIndexSignals(
  signals: PricingSignal[],
  events: NewsStreamEvent[]
): IndexSignal[] {
  return signals.map((signal) => {
    const newsId = resolveNewsId(signal, events);
    return {
      signalId: signal.signal_id,
      signalType: signal.signal_type,
      price: signal.price,
      createdAt: signal.timestamp,
      reasonTag: signal.trend === "BULLISH" ? "Bullish" : "Bearish",
      newsId
    };
  });
}

export function usePricingKline(ticker: string | undefined, days = 180) {
  const newsEvents = useNewsStreamStore((state) => Array.from(state.events.values()));

  const query = useQuery({
    queryKey: ["pricing-kline", ticker, days],
    queryFn: () => fetchPricingKline(ticker!, days),
    enabled: Boolean(ticker),
    staleTime: 60_000
  });

  const series = useMemo<PlaceholderPoint[]>(() => {
    if (!query.data) return [];
    return createSeries(query.data.series);
  }, [query.data]);

  const signals = useMemo<IndexSignal[]>(() => {
    if (!query.data) return [];
    return toIndexSignals(query.data.signals, newsEvents);
  }, [query.data, newsEvents]);

  return {
    query,
    series,
    signals,
    metadata: query.data?.metadata,
    range: query.data?.range,
    movingAverage: query.data?.ml_moving_average
  };
}
