# AI 实时新闻板块信息架构与设计规范（阶段 2 交付草案）

> 版本：v0.1（待设计评审）  
> 目标：指导 Figma 设计稿产出，确保前端实现具备明确的组件结构、交互流程与视觉基准。

---

## 1. 页面结构概览

### 1.1 桌面端布局（≥1440px）
- **左侧主列（72% 宽）**
  - `IndexSignalChart`：折线图 + 成交量柱状图；叠加买/卖信号点，悬浮显示价格、时间、标签。
  - `FiltersBar`：方向筛选（全部/Bullish/Bearish/Neutral）、时间范围（1H、24H、7D）、关键字搜索框。
  - `NewsTickerList`（可选可折叠）：实时新闻卡片缩略列表，点击可触发 Modal。
- **右侧侧栏（28% 宽）**
  - `SentimentDial`：仪表盘展示 `direction` 与 `confidence`。
  - `LiveStatusBar`：显示 SSE 状态、最后更新时间、延迟预警。
  - `SignalLegend`：买/卖点标签说明，含理由标签（如 “OPEC 不及预期”）。

### 1.2 平板端布局（1024–1439px）
- 主列与侧栏上下堆叠，`SentimentDial` 与 `LiveStatusBar` 合并为顶部卡片。
- `FiltersBar` 置于折线图上方，新闻列表以卡片方式紧随其后。

### 1.3 移动端布局（≤1023px）
- 单列滚动：顺序为 `IndexSignalChart` → `FiltersBar` → `SentimentDial` → `LiveStatusBar` → `NewsTickerList`。
- Modal 转为全屏覆盖，Chain of Thought Drawer 由底部滑入。

---

## 2. 组件树定义

```
NewsRealtimePage
├── LayoutShell
│   ├── AppHeader (保留导航/Logo)
│   └── ContentGrid
│       ├── IndexPanel
│       │   ├── FiltersBar
│       │   ├── IndexSignalChart
│       │   └── NewsTickerList (可选)
│       └── InsightsPanel
│           ├── SentimentDial
│           ├── LiveStatusBar
│           └── SignalLegend
├── NewsPreviewModal (Portal)
│   └── components:
│       ├── ModalHeader (标题 + 标签 + 关闭按钮)
│       ├── SignalMeta (方向、理由、时间、价格区间)
│       ├── SummaryText (最大 200 字)
│       └── ActionsRow (查看推理、打开引用、分享等按钮)
└── ChainOfThoughtDrawer (Portal)
    └── components:
        ├── DrawerHeader (返回 Modal / 关闭)
        ├── ThoughtStepList (树状/手风琴结构)
        └── CitationList (可点击跳转新窗口)
```

---

## 3. 关键交互流程

1. **买/卖点点击**
   - 触发条件：点击图表上的 `signalId` 点位或新闻列表项。
   - 响应：异步加载对应的新闻数据（如 Modal 未缓存，则请求 `/api/news/{newsId}` 或从 SSE 缓存中读取）。
   - 反馈：Modal 打开，展示 `headline`、`direction`、`confidence`、`signalTags`、`summary`。

2. **Modal 内操作**
   - “查看推理”：触发 Chain of Thought Drawer，传入 `chain_of_thought` 与 `citations`。
   - “打开引用”：新标签页打开 URL，并弹出 Toast 提示用户离开本站。
   - “标记无关”（选项）：仅在业务确认后启用，影响后续推荐。

3. **Drawer 交互**
   - 支持逐步展开（手风琴模式），每步展示标签、正文、引用链接。
   - 点击引用时提供域名、简短描述；若 `complianceStatus = masked`，显示脱敏提示。

4. **状态提示**
   - SSE 中断：顶部浮出通知条（黄色），显示“实时连接中断，正在重试…”以及重连倒计时。
   - 数据延迟 ≥120s：StatusBar 转为橙色，提供“刷新数据”按钮。

---

## 4. 视角切换与数据流

```
SSE /api/news/stream ───────────────┐
                                   │
                      ┌────────────▼────────────┐
                      │ useNewsStream Store      │
                      │ - latestNews Map         │
                      │ - chainOfThought Cache   │
                      │ - streamStatus           │
                      └────────────┬────────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │                                     │
     IndexSignalChart (signals)          NewsPreviewModal / Drawer
                │                                     │
       useIndexSignals Hook               selects data by newsId
```

