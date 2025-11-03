"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";
import { OilFactorsOverlayChart } from "@/components/charts/OilFactorsOverlayChart";
import { AppShell } from "@/components/layout/AppShell";
import { OilFactorsSidebar } from "@/components/oil/OilFactorsSidebar";
import { useIntl } from "@/lib/i18n/IntlContext";
import { useOilFactors } from "@/lib/hooks/useOilFactors";
import { buildOverlayData } from "@/lib/utils/oilFactors";

const SYMBOL_OPTIONS: { label: string; value: string }[] = [
  { label: "WTI Crude (Continuous)", value: "CL=F" },
  { label: "WTI Crude (Dec 2025)", value: "CLZ25.NYM" },
  { label: "Brent Crude", value: "BZ=F" }
];

const LANGUAGE_OPTIONS: { label: string; value: "Chinese" | "English" }[] = [
  { label: "中文", value: "Chinese" },
  { label: "English", value: "English" }
];


export default function OilFactorsPage() {
  const { t } = useIntl();
  const [ticker, setTicker] = useState(SYMBOL_OPTIONS[0]!.value);
  const [language, setLanguage] = useState<"Chinese" | "English">("Chinese");

  const { query, factors } = useOilFactors({
    ticker,
    language
  });

  const overlayData = useMemo(() => buildOverlayData(factors), [factors]);
  const microPoints = overlayData.micro;
  const macroPoints = overlayData.macro;

  let chartSection: JSX.Element;
  if (query.isLoading) {
    chartSection = (
      <div className="py-16 text-center text-sm text-slate-500">
        {t("oilFactors.loading", "Loading oil factors...")}
      </div>
    );
  } else if (query.isError) {
    chartSection = (
      <div className="py-16 text-center text-sm text-red-500">
        {t("oilFactors.error", "Failed to load oil factors. Please retry.")}
      </div>
    );
  } else if (!microPoints.length && !macroPoints.length) {
    chartSection = (
      <div className="py-16 text-center text-sm text-slate-500">
        {t("oilFactors.emptyMicro", "No micro factor data is available yet.")}
      </div>
    );
  } else {
    chartSection = (
      <div className="flex flex-col gap-6 xl:flex-row">
        <div className="flex-1 rounded-2xl border border-border-muted bg-white p-6 shadow-[0_8px_20px_rgba(15,23,42,0.08)] xl:p-8">
          <OilFactorsOverlayChart
            micro={microPoints}
            macro={macroPoints}
            height={860}
            showAnnotations
            className="w-full"
          />
        </div>
        <OilFactorsSidebar micro={microPoints} macro={macroPoints} className="xl:w-80 2xl:w-96" />
      </div>
    );
  }
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

      {chartContent}
    </div>
  );

  return <AppShell mainColumn={mainColumn} />;
}
