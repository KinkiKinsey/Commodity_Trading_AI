# AI 实时新闻模块落地计划(中国商业上线版)

> 适用范围:Ringshell_AI 项目 Web 端(面向中国境内商业用户)
> 目的:确保 AI 实时新闻模块以可执行的分步方案完成,每一步均有明确的验收标准,供后续多轮 GPT 协作参照。

---

## 0. 背景与约束

- **商业定位**:面向大宗商品研究/交易客户,需提供稳定的实时新闻展示、链式推理、情绪方向与引用详单。
- **技术栈约定**:Next.js 14(App Router), React 18 + Tailwind + Ant Design Pro,实时数据通过 FastAPI SSE/WebSocket。
- **合规要求**:部署在中国境内服务器;第三方接口满足等保二级日志留存;对外引用链接必须显示来源与时间戳。
- **设计参考**:nof1.ai(暗色、霓虹风格、信息密度高),同时兼顾国内审美与可访问性(中文字体、对比度)。
- **辅助资源**:Carbon Design System(布局、交互与 AI Label 工具)仅作参考;所有生成文案需经过中文金融术语校对并落地到自有 i18n 资源。
- **数据库基础**:采用「OLTP + OLAP + Cache」三层结构——PostgreSQL/TimescaleDB 负责主数据与因子快照,ClickHouse(或 Doris)存放高频行情与新闻历史,Redis 作为实时缓存与 SSE 推送缓冲;长远可引入 Kafka 流处理对接外部实时金融数据 API。

### 0.1 仓库结构(已重构)

```
ringshell/
├── backend/                # Python 服务与 LangGraph Agent
│   ├── src/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js Web 工程(待实现)
│   └── web/
├── services/
│   └── ctp/                # 期货通道适配
├── docs/                   # 项目文档(IA、API、规划等)
└── docker-compose.yml
```

> 后续所有后端代码、测试、虚拟环境脚本均在 `backend/` 下维护;前端以 `frontend/web` 为主;公共文档归档至 `docs/`。

### 0.2 数据库与实时数据管道规划

- **关系型数据库(PostgreSQL/TimescaleDB)**
  - 存储用户画像、订阅配置、因子权重快照、AI 推理结果元数据。
  - TimescaleDB 扩展处理 K 线/指标等时序查询,支持未来多因子仪表盘。

- **分析型数据库(ClickHouse 或 Apache Doris)**
  - 按日/小时分区保存行情、新闻全文、链式推理原文,便于高并发查询。
  - 结合物化视图为黑天鹅预警提供快速聚合。

- **缓存层(Redis)**
  - 维护实时新闻最新状态、SSE 心跳、用户自定义假设推理过程。
  - 作为队列缓存外部 API 数据,配合 Celery / FastAPI Background Task 执行刷新。

- **流处理**
  - 推荐引入 Kafka 或 Pulsar 聚合外部实时 API(如 Refinitiv、Wind、Polygon.io),以 topic 形式推送至后端服务。
  - 可用 Flink/ksqlDB 做实时计算,生成黑天鹅预警候选事件。

> 数据库建模与连接配置需在阶段 3.1 中推进:`backend/src/db/` 目录定义 ORM/查询层,提供统一接口给新闻、价格预测、因子仪表盘模块复用。

---

## 仓库现状速览(关键输入输出)

- **智能体输出结果**:`src/core/commodity_agent.py` 调用 LangChain 工作流,最终压缩模型返回 `SOCommodity`(方向 `direction`、置信度 `confidence`、链式推理 `chain_of_thought`、引用 `citations`),是前端实时新闻卡片的核心 JSON。
- **数据检索工具**:`src/core/utils.py`(未展开)与 `firecrawl_search`/`think_tool` 提供新闻信息;输出文本由 `compress_research` 汇总并写入 `analysis` 字段。
- **行情数据入口**:`src/financial/data_sources/price_data.py` 的 `get_yahoo_data` 会返回包含 `['date','close','volume']` 的 `pandas.DataFrame`,用于构建指数曲线、买卖点位。
- **金融分析模块**:`src/financial/analyzers/*` 提供多种指标分析(流动性、期限结构等),多为字符串报告,可拆分关键信息辅助链式推理。
- **CTP 适配层**:`ctp/` 目录封装交易前置与行情通道,后续对接入国内期货所需保持接口稳定。

