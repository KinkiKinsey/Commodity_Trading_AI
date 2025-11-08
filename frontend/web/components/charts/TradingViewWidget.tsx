"use client";

import { memo, useEffect, useRef } from "react";

const SCRIPT_SRC = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";

type TradingViewWidgetProps = {
  symbol?: string;
  locale?: string;
  interval?: string;
  range?: string;
  theme?: "light" | "dark";
};

export const TradingViewWidget = memo(function TradingViewWidget({
  symbol = "NYMEX:CL1!",
  locale = "en",
  interval = "60",
  range = "YTD",
  theme = "light",
}: TradingViewWidgetProps) {
  const container = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = SCRIPT_SRC;
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = `
      {
        "allow_symbol_change": true,
        "calendar": false,
        "details": true,
        "hide_side_toolbar": false,
        "hide_top_toolbar": false,
        "hide_legend": false,
        "hide_volume": false,
        "hotlist": true,
        "interval": "${interval}",
        "locale": "${locale}",
        "save_image": true,
        "style": "1",
        "symbol": "${symbol}",
        "theme": "${theme}",
        "timezone": "Etc/UTC",
        "backgroundColor": "#ffffff",
        "gridColor": "rgba(46, 46, 46, 0.06)",
        "watchlist": ["CME_MINI:NQ1!"],
        "withdateranges": true,
        "range": "${range}",
        "compareSymbols": [{ "symbol": "COMEX:GC1!", "position": "SameScale" }],
        "studies": [
          "STD;Bollinger_Bands",
          "STD;MACD",
          "STD;Divergence%1Indicator",
          "STD;Gaps",
          "STD;Linear_Regression"
        ],
        "autosize": true
      }`;
    if (container.current) {
      container.current.innerHTML = "";
      container.current.appendChild(script);
    }
    return () => {
      if (container.current) {
        container.current.innerHTML = "";
      }
    };
  }, [symbol, locale, interval, range, theme]);

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
