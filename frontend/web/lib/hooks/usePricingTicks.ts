"use client";

import { useMemo } from "react";
import { useQueries, type UseQueryResult } from "@tanstack/react-query";

import type { PricingTickResponse } from "@/lib/api/pricing";
import { PRICING_TICK_ENDPOINT } from "@/lib/config/env";

const resolveEndpointUrl = (endpoint: string) => {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return new URL(endpoint);
  }

  const origin =
    typeof window !== "undefined" && window.location ? window.location.origin : "http://localhost:3000";

  return new URL(endpoint, origin);
};

async function fetchPricingTick(instrumentId: string): Promise<PricingTickResponse> {
  const url = resolveEndpointUrl(PRICING_TICK_ENDPOINT);
  url.searchParams.set("instrument_id", instrumentId);

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Failed to load tick for ${instrumentId} (${response.status})`);
  }
  return (await response.json()) as PricingTickResponse;
}

export type TickRecord = {
  instrumentId: string;
  query: UseQueryResult<PricingTickResponse, Error>;
};

export function usePricingTicks(instrumentIds: string[], refetchInterval = 5000) {
  const queries = useQueries({
    queries: instrumentIds.map((instrumentId) => ({
      queryKey: ["pricing-tick", instrumentId],
      queryFn: () => fetchPricingTick(instrumentId),
      enabled: Boolean(instrumentId),
      refetchInterval,
      staleTime: refetchInterval,
    })),
  });

  const tickRecords = useMemo<TickRecord[]>(
    () =>
      instrumentIds.map((instrumentId, index) => ({
        instrumentId,
        query: queries[index],
      })),
    [instrumentIds, queries]
  );

  const tickMap = useMemo<Record<string, PricingTickResponse | undefined>>(() => {
    const entries: Record<string, PricingTickResponse | undefined> = {};
    tickRecords.forEach(({ instrumentId, query }) => {
      entries[instrumentId] = query.data;
    });
    return entries;
  }, [tickRecords]);

  const isLoading = tickRecords.some(({ query }) => query.isLoading);
  const isFetching = tickRecords.some(({ query }) => query.isFetching);
  const error = tickRecords.find(({ query }) => query.error)?.query.error;

  return {
    tickRecords,
    tickMap,
    isLoading,
    isFetching,
    error,
    refetchAll: () => Promise.all(tickRecords.map(({ query }) => query.refetch())),
  };
}