> 当前仓库尚未包含前端实现;计划需结合上述数据结构定义页面组件、SSE payload,以及买卖点 → 新闻 → 推理的联动。

---

## 阶段拆解与验收(完成一步 → 检验一步)

### 阶段 1 · 需求对齐与落地范围(T+1 天)

- **主要任务**
  - 汇总 `PROJECT_DOCUMENTATION.md` 与 `项目文档` 中的 AI 新闻模块需求,输出 1 页《功能与数据契约摘要》。
  - 明确核心指标:新闻更新频率、链条深度、sentiment/confidence 范围、可展示引用数量。
  - 与业务确认商业上线所需合规项:免责声明、数据来源展示、敏感词过滤流程。
  - 追加客户提出的首页策略:**Index 专区保留**(前期仅展示指数与买/卖点),禁止直接输出大段文本;点击买/卖点触发新闻弹窗,再进入推理链弹窗。

- **验收**
  - 文档提交至 `docs/`(命名 `news_module_requirements.md`),业务负责人批注确认。
  - API 字段对照表与后端团队对齐并记录确认时间(签字或邮件摘要)。

### 阶段 2 · 信息架构与设计定稿(T+1.5 天)

- **主要任务**
  - 在 Figma 建立参考画板,导入本地 `nof1_ai_home.html` 与 `nof1_style*.css` 提炼视觉语言,并与 TradingView / Bloomberg 的专业配色(深灰背景、蓝/紫/橙信号色)混搭,输出桌面、平板、移动 3 个断点的低保真方案。
  - 定义组件树:`HeadlinePanel`、`SentimentDial`、`ChainOfThoughtAccordion`、`CitationsList`、`LiveStatusBar`、`FiltersBar`。
  - 规划两级弹窗:①买/卖点点击出现新闻摘要卡;②在卡片内点击"查看推理"打开链式推理抽屉,并保证移动端触控可用。
  - 形成视觉变量(字体、色板、阴影、动效基准)及无障碍要求(最低对比度 4.5:1、键盘导航顺序),在 Figma 中标注"灵感来源 vs 自定义实现"以防直接复用原站素材;如参考 Carbon AI Label 输出,需要保留原始提示及人工修订记录。

- **验收**
  - 设计稿链接与导出的关键图存放于 `docs/design/`,附带交互说明 PDF。
  - 召开设计评审并记录会议纪要(确认项、遗留问题、负责人)。

### 阶段 3 · 数据契约与实时通道实现(T+2 天,前后端并行)

- **主要任务**
  - 定义 `/api/news/stream` SSE schema(含心跳、错误码、版本号),补充后端单测;payload 需至少包含 `direction`、`confidence`、`chain_of_thought[]`、`citations[]`、`headline`、`timestamp`,与 `SOCommodity` 字段对应。
  - 为指数买/卖点建立数据契约:包含 `signalId`、`signalType`(buy/sell)、`price`、`newsId`、`reasonTag`(如 "OPEC 不及预期"),便于前端点击后查询新闻与推理。
  - 完善敏感词过滤与引用校验流程(上线时后端执行,前端提示状态),提供 `complianceStatus` 字段以告知前端是否需要遮挡文本。
  - 初始化数据库接口:在 `backend/src/db/` 中定义 PostgreSQL/Timescale 连接、`news_events`、`signals` 表结构,ClickHouse 连接配置,以及 Redis Channel(`news_stream`,`user_hypothesis`)。

- **验收**
  - 更新 OpenAPI/接口文档并截图存档;通过 JSON schema 校验。
  - 集成测试脚本跑通(记录命令与输出)并存入 `backend/tests/integration/news_stream.test.md`。

### 阶段 4 · 前端骨架与状态管理(T+1 天)

- **主要任务**
  - 在 `frontend/web` 项目下创建 Next.js 路由 `app/news/real-time/page.tsx`,搭建主布局(宽屏双列、窄屏单列)。
  - 建立 Zustand store + TanStack Query + SSE 客户端封装(`useNewsStream` Hook);额外创建 `useIndexSignals` 以缓存买/卖点位数据。
  - 配置暗色主题、全局字体(本地优先、思源黑体 fallback),接入终端风格基础样式,并准备 TradingView/Bloomberg 色板变量。

