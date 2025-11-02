"use client";

import { ExternalLink } from "lucide-react";
import { useIntl } from "@/lib/i18n/IntlContext";

type CitationsListProps = {
  items: string[];
  heading?: string;
};

export function CitationsList({ items, heading }: CitationsListProps) {
  const { t } = useIntl();

  if (!items.length) {
    return (
      <div className="rounded-lg border border-border-secondary bg-background-tertiary/40 px-4 py-3 text-xs text-text-tertiary">
        {t("citations.empty")}
      </div>
    );
  }

  const effectiveHeading = heading ?? t("chain.citationsHeading");

  return (
    <div className="space-y-3">
      {effectiveHeading ? (
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-text-tertiary">
          {effectiveHeading}
        </p>
      ) : null}
      <ul className="flex flex-col gap-2">
        {items.map((url) => {
          const { host, displayUrl } = parseUrl(url);
          return (
            <li
              key={url}
              className="group flex items-center justify-between gap-3 rounded-lg border border-border-secondary bg-background-tertiary/60 px-3 py-2 transition hover:border-border-primary hover:bg-background-tertiary"
            >
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-text-primary">{host}</p>
                <p className="truncate text-[11px] text-text-tertiary">{displayUrl}</p>
              </div>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 rounded border border-border-secondary px-2 py-1 text-[11px] text-text-secondary transition group-hover:border-border-primary group-hover:text-text-primary"
              >
                <span>{t("citations.open")}</span>
                <ExternalLink size={12} aria-hidden />
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function parseUrl(raw: string): { host: string; displayUrl: string } {
  try {
    const url = new URL(raw.startsWith("http") ? raw : `https://${raw}`);
    const host = url.hostname.replace(/^www\./, "");
    const path = url.pathname === "/" ? "" : url.pathname;
    return { host, displayUrl: `${host}${path}` };
  } catch {
    return { host: raw, displayUrl: raw };
  }
}
