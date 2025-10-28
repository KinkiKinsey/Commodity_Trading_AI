import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useIndexSignalsStore, IndexSignal } from "@/lib/state/indexSignalsStore";
import { INDEX_SIGNALS_ENDPOINT } from "@/lib/config/env";

const resolveEndpointUrl = (endpoint: string) => {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return new URL(endpoint);
  }

  const origin =
    typeof window !== "undefined" && window.location ? window.location.origin : "http://localhost:3000";

  return new URL(endpoint, origin);
};

type FetchSignalsResult = {
  symbol: string;
  signals: IndexSignal[];
};

async function fetchSignals(symbol: string): Promise<FetchSignalsResult> {
  const endpoint = INDEX_SIGNALS_ENDPOINT;
  const url = resolveEndpointUrl(endpoint);
  url.searchParams.set("symbol", symbol);

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`Failed to load signals: ${response.status}`);
  }

  const data = (await response.json()) as IndexSignal[];
  return { symbol, signals: data };
}

export function useIndexSignals(symbol: string) {
  const setSignals = useIndexSignalsStore((state) => state.setSignals);
  const setLoading = useIndexSignalsStore((state) => state.setLoading);
  const setError = useIndexSignalsStore((state) => state.setError);

  const query = useQuery({
    queryKey: ["index-signals", symbol],
    queryFn: () => fetchSignals(symbol),
    enabled: Boolean(symbol),
    staleTime: 30_000
  });

  useEffect(() => {
    if (query.isPending) {
      setLoading(true);
    }
  }, [query.isPending, setLoading]);

  useEffect(() => {
    if (query.isSuccess) {
      setSignals(query.data.symbol, query.data.signals);
    }
  }, [query.data, query.isSuccess, setSignals]);

  useEffect(() => {
    if (query.isError) {
      setError(query.error.message);
    }
  }, [query.error, query.isError, setError]);

  return query;
}
