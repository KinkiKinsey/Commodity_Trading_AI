"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

type Locale = "zh-CN" | "en-US";

type IntlValue = {
  locale: Locale;
  setLocale: (value: Locale) => void;
  t: (key: string) => string;
};

const translations: Record<Locale, Record<string, string>> = {
  "zh-CN": {
    "header.liveFeed": "实时数据流",
    "header.title": "AI 实时新闻板",
    "status.connecting": "正在连接实时数据…",
    "status.connected": "实时连接正常",
    "status.error": "连接异常，正在重试…",
    "banner.error": "连接异常，正在重试…",
    "banner.stale": "数据超过 2 分钟未更新，可能已失去实时性。",
    "button.manualRefresh": "手动刷新",
    "button.refreshData": "刷新数据",
    "filters.direction": "方向",
    "filters.time": "时间范围",
    "filters.searchPlaceholder": "搜索标题、摘要或推理关键词",
    "panel.signals": "指数信号",
    "panel.latest": "最新资讯",
    "panel.entries": "条目",
    "empty.news": "暂无符合筛选条件的新闻，等待实时流更新。",
    "empty.signals": "暂无信号，等待实时推送。",
    "signals.error": "信号加载失败",
    "signals.loading": "正在加载信号…",
    "comingSoon.title": "即将上线",
    "comingSoon.signalLegend": "信号图例与市场背景说明",
    "comingSoon.hypothesis": "用户假设推理输入流",
    "comingSoon.indicators": "更多指标：成交量、技术叠加",
    "modal.summaryFallback": "该新闻支持 AI 推理，可在弹窗查看完整链条。"
  },
  "en-US": {
    "header.liveFeed": "Live Feed",
    "header.title": "AI Real-Time News Board",
    "status.connecting": "Connecting to live feed…",
    "status.connected": "Live connection stable",
    "status.error": "Connection error, retrying…",
    "banner.error": "Connection error, retrying…",
    "banner.stale": "No updates for over 2 minutes. Refresh to stay synced.",
    "button.manualRefresh": "Manual Refresh",
    "button.refreshData": "Refresh Data",
    "filters.direction": "Direction",
    "filters.time": "Time Range",
    "filters.searchPlaceholder": "Search headline, summary, or reasoning keywords",
    "panel.signals": "Index Signals",
    "panel.latest": "Latest Stories",
    "panel.entries": "entries",
    "empty.news": "No news matches current filters; waiting for live updates.",
    "empty.signals": "No signals yet, awaiting live push.",
    "signals.error": "Signal load failed",
    "signals.loading": "Loading signals…",
    "comingSoon.title": "Coming Soon",
    "comingSoon.signalLegend": "Signal legend and market context callouts",
    "comingSoon.hypothesis": "User hypothesis input stream",
    "comingSoon.indicators": "Additional indicators: volume, technical overlays",
    "modal.summaryFallback": "This news supports AI reasoning; open the modal to review the full chain."
  }
};

const IntlContext = createContext<IntlValue | null>(null);

export function IntlProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("zh-CN");

  const value = useMemo<IntlValue>(() => {
    return {
      locale,
      setLocale,
      t: (key: string) => translations[locale][key] ?? key
    };
  }, [locale]);

  return <IntlContext.Provider value={value}>{children}</IntlContext.Provider>;
}

export function useIntl() {
  const ctx = useContext(IntlContext);
  if (!ctx) {
    throw new Error("useIntl must be used within IntlProvider");
  }
  return ctx;
}
