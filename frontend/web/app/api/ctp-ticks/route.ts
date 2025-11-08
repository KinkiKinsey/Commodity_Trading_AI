
import { NextRequest, NextResponse } from "next/server";

import { CTP_CONTRACT_BUFFER, DEFAULT_CTP_CONTRACT_COUNT, generateCtpContractIds, normalizeContractId } from "@/lib/utils/ctpContracts";

const CTP_TICK_BASE_URL = process.env.CTP_TICK_BASE_URL ?? "http://47.108.177.50:8080/md/tick";
const REQUEST_TIMEOUT_MS = 4000;

type CtpTickResponse = {
  ok: boolean;
  instrument_id: string;
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
          const res = await fetch(`${CTP_TICK_BASE_URL}/${id}`, {
            signal: abortController.signal,
            cache: "no-store"
          });

          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }

          const data = (await res.json()) as CtpTickResponse;
          return { id, tick: data } satisfies ApiEntry;
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
