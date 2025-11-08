import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl } from "@/lib/utils/url";

export type CtpInterval = "1m" | "5m" | "15m" | "1h";

export type CtpPriceBar = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number | null;
};

export type CtpKlineResponse = {
  symbol: string;
  interval: CtpInterval;
  range: {
    start: string;
    end: string;
    count: number;
  };
  bars: CtpPriceBar[];
  metadata: {
    fetched_at: string;
    data_latency_seconds: number;
    source_latency_seconds?: number | null;
    notes?: string | null;
  };
};

const DEFAULT_ENDPOINT = process.env.NEXT_PUBLIC_CTP_KLINE_ENDPOINT ?? "/api/ctp/kline";

function buildEndpoint(symbol: string, interval: CtpInterval, count: number) {
  const url = resolveApiUrl(DEFAULT_ENDPOINT);
  url.searchParams.set("symbol", symbol);
  url.searchParams.set("interval", interval);
  url.searchParams.set("count", String(count));
  return url;
}

async function fetchCtpKline(symbol: string, interval: CtpInterval, count: number): Promise<CtpKlineResponse> {
  const url = buildEndpoint(symbol, interval, count);
  const response = await fetch(url.toString(), { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`CTP kline request failed (${response.status})`);
  }
  return (await response.json()) as CtpKlineResponse;
}

export function useCtpKline({
  symbol,
  interval = "1m",
  count = 240
}: {
  symbol?: string;
  interval?: CtpInterval;
  count?: number;
}) {
  return useQuery({
    queryKey: ["ctp-kline", symbol, interval, count],
    queryFn: () => fetchCtpKline(symbol!, interval as CtpInterval, count!),
    enabled: Boolean(symbol),
    staleTime: 5_000,
    retry: 1
  });
}
