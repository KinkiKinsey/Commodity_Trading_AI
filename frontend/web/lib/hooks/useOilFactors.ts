import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchOilFactors, OilFactorRecord } from "@/lib/api/oilFactors";

type UseOilFactorsOptions = {
  ticker?: string;
  language?: string;
  enabled?: boolean;
};

export function useOilFactors(options: UseOilFactorsOptions = {}) {
  const ticker = options.ticker ?? "CLZ25.NYM";
  const language = options.language ?? "Chinese";

  const query = useQuery({
    queryKey: ["oil-factors", ticker, language],
    queryFn: () =>
      fetchOilFactors({
        ticker,
        language
      }),
    enabled: options.enabled ?? true,
    staleTime: 5 * 60 * 1000
  });

  const topFactors = useMemo<OilFactorRecord[]>(() => {
    if (!query.data) return [];
    return query.data.factors.slice(0, 4);
  }, [query.data]);

  return {
    query,
    factors: query.data?.factors ?? [],
    topFactors,
    ticker: query.data?.ticker ?? ticker,
    language: query.data?.language ?? language
  };
}
