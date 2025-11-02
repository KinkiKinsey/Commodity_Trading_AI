"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

export type Locale = "zh-CN" | "en-US";

type IntlValue = {
  locale: Locale;
  setLocale: (value: Locale) => void;
  t: (key: TranslationKey) => string;
};

const zhCN = {
  "header.liveFeed": "实时数据流",
  "header.title": "AI 实时新闻板",
  "status.connecting": "正在连接实时数据…",
  "status.connected": "实时连接正常",
  "status.error": "连接异常，正在重试…",
  "status.lastEventPrefix": "最近事件",
  "status.retryHint": "系统将自动重试，请检查网络或刷新页面。",
  "banner.error": "连接异常，正在重试…",
  "banner.stale": "数据超过 2 分钟未更新，建议刷新保持同步。",
  "button.manualRefresh": "手动刷新",
  "button.refreshData": "刷新数据",
  "button.close": "关闭",
  "button.viewChain": "查看推理链",
  "filters.direction": "方向",
  "filters.time": "时间范围",
  "filters.searchPlaceholder": "请输入至少 20 字的新闻内容，生成 AI 推理链",
  "panel.signals": "指数信号",
  "panel.latest": "最新资讯",
  "panel.entries": "条",
  "empty.news": "暂无符合筛选条件的新闻，等待实时更新。",
  "empty.signals": "暂无信号，等待实时推送。",
  "signals.error": "信号加载失败",
  "signals.loading": "正在加载信号…",
  "signals.truncated": "已显示最近 8 条信号，共 {count} 条",
  "comingSoon.title": "即将上线",
  "comingSoon.signalLegend": "信号图例与市场上下文",
  "comingSoon.hypothesis": "用户假设输入流",
  "comingSoon.indicators": "更多指标：成交量、技术形态",
  "modal.summaryFallback": "该新闻支持 AI 推理，请打开面板查看完整链路。",
  "modal.noSummary": "暂时没有摘要，可查看下方推理链了解详情。",
  "modal.chainTitle": "AI 推理链",
  "modal.generateChain": "生成 AI 推理链",
  "modal.generateChainHint": "当前新闻尚未生成推理链，点击按钮即可创建。",
  "modal.citationsHeading": "相关新闻引用",
  "modal.compliance.blocked": "因合规限制，本推理链部分内容被隐藏。",
  "modal.compliance.masked": "部分内容依据合规要求做了脱敏处理。",
  "modal.noChain": "当前新闻尚未提供推理链路。",
  "modal.linkLabel": "链接",
  "modal.confidenceLabel": "置信度",
  "chain.generatedAt": "生成时间",
  "chain.closeAria": "关闭推理抽屉",
  "chain.relatedLink": "相关链接",
  "chain.citationsHeading": "引用来源",
  "citations.empty": "暂无可引用的来源",
  "citations.open": "打开",
  "search.submit": "生成推理链",
  "search.helper": "粘贴新闻内容，点击按钮生成 AI 推理链。",
  "search.clear": "清除搜索",
  "appShell.nav.market": "市场",
  "appShell.nav.economy": "经济",
  "appShell.nav.industry": "行业",
  "appShell.nav.tech": "科技",
  "appShell.nav.politics": "政治",
  "appShell.nav.business": "商业周刊",
  "appShell.nav.commentary": "评论",
  "appShell.nav.more": "更多",
  "appShell.button.subscribe": "订阅",
  "appShell.button.login": "登录",
  "appShell.button.search": "搜索",
  "appShell.placeholder.market.title": "市场侧栏",
  "appShell.placeholder.market.description": "待填充：行情速览、关注列表等",
  "appShell.placeholder.insights.title": "洞察侧栏",
  "appShell.placeholder.insights.description": "待填充：情绪仪表、洞察模块等",
  "appShell.ticker.placeholder.left": "行情条占位",
  "appShell.ticker.placeholder.right": "SSE 状态流",
  "marketTicker.category.top": "精选证券",
  "marketTicker.category.indices": "市场指数",
  "marketTicker.category.rates": "利率与债券",
  "marketTicker.arrow.up": "▲",
  "marketTicker.arrow.down": "▼",
  "marketTicker.arrow.flat": "→",
  "chart.status.loading": "加载行情数据…",
  "chart.status.empty": "暂无价格数据",
  "sentiment.heading": "情绪指示",
  "sentiment.meta": "AI 结论",
  "sentiment.confidence": "置信度",
  "sentiment.direction.bullish": "看多",
  "sentiment.direction.bearish": "看空",
  "sentiment.direction.neutral": "中性",
  "home.title": "RingShell 控制台",
  "home.description": "请选择左侧导航进入 AI 实时新闻、价格预测或多因子仪表盘模块。",
  "news.latestTitle": "最新资讯",
  "news.signalLabel": "信号",
  "news.localeToggle.en": "EN",
  "news.localeToggle.zh": "中文"
} as const;

export type TranslationKey = keyof typeof zhCN;

