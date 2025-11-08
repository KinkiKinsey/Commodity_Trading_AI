"use client";

import clsx from "clsx";
import { useMemo } from "react";

import { useCtpContracts, type CtpContractEntry } from "@/lib/hooks/useCtpContracts";

type PanelLabels = {
  title: string;
  subtitle: string;
  last: string;
  spread: string;
  volume: string;
  bid: string;
  ask: string;
  updated: string;
  refresh: string;
  refreshing: string;
  waiting: string;
  error: string;
  latency: string;
};

type ContractCard = {
  id: string;
  last: number | null;
  bid: number | null;
  ask: number | null;
  spread: number | null;
  volume: number | null;
  updateLabel: string | null;
  latencyLabel: string | null;
  status: "ok" | "pending" | "error";
  note?: string;
};

type CtpContractsPanelProps = {
  locale: string;
};

export function CtpContractsPanel({ locale }: CtpContractsPanelProps) {
  const { entries, isLoading, isRefreshing, lastUpdated, error, refresh } = useCtpContracts({
    count: 6,
    refreshMs: 5000
  });

  const isZh = locale.startsWith("zh");

  const labels = useMemo<PanelLabels>(
    () => ({
      title: isZh ? "CTP 合约追踪" : "CTP Contracts",
      subtitle: isZh ? "5 秒自动刷新" : "Auto refresh · 5s",
      last: isZh ? "最新价" : "Last",
      spread: isZh ? "点差" : "Spread",
      volume: isZh ? "成交量" : "Volume",
      bid: isZh ? "买一" : "Bid",
      ask: isZh ? "卖一" : "Ask",
      updated: isZh ? "最后同步" : "Last sync",
      refresh: isZh ? "刷新" : "Refresh",
      refreshing: isZh ? "刷新中" : "Refreshing",
      waiting: isZh ? "等待数据" : "Pending",
      error: isZh ? "数据暂不可用" : "Data unavailable",
      latency: isZh ? "延迟" : "Latency"
    }),
    [isZh]
  );

  const priceFormatter = useMemo(
    () =>
      new Intl.NumberFormat(locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }),
    [locale]
  );

  const volumeFormatter = useMemo(
    () =>
      new Intl.NumberFormat(locale, {
        notation: "compact",
        maximumFractionDigits: 1
      }),
    [locale]
  );

  const timeFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }),
    [locale]
  );

  const cards = useMemo<ContractCard[]>(
    () => entries.map((entry) => mapEntryToCard(entry, timeFormatter, labels)),
    [entries, timeFormatter, labels]
  );

  const updatedLabel = useMemo(() => {
    if (!lastUpdated) {
      return labels.waiting;
    }
    return `${labels.updated} · ${timeFormatter.format(lastUpdated)}`;
  }, [lastUpdated, labels.updated, labels.waiting, timeFormatter]);

  return (
    <section className="rounded-2xl border border-border-muted bg-white/95 p-5 shadow-[0_12px_32px_rgba(15,23,42,0.12)] backdrop-blur-sm">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-text-primary">{labels.title}</h3>
          <p className="mt-1 text-xs text-text-secondary">{labels.subtitle}</p>
          <p className="mt-1 text-[10px] text-text-tertiary">{updatedLabel}</p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={isRefreshing}
          className={clsx(
            "rounded-full border px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] transition",
            isRefreshing
              ? "border-border-muted text-text-secondary"
              : "border-black text-black hover:bg-black hover:text-white"
          )}
        >
          {isRefreshing ? labels.refreshing : labels.refresh}
        </button>
      </header>

      {error ? (
        <div className="mt-3 rounded-lg border border-error/40 bg-error/5 px-3 py-2 text-[11px] text-error">
          {labels.error}: {error}
        </div>
      ) : null}

      <div className="mt-4 grid grid-cols-1 gap-4">
        {cards.map((card) => (
          <article
            key={card.id}
            className="w-full rounded-2xl border border-border-muted/80 bg-white/90 p-4 shadow-[0_10px_26px_rgba(15,23,42,0.08)] transition hover:-translate-y-0.5 hover:border-accent-primary/50"
          >
            <div className="flex flex-col gap-1">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-primary">{card.id}</p>
              <p className="text-[11px] text-text-secondary">{card.updateLabel ?? labels.waiting}</p>
            </div>

            <div className="mt-4 flex items-end justify-between gap-4">
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-text-secondary">{labels.last}</p>
                <p
                  className={clsx(
                    "text-2xl font-semibold tabular-nums",
                    card.status === "error"
                      ? "text-error"
                      : card.status === "pending"
                        ? "text-text-secondary"
                        : "text-text-primary"
                  )}
                >
                  {card.last !== null ? priceFormatter.format(card.last) : "--"}
                </p>
              </div>
              <div className="text-right text-[11px] text-text-secondary">
                <p>
                  {labels.bid}: {card.bid !== null ? priceFormatter.format(card.bid) : "--"}
                </p>
                <p>
                  {labels.ask}: {card.ask !== null ? priceFormatter.format(card.ask) : "--"}
                </p>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-[11px] text-text-secondary">
              <div>
                <p className="terminal-text text-[10px] uppercase tracking-[0.18em]">{labels.spread}</p>
                <p className="mt-1 text-sm font-semibold tabular-nums text-text-primary">
                  {card.spread !== null ? priceFormatter.format(card.spread) : "--"}
                </p>
              </div>
              <div className="text-right">
                <p className="terminal-text text-[10px] uppercase tracking-[0.18em]">{labels.volume}</p>
                <p className="mt-1 text-sm font-semibold tabular-nums text-text-primary">
                  {card.volume !== null ? volumeFormatter.format(card.volume) : "--"}
                </p>
              </div>
            </div>

            <div className="mt-3 flex items-center justify-between text-[11px] text-text-tertiary">
              <span>{card.latencyLabel ?? ""}</span>
              {card.note ? <span className="text-error">{card.note}</span> : null}
            </div>
            {card.note ? (
              <p className="mt-2 rounded-lg border border-error/30 bg-error/5 px-3 py-1 text-[11px] text-error">{card.note}</p>
            ) : null}
          </article>
        ))}

        {!cards.length && !isLoading ? (
          <div className="rounded-xl border border-border-muted bg-bg-alt/30 px-4 py-6 text-center text-xs text-text-secondary">
            {labels.waiting}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function mapEntryToCard(entry: CtpContractEntry, timeFormatter: Intl.DateTimeFormat, labels: PanelLabels): ContractCard {
  const tick = entry.tick;
  const bid = typeof tick?.bid_price1 === "number" ? tick.bid_price1 : null;
  const ask = typeof tick?.ask_price1 === "number" ? tick.ask_price1 : null;
  const last = typeof tick?.last_price === "number" ? tick.last_price : null;
  const spread = bid !== null && ask !== null ? ask - bid : null;
  const volume = typeof tick?.volume === "number" ? tick.volume : null;
  const updateLabel = buildUpdateLabel(tick, timeFormatter);
  const latencySeconds =
    typeof tick?.metadata?.data_latency_seconds === "number" ? Number(tick.metadata.data_latency_seconds) : null;
  const latencyLabel = latencySeconds !== null ? `${labels.latency} · ${Math.round(latencySeconds)}s` : null;
  const status: ContractCard["status"] = tick ? "ok" : entry.error ? "error" : "pending";

  return {
    id: entry.id,
    last,
    bid,
    ask,
    spread,
    volume,
    updateLabel,
    latencyLabel,
    status,
    note: entry.error
  };
}

function buildUpdateLabel(tick: CtpContractEntry["tick"], timeFormatter: Intl.DateTimeFormat): string | null {
  if (!tick?.trading_day || !tick.update_time) {
    return null;
  }

  const day = tick.trading_day;

  if (day.length !== 8) {
    return null;
  }

  const year = Number(day.slice(0, 4));
  const month = day.slice(4, 6);
  const date = day.slice(6, 8);
  const millis = tick.update_millisec ?? 0;
  const isoString = `${year}-${month}-${date}T${tick.update_time}.${millis.toString().padStart(3, "0")}Z`;

  const parsed = new Date(isoString);

  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return timeFormatter.format(parsed);
}
