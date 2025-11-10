
import { NextRequest, NextResponse } from "next/server";

import { CTP_CONTRACT_BUFFER, DEFAULT_CTP_CONTRACT_COUNT, generateCtpContractIds, normalizeContractId } from "@/lib/utils/ctpContracts";

const BACKEND_BASE_URL = stripTrailingSlash(process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000");
const DEFAULT_REALTIME_ENDPOINT = appendPath(BACKEND_BASE_URL, "/api/ctp/realtime");
const DEFAULT_PRICING_TICK_ENDPOINT = appendPath(BACKEND_BASE_URL, "/api/pricing/tick");

const CTP_REALTIME_ENDPOINT = resolveEndpoint(
  process.env.CTP_REALTIME_ENDPOINT ?? process.env.NEXT_PUBLIC_CTP_REALTIME_ENDPOINT,
  DEFAULT_REALTIME_ENDPOINT
);
const PRICING_TICK_ENDPOINT = resolveEndpoint(
  process.env.PRICING_TICK_ENDPOINT ?? process.env.NEXT_PUBLIC_PRICING_TICK_ENDPOINT,
  DEFAULT_PRICING_TICK_ENDPOINT
);

const REQUEST_TIMEOUT_MS = 4000;

type PricingMetadataPayload = {
  fetched_at: string;
  data_latency_seconds?: number;
  source_latency_seconds?: number | null;
  notes?: string | null;
  [key: string]: unknown;
};

type QuotePayload = { price?: number | null; volume?: number | null } | null | undefined;

type BackendRealtimeResponse = {
  symbol: string;
  last_price: number;
  volume: number;
  update_time: string;
  update_millisec: number;
  local_timestamp: string;
  exchange_timestamp?: string | null;
  bid?: QuotePayload;
  ask?: QuotePayload;
  metadata?: PricingMetadataPayload;
};

type PricingTickFallbackResponse = {
  instrument_id: string;
  last_price: number;
  volume: number;
  trading_day: string;
  updated_at: string;
  bid: { price: number; volume: number };
  ask: { price: number; volume: number };
  raw?: Record<string, unknown>;
};

type CtpTickResponse = {
  ok: boolean;
  instrument_id: string;
  last_price?: number;
  volume?: number;
  trading_day?: string;
  update_time?: string;
  update_millisec?: number;
  local_timestamp?: string;
  exchange_timestamp?: string | null;
  bid_price1?: number;
  bid_volume1?: number;
  ask_price1?: number;
  ask_volume1?: number;
  metadata?: PricingMetadataPayload;
  [key: string]: unknown;
};

type ApiEntry = {
  id: string;
  tick?: CtpTickResponse;
  error?: string;
};

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const idsParam = searchParams.get("ids");
  const countParam = Number.parseInt(searchParams.get("count") ?? "", 10);

  const requestedCount = Number.isFinite(countParam) && countParam > 0 ? Math.min(countParam, 24) : DEFAULT_CTP_CONTRACT_COUNT;
  const candidateIds = idsParam
    ? idsParam
        .split(",")
        .map((id) => normalizeContractId(id))
        .filter((id): id is string => Boolean(id))
    : generateCtpContractIds(requestedCount + CTP_CONTRACT_BUFFER);

  if (!candidateIds.length) {
    return NextResponse.json({ entries: [], error: "No valid contract IDs provided" }, { status: 400 });
  }

  const abortController = new AbortController();
  const timeoutId = setTimeout(() => abortController.abort(), REQUEST_TIMEOUT_MS);

  try {
    const responses = await Promise.all(candidateIds.map((id) => fetchTickEntry(id, abortController.signal)));

    return NextResponse.json(
      {
        entries: responses,
        fetchedAt: new Date().toISOString()
      },
      {
        status: 200,
        headers: {
          "Cache-Control": "no-store"
        }
      }
    );
  } finally {
    clearTimeout(timeoutId);
  }
}

async function fetchTickEntry(id: string, signal: AbortSignal): Promise<ApiEntry> {
  try {
    const payload = await fetchRealtimeTick(id, signal);
    return { id, tick: mapRealtimeToTick(payload) };
  } catch (realtimeError) {
    if (signal.aborted || isAbortError(realtimeError)) {
      const message = realtimeError instanceof Error ? realtimeError.message : "Request aborted";
      return { id, error: message };
    }

    try {
      const fallback = await fetchPricingTick(id, signal);
      return { id, tick: mapPricingTickToCtpTick(fallback) };
    } catch (fallbackError) {
      if (isAbortError(fallbackError)) {
        const message = fallbackError instanceof Error ? fallbackError.message : "Request aborted";
        return { id, error: message };
      }
      const realtimeMessage = realtimeError instanceof Error ? realtimeError.message : String(realtimeError);
      const fallbackMessage = fallbackError instanceof Error ? fallbackError.message : "Unknown error";
      const combined = fallbackMessage === realtimeMessage ? fallbackMessage : `${fallbackMessage} (realtime: ${realtimeMessage})`;
      return { id, error: combined };
    }
  }
}

