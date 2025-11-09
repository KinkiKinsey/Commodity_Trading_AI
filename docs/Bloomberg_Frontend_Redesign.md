# 彭博风格前端重塑设计蓝图（Ringshell 实时资讯页）

---

## 0. 文档目的与设计体系来源
- **目标**：基于 Bloomberg 设计体系重构 `frontend/web/app/news/real-time/page.tsx`，在保留现有实时能力的前提下，输出专业、信息密集且符合终端使用习惯的界面。
- **引用规范**  
  1. `AI_real_time_news_plan1021.md`（业务目标、数据流、功能需求）  
  2. `docs/项目文档/前端规范/bloomberg-design-specification.md`（官方视觉与交互规范）  
  3. `docs/项目文档/前端规范/bloomberg-variables.css`（CSS 变量）  
  4. `docs/项目文档/前端规范/tailwind.config.js`（Tailwind 配置）  
  5. 手动截取的 SPX 页面参考图：`reference/bloomberg_wti/screenshots/*.png` 与说明 `reference/bloomberg_wti/notes.md`
- **交付**：为产品、设计、前端提供统一的实现蓝图。任何变更需同步更新此文档。

---

## 1. 核心摘要
1. 采用 Bloomberg 终端式深色主题（黑色导航 + 深灰卡片），强调信息密度和数据对齐。  
2. 重建页面骨架：顶部黑色导航、三列主体（市场 / 新闻 / 洞察）、底部行情带。  
3. 将实时新闻、AI 信号、Chain of Thought、情绪仪表、价格图等能力统一在 Bloomberg 视觉语言下呈现。  
4. 逐阶段交付：先搭建主题与骨架，再填充模块、优化交互、确保可访问性与性能指标。  

---

## 2. 用户画像与关键任务
| 角色 | 核心目标 | 高频任务 | 对应模块 |
|------|----------|----------|----------|
| 商品分析师 | 快速洞察油价驱动因素 | 对比价格走势与 AI 推理、整理链路 | 市场列（行情头条、指标卡）、新闻列（CoT、引用） |
| 能源交易员 | 分钟级决策 | 监控实时行情、信号状态、连接稳定性 | 市场列（图表、信号）、顶部警示、底部行情带 |
| 策略研究员 | 回测与复盘 | 搜索历史事件、查看指标统计 | 新闻列（过滤器、列表）、洞察列（统计、情绪） |

---

## 3. 体验原则
1. **高密度**：使用等宽字体、紧凑间距、卡片叠层展示，保证单屏信息量最大。  
2. **专业可信**：显示数据来源、更新时间、预测置信度；重要数据使用 Bloomberg Mono 对齐。  
3. **实时敏捷**：界面需支持 1 秒级推送且保持稳定，实时状态清晰可见。  
4. **结构一致**：导航、卡片、表格、标签遵循设计系统的阴影、边框、字体与色彩规范。  
5. **多语言与键盘友好**：所有交互可键盘触达，支持中英切换、色盲模式。

---

## 4. 页面结构与布局
### 4.1 顶部导航（黑色背景）
- 参考 `bloomberg-design-specification.md` §5.1：黑色导航栏 `--bloomberg-black`，内容宽度 1440px、左右 32px 内间距。  
- 内容：Logo（Ringshell 字标）、一级导航（Markets、Economics...）、辅助导航（More、Live TV）、Subscribe 按钮、用户菜单、全局搜索。  
- Hover 状态：文字从 `rgba(255,255,255,0.7)` 过渡到白色；按钮 hover 背景 `rgba(255,255,255,0.08)`。

### 4.2 主体三列
- **栅格**：`max-width: 1440px`，`grid-template-columns: 320px minmax(0,1fr) 320px`，列间距 24px，顶部/底部留白 48px。  
- **左列（Market Column）**：关注列表、快速行情、模板卡片（可参照 `.market-ticker` 组件）。  
- **中列（Main）**：行情头条 + 工具栏 + AI 信号 + 新闻列表。  
- **右列（Insights）**：LiveStatusBar、Sentiment Dial、Chain of Thought 摘要、Upcoming Features。  
- 在 `xl` 以下（<1280px）右列折叠为抽屉；在 `lg` 以下改为纵向堆叠。

### 4.3 底部行情带
- 背景 `var(--bg-secondary)`，高度 48px，左对齐“Markets Ticker”，右对齐 SSE 状态。  
- 行情项目使用 `.ticker-pill` 样式（字体 `var(--font-data)`，背景 `rgba(255,255,255,0.07)`）。

### 4.4 参考截图
- `nav-top.png`: 导航与工具条布局  
- `hero-overview.png`: 行情头条 + 图表区  
- `overview-key-stats.png`: Overview & Key Statistics + Markets at a Glance  
详见 `reference/bloomberg_wti/notes.md`。

---