const enUS: { [K in TranslationKey]: string } = {
  "header.liveFeed": "Live Feed",
  "header.title": "AI Real-Time News Board",
  "status.connecting": "Connecting to live feed…",
  "status.connected": "Live connection stable",
  "status.error": "Connection error, retrying…",
  "status.lastEventPrefix": "Last event",
  "status.retryHint": "The system will retry automatically. Check your network or refresh.",
  "banner.error": "Connection error, retrying…",
  "banner.stale": "No updates for over 2 minutes. Refresh to stay synced.",
  "button.manualRefresh": "Manual Refresh",
  "button.refreshData": "Refresh Data",
  "button.close": "Close",
  "button.viewChain": "View reasoning chain",
  "filters.direction": "Direction",
  "filters.time": "Time Range",
  "filters.searchPlaceholder": "Paste news content (20+ chars) to generate the AI reasoning chain",
  "panel.signals": "Index Signals",
  "panel.latest": "Latest Stories",
  "panel.entries": "entries",
  "empty.news": "No news matches current filters; waiting for live updates.",
  "empty.signals": "No signals yet, awaiting live push.",
  "signals.error": "Signal load failed",
  "signals.loading": "Loading signals…",
  "signals.truncated": "Showing latest 8 of {count} signals",
  "comingSoon.title": "Coming Soon",
  "comingSoon.signalLegend": "Signal legend and market context callouts",
  "comingSoon.hypothesis": "User hypothesis input stream",
  "comingSoon.indicators": "Additional indicators: volume, technical overlays",
  "modal.summaryFallback": "This news supports AI reasoning; open the panel to review the full chain.",
  "modal.noSummary": "No summary yet. Review the reasoning chain below for details.",
  "modal.chainTitle": "AI Reasoning Chain",
  "modal.generateChain": "Generate AI reasoning chain",
  "modal.generateChainHint": "No reasoning yet. Click the button to generate one.",
  "modal.citationsHeading": "Related References",
  "modal.compliance.blocked": "Some steps are hidden for compliance reasons.",
  "modal.compliance.masked": "Portions have been redacted to meet compliance requirements.",
  "modal.noChain": "This story has not provided a reasoning chain yet.",
  "modal.linkLabel": "Link",
  "modal.confidenceLabel": "Confidence",
  "chain.generatedAt": "Generated",
  "chain.closeAria": "Close reasoning drawer",
  "chain.relatedLink": "Related link",
  "chain.citationsHeading": "Citations",
  "citations.empty": "No citations available",
  "citations.open": "Open",
  "search.submit": "Analyze",
  "search.helper": "Paste any news content and let the AI build the reasoning chain.",
  "search.clear": "Clear search",
  "appShell.nav.market": "Markets",
  "appShell.nav.economy": "Economy",
  "appShell.nav.industry": "Industry",
  "appShell.nav.tech": "Technology",
  "appShell.nav.politics": "Politics",
  "appShell.nav.business": "Businessweek",
  "appShell.nav.commentary": "Opinion",
  "appShell.nav.more": "More",
  "appShell.button.subscribe": "Subscribe",
  "appShell.button.login": "Sign In",
  "appShell.button.search": "Search",
  "appShell.placeholder.market.title": "Market Column",
  "appShell.placeholder.market.description": "Placeholder: market snapshot, watchlist, and more.",
  "appShell.placeholder.insights.title": "Insights Column",
  "appShell.placeholder.insights.description": "Placeholder: sentiment gauges and analytical modules.",
  "appShell.ticker.placeholder.left": "Markets ticker placeholder",
  "appShell.ticker.placeholder.right": "SSE streaming status",
  "marketTicker.category.top": "Featured Securities",
  "marketTicker.category.indices": "Market Indices",
  "marketTicker.category.rates": "Rates & Bonds",
  "marketTicker.arrow.up": "▲",
  "marketTicker.arrow.down": "▼",
  "marketTicker.arrow.flat": "→",
  "chart.status.loading": "Loading price data…",
  "chart.status.empty": "No pricing data yet",
  "sentiment.heading": "Sentiment",
  "sentiment.meta": "AI Insight",
  "sentiment.confidence": "Confidence",
  "sentiment.direction.bullish": "Bullish",
  "sentiment.direction.bearish": "Bearish",
  "sentiment.direction.neutral": "Neutral",
  "home.title": "RingShell Console",
  "home.description": "Use the left navigation to open AI live news, price forecasts, or the multi-factor dashboard.",
  "news.latestTitle": "Latest Updates",
  "news.signalLabel": "Signal",
  "news.localeToggle.en": "EN",
  "news.localeToggle.zh": "中文"
};

const translations: Record<Locale, typeof zhCN> = {
  "zh-CN": zhCN,
  "en-US": enUS
};

const IntlContext = createContext<IntlValue | null>(null);

export function IntlProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("zh-CN");

  const value = useMemo<IntlValue>(
    () => ({
      locale,
      setLocale,
      t: (key) => translations[locale][key] ?? key
    }),
    [locale]
  );

  return <IntlContext.Provider value={value}>{children}</IntlContext.Provider>;
}

export function useIntl() {
  const ctx = useContext(IntlContext);
  if (!ctx) {
    throw new Error("useIntl must be used within IntlProvider");
  }
  return ctx;
}