async function fetchRealtimeTick(symbol: string, signal: AbortSignal): Promise<BackendRealtimeResponse> {
  const url = new URL(CTP_REALTIME_ENDPOINT);
  url.searchParams.set("symbol", symbol);
  const res = await fetch(url.toString(), {
    signal,
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" }
  });

  if (!res.ok) {
    throw new Error(`Realtime HTTP ${res.status}`);
  }

  return (await res.json()) as BackendRealtimeResponse;
}

async function fetchPricingTick(instrumentId: string, signal: AbortSignal): Promise<PricingTickFallbackResponse> {
  const url = new URL(PRICING_TICK_ENDPOINT);
  url.searchParams.set("instrument_id", instrumentId);
  const res = await fetch(url.toString(), {
    signal,
    cache: "no-store",
    headers: { "Cache-Control": "no-cache" }
  });

  if (!res.ok) {
    throw new Error(`Pricing tick HTTP ${res.status}`);
  }

  return (await res.json()) as PricingTickFallbackResponse;
}

function mapRealtimeToTick(payload: BackendRealtimeResponse): CtpTickResponse {
  const tradingDay =
    deriveTradingDayFromTimestamp(payload.exchange_timestamp) ?? deriveTradingDayFromTimestamp(payload.local_timestamp);

  return {
    ok: true,
    instrument_id: payload.symbol,
    last_price: payload.last_price,
    volume: payload.volume,
    trading_day: tradingDay,
    update_time: payload.update_time,
    update_millisec: payload.update_millisec,
    bid_price1: typeof payload.bid?.price === "number" ? payload.bid?.price : undefined,
    bid_volume1: typeof payload.bid?.volume === "number" ? payload.bid?.volume : undefined,
    ask_price1: typeof payload.ask?.price === "number" ? payload.ask?.price : undefined,
    ask_volume1: typeof payload.ask?.volume === "number" ? payload.ask?.volume : undefined,
    local_timestamp: payload.local_timestamp,
    exchange_timestamp: payload.exchange_timestamp,
    metadata: payload.metadata
  };
}

function mapPricingTickToCtpTick(payload: PricingTickFallbackResponse): CtpTickResponse {
  const updatedAt = safeDate(payload.updated_at);
  const fallbackNow = new Date();
  const isoTimestamp = (updatedAt ?? fallbackNow).toISOString();
  const tradingDay =
    formatTradingDayString(payload.trading_day) ??
    (updatedAt ? formatTradingDay(updatedAt) : deriveTradingDayFromTimestamp(isoTimestamp));
  const latency = updatedAt ? Math.max(0, (fallbackNow.getTime() - updatedAt.getTime()) / 1000) : undefined;

  return {
    ok: true,
    instrument_id: payload.instrument_id,
    last_price: payload.last_price,
    volume: payload.volume,
    trading_day: tradingDay,
    update_time: updatedAt ? formatTime(updatedAt) : undefined,
    update_millisec: updatedAt ? updatedAt.getUTCMilliseconds() : undefined,
    bid_price1: payload.bid?.price,
    bid_volume1: payload.bid?.volume,
    ask_price1: payload.ask?.price,
    ask_volume1: payload.ask?.volume,
    local_timestamp: isoTimestamp,
    exchange_timestamp: isoTimestamp,
    metadata: {
      fetched_at: fallbackNow.toISOString(),
      data_latency_seconds: latency,
      source_latency_seconds: null,
      notes: "Fallback via /api/pricing/tick"
    }
  };
}

function deriveTradingDayFromTimestamp(timestamp?: string | null): string | undefined {
  const parsed = safeDate(timestamp);
  if (!parsed) {
    return undefined;
  }
  return formatTradingDay(parsed);
}

function formatTradingDay(date: Date): string {
  const year = date.getUTCFullYear().toString().padStart(4, "0");
  const month = (date.getUTCMonth() + 1).toString().padStart(2, "0");
  const day = date.getUTCDate().toString().padStart(2, "0");
  return `${year}${month}${day}`;
}

function formatTradingDayString(value?: string | null): string | undefined {
  if (!value) {
    return undefined;
  }
  const digits = value.replace(/[^0-9]/g, "");
  if (digits.length === 8) {
    return digits;
  }
  return undefined;
}

function formatTime(date: Date): string {
  const hours = date.getUTCHours().toString().padStart(2, "0");
  const minutes = date.getUTCMinutes().toString().padStart(2, "0");
  const seconds = date.getUTCSeconds().toString().padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}

function safeDate(value?: string | null): Date | null {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}

function stripTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function appendPath(base: string, path: string): string {
  const normalizedBase = stripTrailingSlash(base);
  return `${normalizedBase}${path.startsWith("/") ? path : `/${path}`}`;
}

function resolveEndpoint(envValue: string | undefined, defaultUrl: string): string {
  if (!envValue) {
    return defaultUrl;
  }
  const trimmed = envValue.trim();
  if (!trimmed) {
    return defaultUrl;
  }
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  if (trimmed.startsWith("/")) {
    return `${BACKEND_BASE_URL}${trimmed}`;
  }
  return appendPath(BACKEND_BASE_URL, trimmed);
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}