- **验收**
  - ✅ 前端骨架完成:Next.js 14 + Tailwind + Zustand + React Query 项目已初始化,`app/news/real-time/page.tsx` 展示筛选条、指数信号占位图、新闻列表与状态侧栏。
  - ✅ `useNewsStream` 与 `useIndexSignals` 钩子可处理实时数据状态;`useNewsStreamStore`/`useIndexSignalsStore` 已提供占位逻辑。
  - 待完成:`pnpm lint --filter web`、`pnpm test --filter web --runInBand`(在后续阶段加入实际组件后执行);Storybook 页面骨架将在组件完善后补充并记录于 `docs/review_logs/step4.md`。

### 阶段 5 · 关键组件开发(T+2 天)

- **主要任务**
  - 实现所有核心组件(含加载 Skeleton、错误态):链式推理树支持缩进、高亮、折叠动画。
  - 在 `frontend/web` 下构建 `IndexSignalChart`(当前使用 SVG Sparkline 占位,后续可替换为 ECharts/TradingView),展示价格曲线 + 买卖点标注,点击点位触发 `NewsPreviewModal`。
  - `NewsPreviewModal` 展示标题、方向、信号标签;内部按钮"查看推理"调起 `ChainOfThoughtDrawer`,展示 `chain_of_thought` 分步逻辑及引用。
  - 引用列表自动识别域名并显示 favicon,区分国内/海外链接样式。
  - 实现实时状态条:最近更新时间、数据延迟提示、重连按钮、API 状态指示。

- **验收**
  - ✅ 组件已落地:`SentimentDial`、`LiveStatusBar`、`IndexSignalChart`(SVG 占位)、`NewsPreviewModal`、`ChainOfThoughtDrawer`、`CitationsList` 全部接入页面;信号列表、新闻卡支持状态与键盘操作。
  - ✅ Demo 数据接入:在 `/app/news/real-time/page.tsx` 注入示例新闻「美国总统军事施压委内瑞拉 …」,链式推理、引用、置信度与买卖信号全部按 nof1.ai 风格渲染。
  - ✅ `npm run lint` 通过,确保新增代码符合规范;待下一阶段补充 Storybook 与单测。

### 阶段 6 · 页面整合与交互增强(T+1 天)

- **主要任务**
  - 在 `frontend/web/app/news/real-time/page.tsx` 中配齐各组件,加入方向/时间跨度过滤器、关键词搜索,处理空态和错误态。
  - 将 `get_yahoo_data` 接口或后端封装返回的指数数据转换为前端时序 JSON(日期、收盘价、成交量),驱动价格曲线与信号点;确保索引视图与新闻视图可以解耦切换。
  - 集成国际化(优先 next-intl)以中英文切换;默认中文。
  - 当数据延迟 > 120 秒时显示黄色提醒条,并允许用户手动刷新缓存。

- **验收**
  - ✅ 交互增强完成:新增时间范围(1H/6H/24H/All)、关键词搜索、手动刷新按钮与空态/错误态展示;实时状态栏会在 120s 无更新或连接错误时提示并提供刷新操作。
  - ✅ Demo 数据回退:若未配置 `NEXT_PUBLIC_NEWS_STREAM_ENDPOINT`,自动注入委内瑞拉示例(含链式推理、引用、信号),同时保留对真实 SSE/信号 API 的兼容。
  - ✅ 简易国际化完成:实现自定义 `useIntl` 上下文,默认中文,可在页面内切换中英,核心文案均通过 `t(key)` 渲染。
  - 待完成:使用 mock server 录制 SSE 推送演示视频并归档至 `docs/review_logs/step6.md`;Stage 1 QA checklist 需在后续前后端联调后勾选。

### 阶段 7 · 视觉打磨与动效优化(T+0.5 天)

- **主要任务**
  - 调整 Tailwind Theme Token,确保整体视觉既保留 nof1.ai 灵感又符合 TradingView/Bloomberg 的专业配色(亚蓝/琥珀强调、终端绿红涨跌),并适配国内阅读习惯(字号、行距、字重)。
  - 增加渐入、背景脉冲等动效,并支持 `prefers-reduced-motion`。

