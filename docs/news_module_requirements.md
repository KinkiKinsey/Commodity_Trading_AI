# AI 实时新闻板块功能与数据契约摘要

> 版本：v0.1（待业务确认）  
> 目的：概括“AI 实时新闻板块”当前要实现的范围、输入输出字段与合规约束，供前后端/设计/合规同步。

---

## 1. 功能范围（根据客户最新需求）
- **指数首页保留**：初期的 `index` 页面仅呈现指数曲线、买/卖信号点位及基础指标，不直接裸露大段 AI 文本。
- **两级信息联动**：
  1. 用户点击任一买/卖点 → 弹出 *News Preview Modal*（展示标题、方向、情绪标签、生成时间、关键信号标签）。
  2. Modal 内点击“查看推理” → 打开 *Chain of Thought Drawer*，展示链式推理步骤与引用来源，可进一步拉取完整引用。
- **实时刷新策略**：页面维持 SSE 订阅，指数视图与新闻视图可切换但数据层共享；心跳推荐 10s，新闻有更新时增量推送。
- **多终端适配**：桌面端支持双列布局（左侧指数、右侧实时新闻），移动端以单列+底部抽屉形式呈现。
- **手动刷新与降级**：当 SSE 延迟超过 120s 或断开时，显示黄色提醒条并提供手动刷新；降级时读取最近缓存新闻。

---

## 2. 数据契约

### 2.1 SSE `/api/news/stream`（真实数据源仍待后端实现）
| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| `eventId` | `string` | 唯一事件 ID（UUID） | 用于前端去重 |
| `timestamp` | `string (ISO8601)` | 新闻生成/推送时间 | 显示在卡片与 signal tooltip 中 |
| `headline` | `string` | 新闻标题（与指数信号关联） | 需与 `signals[].newsId` 匹配 |
| `summary` | `string` | 简要摘要（<= 200 字） | 仅用于 Modal，首页不直接展示 |
| `direction` | `"bullish" \| "bearish" \| "neutral"` | 市场方向 | 映射到颜色与箭头 |
| `confidence` | `number (0-1)` | 置信度 | 用于仪表盘组件 |
| `chain_of_thought` | `Array<{ id: string; step: number; text: string; evidence?: string; url?: string; }>` | 链式推理步骤 | 来自 `SOCommodity.chain_of_thought`，需补充结构化字段 |
| `citations` | `string[]` | 引用链接列表 | 基于 `SOCommodity.citations` |
| `signalTags` | `string[]` | 标签（如 “OPEC 不及预期”） | 用于买/卖点 Tooltip 与 Modal |
| `complianceStatus` | `"clean" \| "masked" \| "blocked"` | 合规状态 | `masked` 时前端需提示并遮挡敏感文本 |
| `language` | `string` | 输出语言标识 | 默认为 `zh-CN`，需与用户语言一致 |

### 2.2 指数信号数据（新增）
| 字段 | 类型 | 说明 |
|------|------|------|
| `signalId` | `string` | 信号唯一 ID，与新闻 `eventId` 或 `newsId` 关联 |
| `signalType` | `"buy" \| "sell"` | 信号类型 |
| `price` | `number` | 触发价格 |
| `indexValue` | `number` | 指数当值（可与价格相同，取决于数据源） |
| `reasonTag` | `string` | 触发原因短语，例如 “OPEC 不及预期” |
| `newsId` | `string` | 对应新闻 ID，用于触发 Modal |
| `createdAt` | `string` | 信号生成时间 |

### 2.3 指数行情序列
沿用 `get_yahoo_data` 返回格式（后端可封装为 API）：`[{ date: string, close: number, volume: number }]`。前端需将日期转换为 Unix 时间戳或 ISO 字符串以供图表渲染。

---

## 3. 指标 & 刷新策略
- **新闻刷新频率**：SSE 实时推送；若 60s 内无新事件，仍发送心跳包（含 `event: heartbeat`）。
- **指数与信号**：推荐 1 分钟增量更新；若来自外部 API（Yahoo）需缓存以减少调用。
- **链式推理深度**：默认 6-10 步；当步数 <3 时需在前端提示“推理简化”并允许用户查看原始文本。
- **Latency 目标**：信号触发后 ≤3s 展示 Modal 数据；SSE 重连策略使用指数退避（1s,2s,4s,8s）。

---

## 4. 合规与内容限制
- **数据来源标注**：Modal/Drawer 内需显式显示引用链接标题/域名 + 时间戳；外链打开新窗口并提示“第三方链接”。
- **免责声明**：指数页底部展示“信息仅供研究参考，不构成投资建议”；移动端需在抽屉顶部展示。
- **日志与追溯**：后端需保留 SSE 事件日志 ≥180 天（参考项目文档要求），并记录 `signalId -> newsId` 映射。
- **敏感词过滤**：后端在推流前执行；若触发，`complianceStatus=masked` 并传递脱敏文本，前端提示“部分内容因合规原因已隐藏”。
- **多语言一致性**：遵循原始新闻语言；当输入为中文时输出必须中文（参照 `COMMODITY_AGENT_PROMPT`）。

---

## 5. 待确认事项
| 项目 | 描述 | 负责人 | 状态 |
|------|------|--------|------|
| SSE 接口实现人 | `/api/news/stream` 由谁负责实现/部署 | Backend | ☐ |
| 指数数据源 | 是否继续使用 Yahoo Finance 或切换至国内数据商 | Data | ☐ |
| 合规审查流程 | 敏感词词库、审批人及 SLA | Compliance | ☐ |
| UI 验收 | Figma 设计是否需要客户签字确认 | Design | ☐ |

---

## 6. 阶段 1 验收清单
- [ ] 业务方确认本简表（邮件或 IM 记录）。
- [ ] 后端确认字段列表（尤其 `signalId ↔ newsId` 映射）。
- [ ] 合规团队确认免责声明位置与过滤策略。
- [ ] 设计团队确认交互流程（买/卖点 → 新闻 → 推理弹窗）。

> 完成勾选后方可进入计划的阶段 2（信息架构与设计定稿）。
