import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useIndexSignalsStore, IndexSignal } from "@/lib/state/indexSignalsStore";

type FetchSignalsResult = {
  symbol: string;
  signals: IndexSignal[];
};

async function fetchSignals(symbol: string): Promise<FetchSignalsResult> {
  const endpoint = process.env.NEXT_PUBLIC_INDEX_SIGNALS_ENDPOINT;

  if (!endpoint) {
    return { symbol, signals: [] };
  }

  const response = await fetch(`${endpoint}?symbol=${symbol}`);

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
    enabled: Boolean(symbol) && Boolean(process.env.NEXT_PUBLIC_INDEX_SIGNALS_ENDPOINT),
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
