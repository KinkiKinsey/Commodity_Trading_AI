
import { NextRequest, NextResponse } from "next/server";

import { CTP_CONTRACT_BUFFER, DEFAULT_CTP_CONTRACT_COUNT, generateCtpContractIds, normalizeContractId } from "@/lib/utils/ctpContracts";

const BACKEND_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const DEFAULT_REALTIME_ENDPOINT = `${BACKEND_BASE_URL.replace(/\/$/, "")}/api/ctp/realtime`;
const CTP_REALTIME_ENDPOINT = process.env.CTP_REALTIME_ENDPOINT ?? DEFAULT_REALTIME_ENDPOINT;
const REQUEST_TIMEOUT_MS = 4000;

type BackendRealtimeResponse = {
  symbol: string;
  last_price: number;
  volume: number;
  update_time: string;
  update_millisec: number;
  local_timestamp: string;
  exchange_timestamp?: string | null;
  bid?: { price?: number; volume?: number };
  ask?: { price?: number; volume?: number };
  metadata?: Record<string, unknown>;
};

type CtpTickResponse = {
  ok: boolean;
  instrument_id: string;
  last_price?: number;
  volume?: number;
  update_time?: string;
  update_millisec?: number;
  bid_price1?: number;
  bid_volume1?: number;
  ask_price1?: number;
  ask_volume1?: number;
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
    const responses = await Promise.all(
      candidateIds.map(async (id) => {
        try {
          const url = new URL(CTP_REALTIME_ENDPOINT);
          url.searchParams.set("symbol", id);
          const res = await fetch(url.toString(), {
            signal: abortController.signal,
            cache: "no-store",
            headers: { "Cache-Control": "no-cache" }
          });

          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }

          const data = (await res.json()) as BackendRealtimeResponse;
          return { id, tick: mapRealtimeToTick(data) } satisfies ApiEntry;
        } catch (error) {
          const message = error instanceof Error ? error.message : "Unknown error";
          return { id, error: message } satisfies ApiEntry;
        }
      })
    );

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

function mapRealtimeToTick(payload: BackendRealtimeResponse): CtpTickResponse {
  return {
    ok: true,
    instrument_id: payload.symbol,
    last_price: payload.last_price,
    volume: payload.volume,
    update_time: payload.update_time,
    update_millisec: payload.update_millisec,
    bid_price1: payload.bid?.price,
    bid_volume1: payload.bid?.volume,
    ask_price1: payload.ask?.price,
    ask_volume1: payload.ask?.volume,
    local_timestamp: payload.local_timestamp,
    exchange_timestamp: payload.exchange_timestamp,
    metadata: payload.metadata
  };
}
