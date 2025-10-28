"use client";

import clsx from "clsx";
import { SearchInput } from "@/components/common/SearchInput";

type DirectionValue = "all" | "bullish" | "bearish" | "neutral";
type TimeRangeValue = "1h" | "6h" | "24h" | "all";

type SymbolOption = {
  label: string;
  value: string;
};

type TimeOption = {
  label: string;
  value: TimeRangeValue;
};

type FilterBarProps = {
  symbolOptions: readonly SymbolOption[];
  selectedSymbol: string;
  onSelectSymbol: (value: string) => void;
  directionFilter: DirectionValue;
  onDirectionFilterChange: (value: DirectionValue) => void;
  directionLabels: Record<DirectionValue, string>;
  timeRange: TimeRangeValue;
  onTimeRangeChange: (value: TimeRangeValue) => void;
  timeOptions: readonly TimeOption[];
  searchTerm: string;
  onSearchTermChange: (value: string) => void;
  searchPlaceholder: string;
  locale: "zh-CN" | "en-US";
};

export function FilterBar({
  symbolOptions,
  selectedSymbol,
  onSelectSymbol,
  directionFilter,
  onDirectionFilterChange,
  directionLabels,
  timeRange,
  onTimeRangeChange,
  timeOptions,
  searchTerm,
  onSearchTermChange,
  searchPlaceholder,
  locale
}: FilterBarProps) {
  return (
    <div className="flex w-full flex-wrap items-center gap-3">
      <select
        value={selectedSymbol}
        onChange={(event) => onSelectSymbol(event.target.value)}
        className="rounded-full border border-border-muted bg-white px-4 py-2 text-sm font-medium text-text-primary transition hover:border-border-active"
      >
        {symbolOptions.map((option) => (
          <option key={option.value} value={option.value} className="bg-bg-panel text-text-primary">
            {option.label}
          </option>
        ))}
      </select>

      <SegmentedControl
        values={["all", "bullish", "bearish", "neutral"]}
        active={directionFilter}
        onChange={(value) => onDirectionFilterChange(value as DirectionValue)}
        renderLabel={(value) => directionLabels[value as DirectionValue]}
      />

      <SegmentedControl
        values={timeOptions.map((option) => option.value)}
        active={timeRange}
        onChange={(value) => onTimeRangeChange(value as TimeRangeValue)}
        renderLabel={(value) => timeOptions.find((option) => option.value === value)?.label ?? value}
      />

      <SearchInput
        value={searchTerm}
        onChange={onSearchTermChange}
        placeholder={searchPlaceholder}
        ariaLabel={locale === "zh-CN" ? "搜索新闻关键词" : "Search news keywords"}
        className="min-w-[220px]"
      />
    </div>
  );
}

type SegmentedControlProps<T extends string> = {
  values: readonly T[];
  active: string;
  onChange: (value: T) => void;
  renderLabel: (value: T) => string;
};

function SegmentedControl<T extends string>({ values, active, onChange, renderLabel }: SegmentedControlProps<T>) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {values.map((value) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(value)}
          className={clsx(
            "rounded-full border px-3 py-1 transition-colors",
            active === value
              ? "border-border-active bg-border-active text-bg-base"
              : "border-border-muted text-text-secondary hover:border-border-active/60"
          )}
        >
          {renderLabel(value)}
        </button>
      ))}
    </div>
  );
}