- **验收**
  - Lighthouse 暗色模式评分 ≥ 90,CLS < 0.1,前后对比截图归档。
  - UI 最终截图文档 `docs/review_logs/step7.md`,设计负责人签字确认。

### 阶段 8 · 性能与可观察性(T+0.5 天)

- **主要任务**
  - 集成前端埋点(Convex/Logfire),记录首包时间、SSE 重连次数、错误码分布。
  - 使用 React Profiler 确保关键交互渲染耗时 < 16ms。

- **验收**
  - 输出性能报告与埋点事件表(CSV/Markdown)至 `docs/metrics/`。
  - 前端埋点联通测试(抓包或日志截图)写入验收文档。

### 阶段 9 · 测试、合规审核与上线(T+1 天)

- **主要任务**
  - Playwright 端到端脚本覆盖:首屏加载、实时推送、过滤器、引用跳转、断线重连。
  - 合规检查:免责声明位置、用户协议/隐私政策链接、敏感词演示流程。
  - 组织产品 + 合规 + 技术联合验收会议。

- **验收**
  - `pnpm build --filter web`、`pnpm test --filter web` 全部通过;生成物截图归档。
  - Playwright 录屏与测试报告保存在 `tests/e2e/outputs/`;会议纪要归档。

### 阶段 10 · 发布、监控上线与复盘(T+0.5 天)

- **主要任务**
  - 部署至中国区生产环境(如阿里云、国内版 Vercel),配置 CDN 与 HTTPS。
  - 上线后 24 小时内持续监控 SSE 错误率、页面流量、关键性能指标;准备回滚方案。
  - 召开事后复盘会议,沉淀下一轮迭代表。

- **验收**
  - 上线 checklist(含回滚指引)存于 `docs/release/launch_checklist.md`。
  - 复盘文档记录亮点、问题与后续行动项,明确负责人和截止时间。

---

## 里程碑时间表(可依资源调整)

| 阶段 | 估算工期 | 责任人 | 计划完成日 | 验收状态 |
|------|----------|--------|------------|----------|
| 1 | 1 天 | 需求/Product | YYYY-MM-DD | ☐ |
| 2 | 1.5 天 | 设计 | YYYY-MM-DD | ☐ |
| 3 | 2 天 | 后端/数据 | YYYY-MM-DD | ☐ |
| 4 | 1 天 | 前端 | YYYY-MM-DD | ☐ |
| 5 | 2 天 | 前端 | YYYY-MM-DD | ☐ |
| 6 | 1 天 | 前端 | YYYY-MM-DD | ☐ |
| 7 | 0.5 天 | 前端/设计 | YYYY-MM-DD | ☐ |
| 8 | 0.5 天 | 前端/数据 | YYYY-MM-DD | ☐ |
| 9 | 1 天 | QA/合规 | YYYY-MM-DD | ☐ |
| 10 | 0.5 天 | 运维/产品 | YYYY-MM-DD | ☐ |

> 执行过程中,请在每阶段完成后填写实际日期、结果链接,并在验收栏打勾;若未通过需备注原因与下一步补救计划。

---

## 关键风险与预案

- **数据源波动**:对接多源备份(FMP、华尔街见闻、本地缓存);如主源失效,SSE 以缓存降级,并在 UI 通过红色 Banner 提醒。
- **合规审查**:上线前由法务审核敏感词库、引用来源,确保内容不违反国内监管要求;日志保留不少于 180 天。
- **性能压力**:预估高并发时的 SSE 会话数,若超出 FastAPI 单实例承载,启用多副本 + Redis Pub/Sub 广播。
- **LLM 成本**:链式推理使用分级策略(重点新闻实时、长尾按需生成),提供手动刷新按钮,避免重复调用。
- **信号映射错误**:若买/卖点与新闻 ID 不匹配会破坏体验;需在后端额外单元测试校验 `signalId -> newsId` 映射,并在前端添加异常 fallback(提示"新闻加载失败")。
- **数据库压力**:高频行情与新闻写入需关注 ClickHouse 分区及 Timescale hypertable 配置;必要时引入数据归档策略防止磁盘膨胀。

