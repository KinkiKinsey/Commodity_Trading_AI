"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";

import { AppShell } from "@/components/layout/AppShell";
import { useIntl } from "@/lib/i18n/IntlContext";
import { useOilFactors } from "@/lib/hooks/useOilFactors";
import type { OilFactorRecord } from "@/lib/api/oilFactors";

const SYMBOL_OPTIONS: { label: string; value: string }[] = [
  { label: "WTI Crude (Continuous)", value: "CL=F" },
  { label: "WTI Crude (Dec 2025)", value: "CLZ25.NYM" },
  { label: "Brent Crude", value: "BZ=F" }
];

const LANGUAGE_OPTIONS: { label: string; value: "Chinese" | "English" }[] = [
  { label: "中文", value: "Chinese" },
  { label: "English", value: "English" }
];

const numberFormatter = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 4
});

function renderMetric(value: unknown) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return numberFormatter.format(value);
}

function renderDuration(value: unknown) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return `${value}d`;
}

function FactorRow({ factor }: { factor: OilFactorRecord }) {
  return (
    <tr className="border-b border-border-muted/40 text-xs last:border-0">
      <td className="whitespace-nowrap px-3 py-2 font-medium text-text-primary">{factor.factor}</td>
      <td className="px-3 py-2 uppercase text-text-secondary">{factor.scope ?? "--"}</td>
      <td className="px-3 py-2 text-text-primary">{renderMetric(factor.weighted_mean)}</td>
      <td className="px-3 py-2 text-text-primary">{renderMetric(factor.risk_reward_ratio)}</td>
      <td className="px-3 py-2 text-text-primary">{renderDuration(factor.average_duration)}</td>
      <td className="px-3 py-2 text-text-primary">
        {factor.time_interval ?? `${factor.start_date ?? "--"} → ${factor.end_date ?? "--"}`}
      </td>
      <td className="px-3 py-2 text-text-secondary">{factor.driver_type || "--"}</td>
      <td className="px-3 py-2 text-text-secondary">{factor.AI_Reason || "--"}</td>
    </tr>
  );
}

export default function OilFactorsPage() {
  const { t } = useIntl();
  const [ticker, setTicker] = useState(SYMBOL_OPTIONS[0]!.value);
  const [language, setLanguage] = useState<"Chinese" | "English">("Chinese");

  const { query, factors } = useOilFactors({
    ticker,
    language
  });

  const headline = useMemo(() => {
    if (query.isLoading) return t("oilFactors.loading", "Loading oil factors…");
    if (query.isError) return t("oilFactors.error", "Failed to load oil factors");
    return t("oilFactors.title", "Oil Factor Dashboard");
  }, [query.isError, query.isLoading, t]);

  const mainColumn = (
    <div className="flex flex-col gap-6">
      <section className="flex flex-wrap items-center gap-4">
        <div>
          <label className="mb-1 block text-xs uppercase tracking-[0.2em] text-text-secondary">
            {t("oilFactors.selectSymbol", "Symbol")}
          </label>
          <select
            value={ticker}
            onChange={(event) => setTicker(event.target.value)}
            className="rounded-lg border border-border-muted bg-bg-panel px-3 py-2 text-sm text-text-primary"
          >
            {SYMBOL_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs uppercase tracking-[0.2em] text-text-secondary">
            {t("oilFactors.selectLanguage", "Language")}
          </label>
          <div className="flex gap-2">
            {LANGUAGE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setLanguage(option.value)}
                className={clsx(
                  "rounded-lg px-3 py-2 text-xs font-medium transition-colors",
                  language === option.value
                    ? "bg-accent-primary text-white"
                    : "border border-border-muted bg-bg-panel text-text-secondary hover:text-text-primary"
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-border-muted bg-bg-panel/80 p-4 shadow-[0_12px_32px_rgba(0,0,0,0.35)]">
        <header className="flex flex-col gap-1 pb-4">
          <h2 className="text-sm font-semibold text-text-primary">{headline}</h2>
          <p className="text-xs text-text-secondary">
            {t(
              "oilFactors.subtitle",
              "AI-ranked macro and micro drivers behind recent crude oil price moves."
            )}
          </p>
        </header>

        {query.isLoading ? (
          <div className="py-12 text-center text-sm text-text-secondary">
            {t("oilFactors.loading", "Loading oil factors…")}
          </div>
        ) : query.isError ? (
          <div className="py-12 text-center text-sm text-error">
            {t("oilFactors.error", "Unable to load oil factors. Please retry later.")}
          </div>
        ) : factors.length === 0 ? (
          <div className="py-12 text-center text-sm text-text-secondary">
            {t("oilFactors.empty", "No oil factor metrics are available for this symbol yet.")}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border-muted/40 text-left">
              <thead className="text-[10px] uppercase tracking-[0.2em] text-text-secondary">
                <tr>
                  <th className="px-3 py-2 font-semibold">{t("oilFactors.columns.factor", "Factor")}</th>
                  <th className="px-3 py-2 font-semibold">{t("oilFactors.columns.scope", "Scope")}</th>
                  <th className="px-3 py-2 font-semibold">
                    {t("oilFactors.columns.weightedMean", "Weighted Mean")}
                  </th>
                  <th className="px-3 py-2 font-semibold">{t("oilFactors.columns.riskReward", "Risk/Reward")}</th>
                  <th className="px-3 py-2 font-semibold">{t("oilFactors.columns.avgDuration", "Avg Duration")}</th>
                  <th className="px-3 py-2 font-semibold">{t("oilFactors.columns.timeRange", "Time Range")}</th>
                  <th className="px-3 py-2 font-semibold">{t("oilFactors.columns.driverType", "Driver Type")}</th>
                  <th className="px-3 py-2 font-semibold">{t("oilFactors.columns.reason", "AI Reasoning")}</th>
                </tr>
              </thead>
              <tbody>
                {factors.map((factor) => (
                  <FactorRow key={`${factor.factor}-${factor.start_date}-${factor.end_date}`} factor={factor} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );

  return <AppShell mainColumn={mainColumn} />;
}

