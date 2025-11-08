"use client";

import { memo, useEffect, useRef } from "react";

const SCRIPT_SRC = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";

type CompareSymbol = {
  symbol: string;
  position: "SameScale" | "SeparateChart";
};

type TradingViewWidgetProps = {
  symbol?: string;
  locale?: string;
  interval?: string;
  range?: string;
  theme?: "light" | "dark";
  watchlist?: string[];
  compareSymbols?: CompareSymbol[];
  studies?: string[];
  studiesOverrides?: Record<string, string | number | boolean>;
  autosize?: boolean;
};

export const TradingViewWidget = memo(function TradingViewWidget({
  symbol = "NYMEX:CL1!",
  locale = "en",
  interval = "60",
  range = "YTD",
  theme = "light",
  watchlist = ["CME_MINI:NQ1!"],
  compareSymbols = [{ symbol: "COMEX:GC1!", position: "SameScale" }],
  studies = ["STD;Bollinger_Bands", "STD;MACD", "STD;Divergence%1Indicator", "STD;Gaps", "STD;Linear_Regression"],
  studiesOverrides,
  autosize = true
}: TradingViewWidgetProps) {
  const container = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const currentContainer = container.current;
    if (!currentContainer) {
      return;
    }

    const script = document.createElement("script");
    script.src = SCRIPT_SRC;
    script.type = "text/javascript";
    script.async = true;
    const config: Record<string, unknown> = {
      allow_symbol_change: true,
      calendar: false,
      details: true,
      hide_side_toolbar: false,
      hide_top_toolbar: false,
      hide_legend: false,
      hide_volume: false,
      hotlist: true,
      interval,
      locale,
      save_image: true,
      style: "1",
      symbol,
      theme,
      timezone: "Etc/UTC",
      backgroundColor: "#ffffff",
      gridColor: "rgba(46, 46, 46, 0.06)",
      watchlist,
      withdateranges: true,
      range,
      compareSymbols,
      studies,
      autosize
    };
    if (studiesOverrides) {
      config.studies_overrides = studiesOverrides;
    }
    script.innerHTML = JSON.stringify(config);

    currentContainer.innerHTML = "";
    currentContainer.appendChild(script);
    return () => {
      currentContainer.innerHTML = "";
    };
  }, [symbol, locale, interval, range, theme, watchlist, compareSymbols, studies, studiesOverrides, autosize]);

  return (
    <div className="tradingview-widget-container h-full w-full" ref={container} style={{ height: "100%", width: "100%" }}>
      <div className="tradingview-widget-container__widget" style={{ height: "calc(100% - 32px)", width: "100%" }} />
      <div className="tradingview-widgetopyright text-[10px]">
        <a href="https://www.tradingview.com/symbols/NYMEX-CL1!/" rel="noopener nofollow" target="_blank">
          <span className="blue-text">CL1! chart</span>
        </a>
        <span className="trademark"> by TradingView</span>
      </div>
    </div>
  );
});

export default TradingViewWidget;
