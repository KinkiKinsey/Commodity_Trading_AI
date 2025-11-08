# -*- coding: utf-8 -*-
from pathlib import Path
path = Path("frontend/web/app/news/real-time/page.tsx")
text = path.read_text(encoding="utf-8")
old = '  const updateLabel = formattedTime\n\n    ? (isZh ? "??????? " + formattedTime : "As of " + formattedTime)\n\n    : null;\n\n\n\n  return ('
new = '  const updateLabel = formattedTime\n\n    ? (isZh ? "??????? " + formattedTime : "As of " + formattedTime)\n\n    : null;\n\n\n\n  const labels = {\n\n    latency: isZh ? "延迟" : "Latency",\n\n    exchange: isZh ? "交易所" : "Exchange",\n\n    currency: isZh ? "计价货币" : "Currency",\n\n    sentiment: isZh ? "情绪指示" : "Sentiment",\n\n    aiInsight: isZh ? "AI 结论" : "AI Insight",\n\n    confidence: isZh ? "置信度" : "Confidence"\n\n  };\n\n\n\n  const metaBadges: string[] = [];\n\n  if (metadata?.data_latency_seconds !== undefined) {\n\n    metaBadges.push(`${labels.latency} · ${metadata.data_latency_seconds}s`);\n\n  }\n\n  if (source?.exchange) {\n\n    metaBadges.push(`${labels.exchange} · ${source.exchange}`);\n\n  }\n\n  if (source?.currency) {\n\n    metaBadges.push(`${labels.currency} · ${source.currency}`);\n\n  }\n\n\n\n  const sentimentMap = isZh\n\n    ? { bullish: "看多", bearish: "看空", neutral: "中性" }\n\n    : { bullish: "Bullish", bearish: "Bearish", neutral: "Neutral" };\n\n\n\n  const sentimentText = sentimentDirection ? sentimentMap[sentimentDirection] : null;\n\n  const sentimentTone =\n\n    sentimentDirection === "bullish"\n\n      ? "text-accent-bull"\n\n      : sentimentDirection === "bearish"\n\n        ? "text-accent-bear"\n\n        : "text-text-primary";\n\n\n\n  const confidencePercent = Math.round(\n\n    Math.max(0, Math.min(1, sentimentConfidence ?? 0.5)) * 100\n\n  );\n\n\n\n  return ('
if old not in text:
    raise SystemExit("target block not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
