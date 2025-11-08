
import { useCallback, useEffect, useRef, useState } from "react";

import { CTP_CONTRACT_BUFFER, DEFAULT_CTP_CONTRACT_COUNT, generateCtpContractIds } from "@/lib/utils/ctpContracts";

const DEFAULT_REFRESH_MS = 5000;
const INTERNAL_ENDPOINT = "/api/ctp-ticks";

export type CtpTickResponse = {
  ok: boolean;
  instrument_id: string;
  last_price?: number;
  volume?: number;
  trading_day?: string;
  update_time?: string;
  update_millisec?: number;
  bid_price1?: number;
  bid_volume1?: number;
  ask_price1?: number;
  ask_volume1?: number;
  [key: string]: unknown;
};

export type CtpContractEntry = {
  id: string;
  tick?: CtpTickResponse;
  error?: string;
};

export type UseCtpContractsOptions = {
  count?: number;
  refreshMs?: number;
};

export type UseCtpContractsResult = {
  entries: CtpContractEntry[];
  isLoading: boolean;
  isRefreshing: boolean;
  lastUpdated: Date | null;
  error: string | null;
  refresh: () => void;
};

function isAbortError(error: unknown): boolean {
  if (typeof DOMException !== "undefined" && error instanceof DOMException) {
    return error.name === "AbortError";
  }
  return error instanceof Error && error.name === "AbortError";
}

export function useCtpContracts(options?: UseCtpContractsOptions): UseCtpContractsResult {
  const { count = DEFAULT_CTP_CONTRACT_COUNT, refreshMs = DEFAULT_REFRESH_MS } = options ?? {};
  const [entries, setEntries] = useState<CtpContractEntry[]>(() => generateCtpContractIds(count).map((id) => ({ id })));
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const controllerRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  const fetchContracts = useCallback(async () => {
    setIsRefreshing(true);
    const controller = new AbortController();
    controllerRef.current?.abort();
    controllerRef.current = controller;

    const candidateIds = generateCtpContractIds(count + CTP_CONTRACT_BUFFER);
    const orderMap = new Map<string, number>();
    candidateIds.forEach((id, index) => orderMap.set(id, index));
    const query = new URLSearchParams({
      ids: candidateIds.join(","),
      count: String(count)
    });

    try {
      const res = await fetch(`${INTERNAL_ENDPOINT}?${query.toString()}`, {
        signal: controller.signal,
        cache: "no-store",
        headers: {
          "Cache-Control": "no-cache"
        }
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const payload = (await res.json()) as {
        entries?: CtpContractEntry[];
        fetchedAt?: string;
        error?: string;
      };

      if (!mountedRef.current || controller.signal.aborted) {
        return;
      }

      const responses = (payload.entries ?? []).sort((a, b) => (orderMap.get(a.id) ?? 0) - (orderMap.get(b.id) ?? 0));
      const valid = responses.filter((entry) => entry.tick).slice(0, count);
      let finalEntries = valid;

      if (valid.length < count) {
        const fallback = responses.filter((entry) => !entry.tick).slice(0, count - valid.length);
        finalEntries = [...valid, ...fallback];
      }

      setEntries(
        finalEntries.map((entry) => ({
          id: entry.id,
          tick: entry.tick,
          error: entry.error
        }))
      );
      setError(payload.error ?? null);
      setLastUpdated(payload.fetchedAt ? new Date(payload.fetchedAt) : new Date());
    } catch (err) {
      if (isAbortError(err)) {
        return;
      }
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : "请求 CTP 数据失败");
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    }
  }, [count]);

  useEffect(() => {
    mountedRef.current = true;
    fetchContracts();

    const intervalId = setInterval(() => {
      fetchContracts();
    }, refreshMs);

    return () => {
      mountedRef.current = false;
      controllerRef.current?.abort();
      clearInterval(intervalId);
    };
  }, [fetchContracts, refreshMs]);

  const refresh = useCallback(() => {
    void fetchContracts();
  }, [fetchContracts]);

  return {
    entries,
    isLoading,
    isRefreshing,
    lastUpdated,
    error,
    refresh
  };
}
