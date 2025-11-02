"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";
import { useIntl, type TranslationKey } from "@/lib/i18n/IntlContext";

type TickerDirection = "up" | "down" | "flat";

type LocalisedName = {
  zh: string;
  en: string;
};

type MarketItem = {
  name: LocalisedName;
  value: number;
  changePct: number;
  direction: TickerDirection;
};

type CategoryKey = "top" | "indices" | "rates";

const CATEGORY_KEYS: CategoryKey[] = ["top", "indices", "rates"];

const CATEGORY_LABEL_KEYS: Record<CategoryKey, TranslationKey> = {
  top: "marketTicker.category.top",
  indices: "marketTicker.category.indices",
  rates: "marketTicker.category.rates"
};

const MARKET_DATA: Record<CategoryKey, MarketItem[]> = {
  top: [
    { name: { zh: "标普500", en: "S&P 500" }, value: 6791.69, changePct: 0.79, direction: "up" },
    { name: { zh: "纳斯达克100", en: "Nasdaq 100" }, value: 23204.87, changePct: 1.15, direction: "up" },
    { name: { zh: "恒生科技", en: "Hang Seng Tech" }, value: 4386.21, changePct: -0.35, direction: "down" },
    { name: { zh: "WTI 原油", en: "WTI Crude" }, value: 81.5, changePct: 0.42, direction: "up" },
    { name: { zh: "伦敦金", en: "London Gold" }, value: 2351.2, changePct: -0.12, direction: "down" }
  ],
  indices: [
    { name: { zh: "上证综指", en: "SSE Composite" }, value: 3112.44, changePct: -0.18, direction: "down" },
    { name: { zh: "沪深300", en: "CSI 300" }, value: 3550.12, changePct: 0.36, direction: "up" },
    { name: { zh: "创业板指", en: "ChiNext" }, value: 2109.77, changePct: 0.52, direction: "up" },
    { name: { zh: "恒生指数", en: "Hang Seng" }, value: 18205.4, changePct: 0.54, direction: "up" },
    { name: { zh: "日经225", en: "Nikkei 225" }, value: 32950.68, changePct: -0.27, direction: "down" }
  ],
  rates: [
    { name: { zh: "美债10年", en: "US 10Y Treasury" }, value: 4.02, changePct: 0.03, direction: "up" },
    { name: { zh: "英债10年", en: "UK 10Y Gilt" }, value: 2.35, changePct: -0.02, direction: "down" },
    { name: { zh: "美国联邦基金目标", en: "Fed Funds Target" }, value: 5.33, changePct: 0, direction: "flat" },
    { name: { zh: "欧元区基准利率", en: "ECB Policy Rate" }, value: 3.75, changePct: 0, direction: "flat" },
    { name: { zh: "美元指数", en: "US Dollar Index" }, value: 103.42, changePct: -0.11, direction: "down" }
  ]
};

const DIRECTION_META: Record<TickerDirection, { tone: string; labelKey: TranslationKey }> = {
  up: { tone: "text-accent-bull", labelKey: "marketTicker.arrow.up" },
  down: { tone: "text-accent-bear", labelKey: "marketTicker.arrow.down" },
  flat: { tone: "text-white/70", labelKey: "marketTicker.arrow.flat" }
};

export function MarketTicker() {
  const { locale, t } = useIntl();
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<CategoryKey>("top");

  const formatter = useMemo(
    () =>
      new Intl.NumberFormat(locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }),
    [locale]
  );

  const items = MARKET_DATA[category];
  const selectedLabel = t(CATEGORY_LABEL_KEYS[category]);

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
            <div className="absolute left-0 top-full z-[60] mt-2 w-44 overflow-hidden rounded-lg border border-white/20 bg-black/95 shadow-lg">
              {CATEGORY_KEYS.map((option) => (
                <button
                  key={option}
                  type="button"
                  className={clsx(
                    "block w-full px-4 py-2 text-left text-xs tracking-[0.12em] transition",
                    option === category
                      ? "bg-white/10 text-white"
                      : "text-white/70 hover:bg-white/10 hover:text-white"
                  )}
                  onClick={() => {
                    setCategory(option);
                    setOpen(false);
                  }}
                >
                  {t(CATEGORY_LABEL_KEYS[option])}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex flex-1 items-center gap-2 overflow-x-auto">
          {items.map((item) => {
            const { tone, labelKey } = DIRECTION_META[item.direction];
            const displayName = locale === "zh-CN" ? item.name.zh : item.name.en;
            return (
              <div
                key={displayName}
                className="inline-flex min-w-[180px] items-center gap-3 rounded-full bg-white/10 px-4 py-2 text-xs tracking-[0.08em]"
              >
                <span className="font-semibold text-white">{displayName}</span>
                <span className="tabular-nums text-white/80">{formatter.format(item.value)}</span>
                <span className={clsx("tabular-nums", tone)}>
                  {t(labelKey)} {Math.abs(item.changePct).toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
