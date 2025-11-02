"use client";

import { ChangeEvent, FormEvent } from "react";
import clsx from "clsx";
import { Loader2, Search, X } from "lucide-react";
import { useIntl } from "@/lib/i18n/IntlContext";

const MAX_LENGTH = 8000;

type SearchInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: (value: string) => void | Promise<void>;
  placeholder?: string;
  className?: string;
  ariaLabel?: string;
  isLoading?: boolean;
};

export function SearchInput({
  value,
  onChange,
  onSubmit,
  placeholder,
  className,
  ariaLabel,
  isLoading = false
}: SearchInputProps) {
  const { t } = useIntl();

  const handleInput = (event: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(event.target.value);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || !onSubmit) return;
    void onSubmit(trimmed);
  };

  const handleClear = () => {
    if (isLoading) return;
    onChange("");
  };

  const charCount = value.length;
  const remaining = Math.max(MAX_LENGTH - charCount, 0);

  return (
    <form onSubmit={handleSubmit} className={clsx("relative flex w-full", className)}>
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-3xl opacity-90"
        style={{
          background: "linear-gradient(120deg, #60a5fa, #a855f7, #f97316, #22d3ee, #60a5fa)",
          backgroundSize: "300% 300%",
          animation: "gradientGlow 6s ease-in-out infinite",
          filter: "blur(0.75px) drop-shadow(0 0 14px rgba(99,102,241,0.35))",
          pointerEvents: "none"
        }}
      />
      <div className="relative z-10 flex w-full flex-col gap-3 rounded-3xl bg-white/95 px-5 py-4 text-base shadow-[0_20px_55px_rgba(15,23,42,0.12)] backdrop-blur">
        <div className="flex items-center justify-between gap-2">
          <button
            type="submit"
            disabled={isLoading}
            className={clsx(
              "inline-flex items-center gap-2 rounded-full border border-border-muted/70 bg-transparent px-3 py-1.5 text-sm text-text-secondary transition hover:border-border-active hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-active focus-visible:ring-offset-2 focus-visible:ring-offset-white",
              isLoading && "cursor-not-allowed opacity-70 hover:text-text-secondary"
            )}
            aria-label={ariaLabel ?? t("search.submit")}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Search size={16} aria-hidden />}
            <span>{t("search.submit")}</span>
          </button>
          {value ? (
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading}
              className={clsx(
                "inline-flex h-8 w-8 items-center justify-center rounded-full border border-border-muted/70 bg-bg-alt text-text-secondary transition hover:border-border-active hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-active focus-visible:ring-offset-2 focus-visible:ring-offset-white",
                isLoading && "cursor-not-allowed opacity-60 hover:text-text-secondary"
              )}
              aria-label={t("search.clear")}
            >
              <X size={14} aria-hidden />
            </button>
          ) : null}
        </div>

        <textarea
          value={value}
          onChange={handleInput}
          placeholder={placeholder}
          aria-label={ariaLabel ?? placeholder}
          disabled={isLoading}
          maxLength={MAX_LENGTH}
          rows={6}
          className={clsx(
            "min-h-[160px] w-full resize-vertical rounded-2xl border border-border-muted/40 bg-white/90 px-4 py-3 text-base text-text-primary outline-none transition placeholder:text-text-tertiary/60 focus:border-border-active focus:ring-0 disabled:cursor-not-allowed disabled:opacity-70"
          )}
        />

        <div className="flex items-center justify-between text-[11px] text-text-tertiary">
          <span>{t("search.helper")}</span>
          <span className={clsx(remaining === 0 && "text-market-negative")}>
            {charCount}/{MAX_LENGTH}
          </span>
        </div>
      </div>
    </form>
  );
}
