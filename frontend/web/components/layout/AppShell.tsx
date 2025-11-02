import type { ReactNode } from "react";
import clsx from "clsx";
import { MarketTicker } from "./MarketTicker";
import { useIntl, type TranslationKey } from "@/lib/i18n/IntlContext";

const PRIMARY_NAV_KEYS = [
  "appShell.nav.market",
  "appShell.nav.economy",
  "appShell.nav.industry",
  "appShell.nav.tech",
  "appShell.nav.politics",
  "appShell.nav.business",
  "appShell.nav.commentary"
] as const satisfies TranslationKey[];

const SECONDARY_NAV_KEYS = ["appShell.nav.more"] as const satisfies TranslationKey[];

type AppShellProps = {
  mainColumn: ReactNode;
  leftColumn?: ReactNode;
  rightColumn?: ReactNode;
  bottomSlot?: ReactNode;
};

export function AppShell({ mainColumn, leftColumn, rightColumn, bottomSlot }: AppShellProps) {
  const { t } = useIntl();
  return (
    <div className="flex min-h-screen flex-col bg-bg-base text-text-primary">
      <Header />
      <div className="flex flex-1 flex-col">
        <div className="mx-auto flex w-full max-w-[1440px] flex-1 flex-col gap-6 px-4 py-8 lg:px-8">
          <div className="grid gap-5 xl:grid-cols-[200px_minmax(0,1fr)_380px]">
            <aside className={clsx("hidden flex-col gap-6 xl:flex")}>
              {leftColumn ?? (
                <PlaceholderCard
                  title={t("appShell.placeholder.market.title")}
                  description={t("appShell.placeholder.market.description")}
                />
              )}
            </aside>

            <section className="min-w-0 flex flex-col gap-6">{mainColumn}</section>

            <aside className={clsx("hidden flex-col gap-6 xl:flex")}>
              {rightColumn ?? (
                <PlaceholderCard
                  title={t("appShell.placeholder.insights.title")}
                  description={t("appShell.placeholder.insights.description")}
                />
              )}
            </aside>
          </div>

          <div className="flex flex-col gap-6 xl:hidden">
            {leftColumn ? <div className="flex flex-col gap-6">{leftColumn}</div> : null}
            {rightColumn ? <div className="flex flex-col gap-6">{rightColumn}</div> : null}
          </div>
        </div>
      </div>
      <footer className="border-t border-border-muted bg-bg-alt">
        {bottomSlot ?? <TickerPlaceholder />}
      </footer>
    </div>
  );
}

function Header() {
  const { t } = useIntl();
  return (
    <header className="border-b border-border-muted bg-black text-white">
      <div className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-4 px-4 py-4 lg:px-8">
        <div className="flex items-center gap-8">
          <span className="text-xl font-semibold tracking-[0.2em]">Ringshell</span>
          <nav className="hidden items-center gap-4 text-sm uppercase tracking-[0.18em] text-white/70 lg:flex">
            {PRIMARY_NAV_KEYS.map((key) => (
              <a key={key} className="cursor-pointer transition hover:text-white">
                {t(key)}
              </a>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <nav className="hidden items-center gap-3 uppercase tracking-[0.18em] text-white/70 md:flex">
            {SECONDARY_NAV_KEYS.map((key) => (
              <a key={key} className="cursor-pointer transition hover:text-white">
                {t(key)}
              </a>
            ))}
          </nav>
          <button className="rounded-full border border-white/40 px-4 py-1 text-xs font-medium uppercase tracking-[0.18em] text-white transition hover:bg-white hover:text-black">
            {t("appShell.button.subscribe")}
          </button>
          <div className="flex items-center gap-2 rounded-full border border-white/30 px-3 py-1 text-xs uppercase tracking-[0.18em] text-white/80">
            <span>{t("appShell.button.login")}</span>
          </div>
          <button className="rounded-full border border-white/30 px-3 py-1 text-xs uppercase tracking-[0.18em] text-white/80 transition hover:border-white hover:text-white">
            {t("appShell.button.search")}
          </button>
        </div>
      </div>
      <MarketTicker />
    </header>
  );
}

function PlaceholderCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-border-muted bg-white p-5 text-sm text-text-secondary shadow-[0_4px_12px_rgba(15,23,42,0.08)]">
      <h3 className="text-xs font-semibold uppercase tracking-[0.25em] text-text-primary">{title}</h3>
      <p className="mt-3 leading-relaxed">{description}</p>
    </div>
  );
}

function TickerPlaceholder() {
  const { t } = useIntl();
  return (
    <div className="mx-auto flex w-full max-w-[1440px] items-center justify-between gap-4 px-4 py-4 text-xs text-text-secondary lg:px-8">
      <span className="uppercase tracking-[0.18em]">{t("appShell.ticker.placeholder.left")}</span>
      <span className="uppercase tracking-[0.18em] text-state-warning">{t("appShell.ticker.placeholder.right")}</span>
    </div>
  );
}