- `useNewsStream`：维护 `Map<newsId, NewsPayload>`、`streamStatus`、最近更新时间。
- `useIndexSignals`：从价格数据接口或后端推送获取 `{ signalId, newsId, price, reasonTag }`，并与 `useNewsStream` 关联。
- 全局事件：当 SSE 推来新新闻时，若存在匹配的 `signalId`，在图表上高亮该点位。

---

## 5. 视觉与主题基准

### 5.1 色板（初稿）
| 名称 | 十六进制 | 用途 | 备注 |
|------|----------|------|------|
| `bg-primary` | `#05070D` | 主背景 | 参考 nof1.ai，需确保文本对比度 |
| `bg-surface` | `#0E1118` | 卡片背景 | 2px 边框强调“终端”感 |
| `accent-bull` | `#00B2A9` | Bullish 状态 | 参考 TradingView 绿色但略带青色 |
| `accent-bear` | `#FF5C5C` | Bearish 状态 | 高频对比色 |
| `accent-neutral` | `#F0A500` | Neutral/Highlight | 接近 Bloomberg 橙 |
| `accent-signal` | `linear-gradient(135deg, #36C2FF, #9A4DFF)` | 买/卖信号描边 | 霓虹渐变取自 nof1.ai |
| `text-primary` | `#E5EAF5` | 主文本 | 与背景对比约 12:1 |
| `text-secondary` | `#9AA5BE` | 次级文本 | 控制对比约 4.5:1 |
| `border-strong` | `#1F2430` | 2px 边框 | 模拟 Bloomberg 界面分割线 |

### 5.2 字体与字号
- 主字体：`Inter` / `IBM Plex Sans`（Fallback：思源黑体）。
- 等宽数据：`IBM Plex Mono`。
- 字号层级：`32/24/20/16/14/12/10`，分别用于标题、标签、图表刻度。
- Carbon AI Label 使用建议：在 Figma 中尝试自动生成按钮/ARIA 文案时，保留原始提示并手动翻译调整，最终写入 i18n 文本表。

### 5.3 间距与网格
- 网格：12 列，gutter 24px。
- 内间距：卡片采用 24px，Modal 32px，Drawer 28px。
- 圆角：卡片 12px，按钮 8px，图表容器 16px。

---

## 6. 可访问性与国际化

- 色彩对比度按照 WCAG AA 标准（文本对比 ≥4.5:1，小标签 ≥3:1）。
- 提供键盘焦点样式（1px 外描边 + 内阴影）。
- Modal / Drawer 打开时禁止背景滚动，支持 `Esc` & 关闭按钮。
- 所有动态文本需绑定到 i18n 资源（`zh-CN` 为默认），后续可扩展 `en-US`。
- Carbon AI Label 生成的文案仅作为建议稿，最终版本需通过人工审核并记录在设计备注中。

---

## 7. 设计产出要求

- **Figma 文件结构**：
  - Page 1：Desktop 1440、Tablet 1280、Mobile 428 布局。
  - Page 2：组件库（Buttons、Badges、Charts、Modals）。
  - Page 3：交互动效说明（使用 FigJam 或注释层）。
- **交付物**：
  - 组件命名遵循 `News/ComponentName/Variant`，便于 Storybook 映射。
  - 导出 `PNG`/`PDF` 快照，存放于 `docs/design/exports/`。
  - 在设计描述中附加 Carbon AI Label 提示与翻译对照。

---

## 8. 开放问题

| 问题 | 当前假设 | 责任人 | 备注 |
|------|----------|--------|------|
| 图表库选择 | 优先 Apache ECharts，如需 TradingView 小组件需评估许可证 | Frontend | 待确认 |
| Modal 数据加载策略 | 首次打开时触发 `/api/news/{id}`，之后缓存 | Backend/Frontend | 需确定接口是否存在 |
| 信号点样式 | 使用渐变描边还是纯色？需 A/B | Design | 设计评审决定 |

---

## 9. 下一步

1. 将本规范同步至设计团队，收集反馈并更新颜色/布局。
2. 在 Figma 中根据本规范搭建 Desktop 版本 → Tablet → Mobile。
3. 设计评审后，输出交互说明与截图，回填至计划中的设计评审纪要。