## 5. 视觉系统（根据 CSS 变量）
### 5.1 颜色映射
| 语义 | CSS 变量 | 十六进制 | 用途 |
|------|----------|----------|------|
| 导航背景 | `--bloomberg-black` | `#000000` | 顶部栏、底部 ticker |
| 页面背景 | `--bg-primary` | `#0D0D0D` | 页面背景 |
| 卡片背景 | `--bg-card` | `#1C1C1C` | 市场/新闻/洞察卡片 |
| Hover 背景 | `--bg-hover` | `rgba(255,255,255,0.03)` | 卡片 hover |
| 正文文字 | `--text-primary` | `#FFFFFF` | 主文字 |
| 次级文字 | `--text-secondary` | `#A0A0A0` | 描述/时间戳 |
| 正向数值 | `--color-positive` | `#00C805` | 上涨/多头 |
| 负向数值 | `--color-negative` | `#FF3347` | 下跌/空头 |
| 警示 | `--color-warning` | `#F59E0B` | SSE 异常提示 |

> 若需浅色对比（用户反馈导航黑 + 内容白），可在 `body` 增加 `data-theme="light"` 并引入衍生变量，但此设计蓝图默认深色方案。

### 5.2 字体
- 主体字体：`var(--font-body)`（Inter 系列）。  
- 数据字体：`var(--font-data)` 用于价格、涨跌幅、统计。  
- 字重：标题使用 `--font-semibold (600)`，正文 `--font-regular (400)`，标签/按钮 `--font-medium (500)`。  
- 数字对齐：`font-variant-numeric: tabular-nums`。

### 5.3 间距与圆角
- 间距：`var(--space-4)` (16px) 为基础单位，卡片外间距 24px。  
- 圆角：卡片 `--radius-md (6px)`，按钮 `--radius-sm (4px)`。  
- 阴影：`shadow-dark-md` (`0 4px 6px rgba(0,0,0,0.3)`) 突出卡片层级。

### 5.4 图标与图表
- 图标集：Lucide 图标 16px/20px、笔直线条，颜色 `text-secondary` hover 到白色。  
- 图表背景：`#111111`，轴线半透明白色，涨跌使用 `--color-positive`/`--color-negative`，信号 marker 使用橙色描边。

---

## 6. 模块化组件规范
### 6.1 顶部导航 `.global-navbar`
- 高度 64px，左右 Padding 32px，Logo 左对齐，右侧包含 Subscribe、用户菜单、搜索。  
- 使用 CSS 类：`bg-black text-white flex items-center justify-between`.

### 6.2 行情头条 `.market-hero`
- 左侧：Ticker 徽章、资产名称（`text-2xl`）、市场状态。  
- 中部：主要数值（`text-data-lg`）、涨跌幅（颜色正/负）、上次更新时间。  
- 右侧：`Add to Watchlist`、`Share`、`More`，按钮使用 `.btn-secondary`。  
- 下方 3×2 数据网格，使用 `.data-grid`（参见设计规范 §8.3）。

### 6.3 图表与工具栏
- 工具栏按钮高度 36px，间距 8px，选中态背景 `rgba(255,255,255,0.08)`，边框 `--border-primary`。  
- 图表容器 `.chart-card` 背景 `--bg-card`，内边距 24px，支持 `News` toggle、`Add Comparison` 输入框（`.input` 样式）。

### 6.4 实时信号列表
- 列表项高度 48px，左右 Padding 16px，hover 状态 border 改为 `--bloomberg-orange`。  
- 左侧标签 `terminal-text` (IBM Plex Mono 11px)，右侧时间/价格 `text-xs`.

### 6.5 新闻卡片 `.news-card`
- 背景 `--bg-card`，左侧竖线 `border-left: 3px solid transparent`，hover 变为 `--bloomberg-orange`。  
- 标题使用 `text-base font-semibold`, 摘要 `text-sm text-secondary`，标签 `text-xs uppercase`.

### 6.6 洞察侧栏模块
- **Sentiment Dial**：使用 `market-positive`/`market-negative` 渐变指针，标签 `tabular-nums`。  
- **Chain of Thought 摘要**：列表项高度 56px，展示步骤标题 + 时间 + 来源。  
- **LiveStatusBar**：三态 Badge（connecting/ open/ error）颜色对应警示色。

### 6.7 表格与统计
- `Overview`/`Key Statistics` 表使用 `.data-table`：标题 sticky、数值右对齐、hover 背景 `rgba(255,255,255,0.03)`。

---

## 7. 栅格与响应式
- 断点采用设计系统：`xs 480`, `sm 640`, `md 768`, `lg 1024`, `xl 1280`, `2xl 1536`, `3xl 1920`.  
- `xl` 以上使用三列，`lg` 以下转为两列（市场 + 新闻），`md` 以下全部改为纵向堆叠并通过 tabs 在顶部切换。  
- 最大宽度 `max-w-8xl (88rem)`，导航与底部 ticker 与主体对齐。

---

