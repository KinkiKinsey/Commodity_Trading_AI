"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";

type TickerDirection = "up" | "down" | "flat";

type MarketItem = {
  name: string;
  value: number;
  changePct: number;
  direction: TickerDirection;
};

type CategoryKey = "top" | "indices" | "rates";

const CATEGORY_OPTIONS: { id: CategoryKey; label: string }[] = [
  { id: "top", label: "精选证券" },
  { id: "indices", label: "市场指数" },
  { id: "rates", label: "利率与债券" }
];

const MARKET_DATA: Record<CategoryKey, MarketItem[]> = {
  top: [
    { name: "标普500", value: 6791.69, changePct: 0.79, direction: "up" },
    { name: "纳斯达克100", value: 23204.87, changePct: 1.15, direction: "up" },
    { name: "恒生科技", value: 4386.21, changePct: -0.35, direction: "down" },
    { name: "WTI 原油", value: 81.5, changePct: 0.42, direction: "up" },
    { name: "伦敦金", value: 2351.2, changePct: -0.12, direction: "down" }
  ],
  indices: [
    { name: "上证综指", value: 3112.44, changePct: -0.18, direction: "down" },
    { name: "沪深300", value: 3550.12, changePct: 0.36, direction: "up" },
    { name: "创业板指", value: 2109.77, changePct: 0.52, direction: "up" },
    { name: "恒生指数", value: 18205.4, changePct: 0.54, direction: "up" },
    { name: "日经225", value: 32950.68, changePct: -0.27, direction: "down" }
  ],
  rates: [
    { name: "美债10年", value: 4.02, changePct: 0.03, direction: "up" },
    { name: "英债10年", value: 2.35, changePct: -0.02, direction: "down" },
    { name: "美国联邦基金目标", value: 5.33, changePct: 0, direction: "flat" },
    { name: "欧元区基准利率", value: 3.75, changePct: 0, direction: "flat" },
    { name: "美元指数", value: 103.42, changePct: -0.11, direction: "down" }
  ]
};

const DIRECTION_META: Record<TickerDirection, { icon: string; tone: string }> = {
  up: { icon: "▲", tone: "text-accent-bull" },
  down: { icon: "▼", tone: "text-accent-bear" },
  flat: { icon: "→", tone: "text-white/70" }
};

export function MarketTicker() {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<CategoryKey>("top");

  const formatter = useMemo(
    () =>
      new Intl.NumberFormat("zh-CN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }),
    []
  );

  const items = MARKET_DATA[category];
  const selectedLabel = CATEGORY_OPTIONS.find((option) => option.id === category)?.label ?? "";

  return (
    <div className="border-t border-white/10 bg-black/90">
      <div className="mx-auto flex w-full max-w-[1440px] items-center gap-4 px-4 py-3 text-xs text-white lg:px-8">
        <div className="relative">
          <button
            type="button"
            onClick={() => setOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-white/30 px-4 py-2 text-xs font-medium tracking-[0.16em] uppercase text-white/80 transition hover:border-white hover:text-white"
          >
            <span>{selectedLabel}</span>
            <span className="text-[10px]">{open ? "▲" : "▼"}</span>
          </button>
          {open ? (
            <div className="absolute left-0 top-full z-[60] mt-2 w-40 overflow-hidden rounded-lg border border-white/20 bg-black/95 shadow-lg">
              {CATEGORY_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={clsx(
                    "block w-full px-4 py-2 text-left text-xs tracking-[0.12em] transition",
                    option.id === category
                      ? "bg-white/10 text-white"
                      : "text-white/70 hover:bg-white/10 hover:text-white"
                  )}
                  onClick={() => {
                    setCategory(option.id);
                    setOpen(false);
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex flex-1 items-center gap-2 overflow-x-auto">
          {items.map((item) => {
            const { icon, tone } = DIRECTION_META[item.direction];
            return (
              <div
                key={item.name}
                className="inline-flex min-w-[180px] items-center gap-3 rounded-full bg-white/10 px-4 py-2 text-xs tracking-[0.08em]"
              >
                <span className="font-semibold text-white">{item.name}</span>
                <span className="tabular-nums text-white/80">{formatter.format(item.value)}</span>
                <span className={clsx("tabular-nums", tone)}>
                  {icon} {Math.abs(item.changePct).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
