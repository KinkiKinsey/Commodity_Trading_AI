# `/api/news/stream` SSE 数据契约（阶段 3 输出草案）

> 版本：v0.1（待后端确认）  
> 目的：明确 AI 实时新闻板块所需的实时推送格式、示例与校验要求，指导后端实现及前端对接。

---

## 1. 事件基础格式

- **通道**：Server-Sent Events (`Content-Type: text/event-stream`)
- **心跳**：每 10 秒推送 `event: heartbeat`，`data: {"timestamp": "...", "status": "ok"}`。
- **数据事件**：`event: news` 携带单条新闻与信号信息。

### 1.1 JSON Schema

```jsonc
{
  "$id": "https://ringshell.ai/schemas/news-stream-event.json",
  "type": "object",
  "required": [
    "eventId",
    "timestamp",
    "headline",
    "direction",
    "confidence",
    "chainOfThought",
    "citations",
    "signalTags",
    "language",
    "complianceStatus"
  ],
  "properties": {
    "eventId": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "string", "format": "date-time" },
    "headline": { "type": "string", "maxLength": 200 },
    "summary": { "type": "string", "maxLength": 200 },
    "direction": { "enum": ["bullish", "bearish", "neutral"] },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "language": { "type": "string", "pattern": "^[a-z]{2}-[A-Z]{2}$" },
    "chainOfThought": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "step", "text"],
        "properties": {
          "id": { "type": "string" },
          "step": { "type": "integer", "minimum": 0 },
          "text": { "type": "string" },
          "evidence": { "type": "string" },
          "url": { "type": "string", "format": "uri" }
        }
      }
    },
    "citations": {
      "type": "array",
      "items": { "type": "string", "format": "uri" }
    },
    "signalTags": {
      "type": "array",
      "items": { "type": "string", "maxLength": 32 },
      "maxItems": 5
    },
    "complianceStatus": { "enum": ["clean", "masked", "blocked"] },
    "signal": {
      "type": "object",
      "required": ["signalId", "signalType", "price", "createdAt"],
      "properties": {
        "signalId": { "type": "string" },
        "signalType": { "enum": ["buy", "sell"] },
        "price": { "type": "number" },
        "indexValue": { "type": "number" },
        "reasonTag": { "type": "string" },
        "newsId": { "type": "string" },
        "createdAt": { "type": "string", "format": "date-time" }
      }
    }
  }
}
```

### 1.2 示例事件

```text
event: news
data: {
  "eventId": "5fe1942c-1201-4b0d-ae3c-6f2ec8ec45a8",
  "timestamp": "2025-10-20T21:00:11Z",
  "headline": "OPEC 产量增速不及预期，美原油盘中拉升",
  "summary": "本轮 OPEC 会议未能就超产国家执行方案达成一致，原油供给存在缺口。",
  "direction": "bullish",
  "confidence": 0.76,
  "language": "zh-CN",
  "chainOfThought": [
    {
      "id": "step-1",
      "step": 1,
      "text": "OPEC 官方声明显示 2025 Q1 产量增幅低于计划值 20 万桶/日。",
      "evidence": "OPEC 官方声明 PDF",
      "url": "https://www.opec.org/opec_web/en/press_room/1234.htm"
    },
    {
      "id": "step-2",
      "step": 2,
      "text": "EIA 数据显示美国商业原油库存连续三周下降。",
      "url": "https://www.eia.gov/petroleum/status"
    },
    {
      "id": "step-3",
      "step": 3,
      "text": "市场预期供给紧张，WTI 期货价格盘中涨幅 2.1%。"
    }
  ],
  "citations": [
    "https://www.reuters.com/markets/asia/oil-market",
    "https://www.bloomberg.com/oil-supply-2025"
  ],
  "signalTags": ["OPEC 不及预期", "库存下滑"],
  "complianceStatus": "clean",
  "signal": {
    "signalId": "sig-20251020-2100",
    "signalType": "buy",
    "price": 88.45,
    "indexValue": 5123.7,
    "reasonTag": "OPEC 不及预期",
    "newsId": "5fe1942c-1201-4b0d-ae3c-6f2ec8ec45a8",
    "createdAt": "2025-10-20T21:00:05Z"
  }
}
```

---

## 2. 错误与合规状态

| 状态 | 含义 | 前端处理 |
|------|------|----------|
| `clean` | 正常内容 | 正常展示 |
| `masked` | 已做敏感词脱敏 | 在 Modal 与 Drawer 顶部显示提示：“部分内容因合规要求已隐藏” |
| `blocked` | 内容不可展示 | Modal 显示“内容暂不可用”，禁用“查看推理”按钮，并记得记录埋点 |

若后端检测到严重合规问题，可推送 `event: compliance_alert`，前端以 Toast 显示并要求刷新。

---

## 3. 信号与新闻关联

- `signal.signalId` 与图表点位一一对应。
- `signal.newsId` 默认等于 `eventId`，用于 Modal 复用缓存。
- 后端需在推流前验证 `signal.newsId` 存在于缓存池；若不匹配则返回 `event: error`。

---

## 4. 心跳与重连策略

```text
event: heartbeat
data: {"timestamp":"2025-10-20T21:00:20Z","status":"ok"}
```

- 若前端 20 秒内未收到 heartbeat，应显示黄色提醒并尝试重连。
- 推荐的重连间隔：1s → 2s → 4s → 8s（最大 30s），并在重连成功时记录埋点。

---

## 5. 校验与测试

- JSON Schema 可用于后端单元测试及前端契约测试。
- 在 `backend/tests/integration/news_stream.test.md` 中记录 curl/pytest 示例。
- 若使用 Pydantic，可参考 `src/models/schema.py` 中新增的 `NewsStreamEvent` 与 `ChainOfThoughtStep` 模型。

---

## 6. 待确认

| 项目 | 当前状态 | 责任人 |
|------|----------|--------|
| `summary` 是否必填 | 建议作为可选字段，空时前端使用默认占位 | Backend |
| `indexValue` 数据源 | 使用同一行情 API 还是单独字段 | Data |
| `complianceStatus=blocked` 时是否推送 `chainOfThought` | 建议仍下发但标记，不渲染正文 | Compliance |
| `signalTags` 来源 | LLM 生成 or Rule-based | Product |

---

> 后续更新需同步计划文档与测试脚本，确保前后端一致。
