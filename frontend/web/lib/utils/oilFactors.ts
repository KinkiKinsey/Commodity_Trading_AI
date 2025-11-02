"use client";

import type { LineSeriesDefinition } from "@/components/charts/BloombergLineChart";
import type { OilFactorRecord } from "@/lib/api/oilFactors";

const DATE_PATTERN = /\d{4}-\d{2}-\d{2}/;

export function normaliseDateString(value?: string | null): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = new Date(trimmed);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString().slice(0, 10);
}

export function resolvePlotDate(factor: OilFactorRecord): string | null {
  const end = normaliseDateString(factor.end_date);
  if (end) return end;
  const start = normaliseDateString(factor.start_date);
  if (start) return start;
  if (factor.time_interval) {
    const match = factor.time_interval.match(DATE_PATTERN);
    if (match?.[0]) {
      return normaliseDateString(match[0]);
    }
  }
  return null;
}

export function formatInterval(factor: OilFactorRecord): string {
  if (factor.time_interval && factor.time_interval.trim()) {
    return factor.time_interval;
  }
  const start = factor.start_date && factor.start_date.trim() ? factor.start_date : "--";
  const end = factor.end_date && factor.end_date.trim() ? factor.end_date : "--";
  return `${start} -> ${end}`;
}

export function isMicroScope(scope: string | undefined | null): boolean {
  return scope ? scope.trim().toLowerCase().startsWith("micro") : false;
}

export function isMacroScope(scope: string | undefined | null): boolean {
  return scope ? scope.trim().toLowerCase().startsWith("macro") : false;
}

const DEFAULT_SERIES_OPTIONS = {
  fallbackName: "Unnamed factor"
};

type BuildSeriesOptions = {
  fallbackName?: string;
};

function toNumeric(value: unknown): number | null {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function sortByTimeAsc<T extends { time: string }>(data: T[]): T[] {
  return [...data].sort((a, b) => (a.time === b.time ? 0 : a.time < b.time ? -1 : 1));
}

export function buildMicroLineSeries(
  factors: OilFactorRecord[],
  options: BuildSeriesOptions = DEFAULT_SERIES_OPTIONS
): LineSeriesDefinition[] {
  const fallbackName = options.fallbackName ?? DEFAULT_SERIES_OPTIONS.fallbackName;
  const groups = new Map<string, LineSeriesDefinition>();

  factors.forEach((factor) => {
    if (!isMicroScope(factor.scope)) return;
    const plotDate = resolvePlotDate(factor);
    if (!plotDate) return;

    const value = toNumeric(factor.weighted_mean);
    if (value === null) return;

    const name = (factor.factor && factor.factor.trim()) || fallbackName;
    const series = groups.get(name) ?? { id: name, name, data: [] };

    series.data.push({
      time: plotDate,
      value,
      label: formatInterval(factor),
      meta: factor
    });
    groups.set(name, series);
  });

  return Array.from(groups.values()).map((entry) => ({
    ...entry,
    data: sortByTimeAsc(entry.data)
  }));
}

export type OverlayDataPoint = {
  time: string;
  value: number;
  variance?: number;
  label: string;
  factor: string;
  scope: string;
};

export type OverlayData = {
  micro: OverlayDataPoint[];
  macro: OverlayDataPoint[];
};

export function buildOverlayData(factors: OilFactorRecord[]): OverlayData {
  const micro: OverlayDataPoint[] = [];
  const macro: OverlayDataPoint[] = [];

  factors.forEach((factor) => {
    const plotDate = resolvePlotDate(factor);
    if (!plotDate) return;

    const meanRaw = toNumeric(factor.weighted_mean);
    if (meanRaw === null) return;

    const varianceRaw = toNumeric(factor.weighted_variance);
    const scaledMean = meanRaw * 100;
    const scaledVariance = varianceRaw !== null ? varianceRaw * 100 * 100 : undefined;

    const entry: OverlayDataPoint = {
      time: plotDate,
      value: scaledMean,
      variance: scaledVariance,
      label: formatInterval(factor),
      factor: factor.factor ?? "",
      scope: factor.scope ?? "unknown"
    };

    if (isMicroScope(factor.scope)) {
      micro.push(entry);
    } else if (isMacroScope(factor.scope)) {
      macro.push(entry);
    }
  });

  return {
    micro: sortByTimeAsc(micro),
    macro: sortByTimeAsc(macro)
  };
}