## 8. 交互与微动效
- 新数据到达时对价格和信号卡使用 `animate-data-update`（橙色闪烁 0.5s）。  
- 新闻列表 hover 左侧竖线过渡到橙色，卡片滑动 `translateY(-4px)`。  
- 图表 tooltip、切换按钮等动效遵循 `transition-duration: 200ms`。  
- LiveStatusBar 连接状态使用 `pulse` 动画提示。  
- 键盘交互：Tab 顺序为 导航 → 筛选器 → 新闻卡 → 洞察 → 底部 ticker。

---

## 9. 可访问性与国际化
- 所有颜色对比度 ≥ 4.5:1；提供 `data-color-scheme="cvd"` 以启用蓝/红涨跌模式。  
- 新闻卡、按钮、toggle 均提供 `aria-label` 与 `aria-pressed`；新闻列表 `aria-live="polite"`。  
- 语言切换：`zh-CN` 与 `en-US`，日期/数字格式跟随 locale。  
- 提供 `Skip to latest news` 隐藏链接、`focus-visible` 样式以及表格 `scope` 属性。

---

## 10. 实施指南
1. **引入主题**  
   - 方案 A：在 `_app` 或 `layout.tsx` 中引入 `bloomberg-variables.css`，并在 `body` 添加 `data-theme="dark"`。  
   - 方案 B：复制官方 `tailwind.config.js`，合并到项目 `tailwind.config.ts`（保留现有内容），并启用自定义 utilities。  
2. **全局样式**：在 `globals.css` 中设置 `font-family: var(--font-body)`、`background-color: var(--bg-primary)`。  
3. **组件类名**：优先使用提供的 `.data-card`、`.input`、`.btn` 等 class，保证视觉一致。  
4. **暗浅模式切换**：若需要浅色内容区，可在 wrapper 上添加 `data-theme="light"` 并根据 CSS 变量切换。  
5. **PostCSS**：如使用 Tailwind，确保 `postcss.config.js` 开启 `tailwindcss` 与 `autoprefixer`。

---

## 11. 递进式路标
| 阶段 | 目标 | 关键产出 |
|------|------|----------|
| Phase 1 | 主题与骨架 | 引入设计系统变量、导航/三列/底部骨架（已完成） |
| Phase 2 | 市场列细化 | Watchlist、快速行情、Key Stats 卡片 |
| Phase 3 | 主列深度 | 行情头条、工具栏、图表、信号列表、新闻卡 |
| Phase 4 | 洞察列 | 情绪仪表、CoT 摘要、Markets at a Glance |
| Phase 5 | 搜索与模态 | 全局搜索、比较组件、预览/推理抽屉一致化 |
| Phase 6 | QA & 性能 | 无障碍、E2E、性能指标、文档更新 |

---

## 12. 交付与依赖
- 组件代码（`app/news/real-time`、`components/layout` 等）  
- 主题配置与变量文档  
- Storybook 描述（导航、行情头条、新闻卡、洞察模块）  
- 更新后的 README/发布说明  
- 参考素材归档（screenshots、notes、设计规范）

---

## 13. 风险与开放问题
1. **实时性能**：Charts/Signals 更新频率需评估，避免背景色与阴影引起渲染卡顿。  
2. **版权与品牌**：需确认 Ringshell 是否允许使用 Bloomberg 字体/配色，必要时做定制化变体。  
3. **可用性测试**：需要在实际交易工作流中验证暗色方案与布局是否满足需求。  
4. **浅色诉求**：若业务要求白底内容，需定义 `light` 主题覆盖表（在附录提供占位方案）。  

---

## 14. 成功指标
- 用户完成关键任务时间缩短 ≥30%（找新闻、定位信号、切换资产）。  
- SSE 连接延迟 < 2s，24 小时内无未捕获异常。  
- 可访问性检查（axe、Lighthouse）无严重错误，色盲模式可用。  
- FCP < 1.5s，LCP < 2.5s，CLS < 0.1，TTI < 3.8s。  
- UAT 满意度 ≥ 4/5。

---

## 15. 附录
### 15.1 参考资料
- `docs/项目文档/前端规范/`：设计说明、CSS 变量、Tailwind 配置。  
- `reference/bloomberg_wti/`：截图、notes、捕获脚本。  
- 相关组件：`components/common/data-card.tsx`, `components/news/*`, `components/layout/AppShell.tsx`.

### 15.2 轻量白底模式（可选扩展）
若需要“黑色导航 + 白色内容区”的变体，可在根节点加 `data-theme="light"` 并覆盖以下变量：
```css
[data-theme="light"] {
  --bg-primary: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-alt: #F5F7FA;
  --text-primary: #0A0C10;
  --text-secondary: #4C4C4C;
  --border-primary: rgba(15, 23, 42, 0.08);
}
```

---

**版本**：2.0.0  
**最后更新**：2025-10-26  
**维护人**：前端团队 (参考 Bloomberg Design System)  
