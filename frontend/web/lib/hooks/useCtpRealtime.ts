import { useQuery } from "@tanstack/react-query";
import { resolveApiUrl } from "@/lib/utils/url";

export type CtpRealtimeTick = {
  symbol: string;
  local_timestamp: string;
  exchange_timestamp?: string | null;
  update_time: string;
  update_millisec: number;
  last_price: number;
  volume: number;
  bid?: { price?: number | null; volume?: number | null } | null;
  ask?: { price?: number | null; volume?: number | null } | null;
  metadata?: {
    fetched_at: string;
    data_latency_seconds?: number;
    source_latency_seconds?: number | null;
    notes?: string | null;
  };
};

const DEFAULT_ENDPOINT = process.env.NEXT_PUBLIC_CTP_REALTIME_ENDPOINT ?? "/api/ctp/realtime";

function buildUrl(symbol: string) {
  const url = resolveApiUrl(DEFAULT_ENDPOINT);
  url.searchParams.set("symbol", symbol);
  return url;
}

async function fetchRealtime(symbol: string): Promise<CtpRealtimeTick> {
  const response = await fetch(buildUrl(symbol).toString(), { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load realtime tick (${response.status})`);
  }
  return (await response.json()) as CtpRealtimeTick;
}

export function useCtpRealtime(symbol?: string, enabled = true) {
  return useQuery({
    queryKey: ["ctp-realtime", symbol],
    queryFn: () => fetchRealtime(symbol!),
    enabled: Boolean(symbol) && enabled,
    staleTime: 2000,
    refetchInterval: 2000,
    retry: 1
  });
}
