import type { NewsStreamEvent } from "@/lib/state/newsStreamStore";
import type { IndexSignal } from "@/lib/state/indexSignalsStore";

const headline = "美国总统军事施压委内瑞拉 美国议员强调战争须经国会授权";
const summary =
  "美国对委内瑞拉实施军事压力并强调国会授权程序，油市风险溢价升温。AI 推理链展示了地缘政治升级如何推高原油价格风险。";
const chainText = [
  "2025 年 10 月 15 日，总统特朗普讨论对委内瑞拉进行军事打击，标志着美国在该地区行动升级。五角大楼部署海军特遣队并摧毁多艘运毒船只。(来源: Argus)",
  "美国政府已将行动告知国会，称其为\"非国际武装冲突\"，但尚无更广泛军事行动授权。目前美军规模不足以进行全面入侵，但 3,500 名海军陆战队和 3,400 名海军人员正在提升紧张局势。(来源: Argus)",
  "随着 B-52 轰炸机和 CIA 打击与马杜罗相关贩毒网络，危机继续升温。马杜罗号召大量预备役，称美国意在夺取委内瑞拉油气资产。(来源: CNN)",
  "目前未发现委内瑞拉原油出口中断的明确迹象，但可信的军事威胁提升了供应中断风险，市场倾向将其计入地缘风险溢价。",
  "多方来源（Argus、CNN）显示形势高度紧张，美国军事态势强硬，委内瑞拉动员力量抗衡并围绕油气资源展开言论。",
  "虽然目前仍未演变成全面战争，但持续升级的不确定性支撑了对原油的看涨立场。",
  "委内瑞拉仍是重要（虽已削弱）的原油出口国，任何立即风险都可能导致全球供应扰动，构成明显的看涨信号。"
];

export function buildSampleNewsEvent(): NewsStreamEvent {
  const eventId = `demo-venezuela-${Date.now()}`;
  return {
    eventId,
    timestamp: new Date().toISOString(),
    headline,
    summary,
    direction: "bullish",
    confidence: 0.9,
    language: "zh-CN",
    chain_of_thought: chainText.map((text, index) => ({
      id: `step-${index}`,
      step: index,
      text
    })),
    citations: [
      "https://www.argusmedia.com/es/news-and-insights/latest-market-news/2742717-trump-discusses-venezuela-land-strikes",
      "https://www.cnn.com/2025/10/18/politics/trump-maduro-tensions-venezuela-military"
    ],
    signalTags: ["OPEC 风险", "军事升级"],
    complianceStatus: "clean",
    signal: {
      signalId: `sig-${eventId}`,
      signalType: "buy",
      price: 88.45,
      indexValue: 5123.7,
      reasonTag: "地缘风险溢价",
      newsId: eventId,
      createdAt: new Date().toISOString()
    }
  };
}

export function buildSampleSignals(eventId: string): IndexSignal[] {
  const baseTime = Date.now();
  return [
    {
      signalId: `sig-${baseTime}`,
      signalType: "buy",
      price: 88.45,
      createdAt: new Date(baseTime - 10 * 60 * 1000).toISOString(),
      reasonTag: "地缘风险溢价",
      newsId: eventId
    },
    {
      signalId: `sig-${baseTime}-2`,
      signalType: "sell",
      price: 85.2,
      createdAt: new Date(baseTime - 60 * 60 * 1000).toISOString(),
      reasonTag: "短线获利了结",
      newsId: eventId
    }
  ];
}


