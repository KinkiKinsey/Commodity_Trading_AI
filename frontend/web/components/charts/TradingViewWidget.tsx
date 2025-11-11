"use client";

import { memo, useEffect, useRef } from "react";

interface TradingViewWidgetProps {
  symbol?: string;
  locale?: string;
  watchlist?: string[];
  compareSymbols?: Array<{ symbol: string; position?: string }>;
  studies?: string[];
  studiesOverrides?: Record<string, any>;
  autosize?: boolean;
}

function TradingViewWidget(_props: TradingViewWidgetProps) {
  // 忽略所有传入的 props，使用硬编码配置
  const container = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!container.current) return;

    // 清空容器
    container.current.innerHTML = "";

    // 创建 widget 容器
    const widgetContainer = document.createElement("div");
    widgetContainer.className = "tradingview-widget-container__widget";
    widgetContainer.style.height = "100%";
    widgetContainer.style.width = "100%";
    container.current.appendChild(widgetContainer);

    // 创建并添加脚本
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      allow_symbol_change: true,
      calendar: false,
      details: false,
      hide_side_toolbar: true,
      hide_top_toolbar: false,
      hide_legend: false,
      hide_volume: false,
      hotlist: false,
      interval: "D",
      locale: "zh_CN",
      save_image: true,
      style: "1",
      symbol: "TVC:USOIL",
      theme: "light",
      timezone: "Etc/UTC",
      backgroundColor: "#ffffff",
      gridColor: "rgba(46, 46, 46, 0.06)",
      watchlist: [],
      withdateranges: false,
      compareSymbols: [],
      studies: [
        "STD;Bollinger_Bands",
        "STD;MACD",
        "STD;Divergence%1Indicator",
        "STD;Gaps",
        "STD;Linear_Regression"
      ],
      autosize: true
    });
    container.current.appendChild(script);
  }, []);

  return (
    <div className="tradingview-widget-container" ref={container} style={{ height: "100%", width: "100%" }}></div>
  );
}

export default memo(TradingViewWidget);