---

## 后续扩展规划(阶段 11+)

### 阶段 11 · AI 价格预测界面(T+3 天)

- **目标**:为用户提供标的级别的 AI 买卖建议与完整推理链。
- **主要任务**
  - 后端:新增 `/api/price/advice`(返回 K 线数据、AI 买卖建议、推理链、tech index 指标),同步写入 TimescaleDB。
  - 前端:在 `frontend/web/app/price-advisor/` 创建页面,展示新闻列表(对标的过滤)、AI 买卖意见卡片、K 线图(ECharts/TradingView API)与推理抽屉。
  - 引入 `Tech Index` 指标模块,聚合 supply/demand/inventory 等因子,映射到择时判断。
- **验收**:K 线与买卖点位同步显示,AI 总结支持链式推理分步查看;数据来自实时 API 与数据库缓存。

### 阶段 12 · 多因子仪表盘(T+2 天)

- **目标**:为单个标的提供因子仪表盘视图。
- **主要任务**
  - 数据:在 Timescale/ClickHouse 设计 `factor_metrics` 表,存储因子取值与时间序列。
  - 前端:构建 `frontend/web/app/factors/[symbol]/page.tsx`,使用雷达图/条形图/热力图展示因子强弱;支持切换时间周期。
  - 状态:复用 TanStack Query + Zustand 管理因子数据缓存。
- **验收**:仪表盘响应 3 秒内渲染完成;因子说明与链接可跳转到相关新闻/推理。

### 阶段 13 · 黑天鹅预警系统(T+3 天)

- **目标**:识别潜在黑天鹅事件并可视化推导路径。
- **主要任务**
  - 数据:配置 Kafka topic `alerts.black_swan`,由后端任务消费并写入预警表;ClickHouse 物化视图聚合预警概率。
  - 后端 API:`/api/alerts/black-swan` 返回等级(1-5)与推断树节点(每节点对应金融指标/数据源)。
  - 前端:在 `frontend/web/app/black-swan/` 使用树图/力导向图展示推断链,节点可展开查看指标详情。
  - 合规:对高风险事件提供人工审核入口。
- **验收**:树图在桌面端 60fps 内渲染;移动端提供简化列表;预警日志持久化并可追溯。

### 阶段 14 · 用户假设推理与互动(T+1.5 天)

- **目标**:允许用户输入自定义假设,实时查看 AI 推理结果(利多/利空)。
- **主要任务**
  - 后端:实现 `/api/hypothesis/run`,调用 LangGraph Agent,记录推理步骤到 Redis(用于 SSE 推送)并写入 PostgreSQL。
  - 前端:在新闻与价格预测界面提供输入组件,实时展示"假设推理轨迹"时间轴。
  - 评价机制:附带反馈按钮,做强化学习信号采集。
- **验收**:假设推理 3 秒内开始输出;推理链条支持逐步流式展示。

---

## 附录 · nof1.ai 风格拆解(仅供设计参照)

- **资源位置**:仓库根目录的 `nof1_ai_home.html`、`nof1_style1.css`、`nof1_style2.css`,仅用于提炼设计语言,禁止直接复制原站文案或素材。
- **核心特征**
  - 字体:IBM Plex Mono 等宽风格;国内上线需在 Tailwind 主题中加入思源黑体等中文 fallback。
  - 色板:暗色背景/1px 黑色边框、蓝/紫/绿/橙霓虹渐变;根据国内用户习惯适当提升对比度。
  - 组件语汇:终端风按钮、右侧信息终端、细滚动条;应抽象为 `terminal-card`、`terminal-badge` 等自定义组件。
- **交互动效**:hover 边框发光、状态闪烁等;实现时需兼容 `prefers-reduced-motion` 并提供触屏反馈。
- **合规提醒**:在 Figma/文档中注明"灵感来源",确保最终视觉实现为自主创作。

---

## 修订记录

| 日期 | 版本 | 说明 | 编辑人 |
|------|------|------|--------|
| YYYY-MM-DD | v1.0 | 初版计划,覆盖阶段 1-10 与验收标准 | GPT-Assist |