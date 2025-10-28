"use client";

import { ChangeEvent } from "react";
import clsx from "clsx";
import { Search, X } from "lucide-react";

type SearchInputProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  ariaLabel?: string;
};

export function SearchInput({ value, onChange, placeholder, className, ariaLabel }: SearchInputProps) {
  const handleInput = (event: ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
  };

  return (
    <div className={clsx("relative flex min-w-[200px] flex-1 items-center", className)}>
      <Search size={16} className="pointer-events-none absolute left-3 text-text-tertiary" aria-hidden />
      <input
        type="search"
        value={value}
        onChange={handleInput}
        placeholder={placeholder}
        aria-label={ariaLabel ?? placeholder}
        className="w-full rounded-full border border-border-muted bg-white pl-9 pr-10 py-2 text-sm text-text-primary outline-none transition focus:border-border-active focus:ring-0"
      />
      {value ? (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute right-2 inline-flex h-6 w-6 items-center justify-center rounded-full border border-border-muted bg-bg-alt text-text-secondary transition hover:border-border-active hover:text-text-primary"
          aria-label="清除搜索"
        >
          <X size={14} aria-hidden />
        </button>
      ) : null}
    </div>
  );
}

