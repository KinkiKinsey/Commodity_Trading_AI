# Ringshell_AI 项目实施文档

> 版本：2025-10-15  
> 维护人：Ringshell AI 工程团队

---

## 1. 项目概述

Ringshell Agent 旨在构建一个面向大宗商品（尤其是原油期货）的智能因子洞察与实时信息分析平台。系统整合结构化行情、非结构化新闻、LLM 推理和量化指标，为交易与研究团队提供「因子影响度量」「黑天鹅预警」「实时新闻板」「多因子仪表盘」等关键能力。

本文件覆盖当前代码仓库结构、目标功能、端到端数据流、关键模块设计、部署运维方案以及迭代路线图，作为团队协同的统一参考。

---

## 2. 业务目标与价值

- **实时捕捉市场驱动力**：分钟级行情与新闻数据实时拉取、加工，支持用户在多终端查看趋势和因子变化。
- **可解释的因子分析**：通过 LLM + 量化模型输出因子影响权重、时间区间、趋势摘要，为交易决策提供透明依据。
- **黑天鹅预警能力**：针对突发事件的评估与推演，结合历史案例和指标体系，提示潜在风险。
- **交互式前端体验**：复用现有小程序/网页前端，提供多周期 K 线、因子仪表盘、推理链可视化。
- **可扩展的数据基础设施**：利用 Kafka + ClickHouse/Redis 处理实时与历史数据，支持未来多品种和多团队协作。

---

## 3. 系统架构总览

```
┌──────────────┐       ┌────────────────────┐
│ 外部数据源   │       │ 第三方服务         │
│ - 行情 API   │       │ - DeepSeek/OpenAI  │
│ - 新闻 FMP   │       │ - Convex Middleware │
└──────┬───────┘       └─────────┬──────────┘
        │                         │
        ▼                         ▼
┌────────────────────────────────────────┐
│ 采集层                                 │
│ - Kafka/Ticker Ingestor                │
│ - ClickHouse Raw Tables                │
│ - Redis Caching                        │
└────────┬──────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ 数据与模型计算层                        │
│ - Data_Source (行情+新闻)               │
│ - LLM_Source (LLM 调度)                 │
│ - LLM_Trend_Summary (趋势 JSON)        │
│ - Oil_Impact_Metrics & Incremental     │
│ - Tech_Index 指标库                     │
└────────┬──────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ API 服务层                             │
│ - FastAPI 服务：/api/price /api/factors│
│ - WebSocket/SSE 实时推送                │
│ - Convex/中间件整合                     │
└────────┬──────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ 前端与客户端                            │
│ - 小程序因子表盘                        │
│ - Web 仪表盘 (Driven.ai 类交互)         │
│ - 内部运营后台                          │
└────────────────────────────────────────┘
```

### 3.1 前端技术选型

- **Web 主站（桌面/移动）**：TypeScript + React 18，采用 Next.js 14 App Router（SSR + ISR）提升首屏速度与 SEO；UI 层统一使用 Ant Design Pro + Tailwind，图表体系基于 Apache ECharts（K 线、指标叠加、热力图）封装可复用组件。
- **小程序端**：基于 Taro（React 语法）输出微信/企业微信版本，复用核心状态与数据访问逻辑；图表选用 F2/AntV-Lite 以适配小程序渲染性能。
- **状态管理与通信**：Zustand 管理局部状态，TanStack Query 负责接口数据缓存与失效刷新，结合 SSE/WebSocket 获取实时行情。
- **工程体系**：pnpm + Turborepo 管理 web、mini-program、组件库三套包，统一 ESLint/Prettier/Jest 配置；CI 阶段执行 `pnpm lint && pnpm test --filter web`。

### 3.2 后端技术选型

- **核心框架**：Python 3.11 + FastAPI（Uvicorn/Gunicorn）提供 REST/SSE/WebSocket 服务，`fastapi-cache` + Redis 支撑多语言缓存。
- **数据访问层**：SQLModel/SQLAlchemy 统一 ClickHouse、Redis、对象存储访问；Pydantic v2 校验外部行情与新闻字段。
- **任务编排与流式处理**：Kafka + Faust/Bytewax 计算实时指标，APScheduler/Celery 承担 LLM 推理、增量回填等异步任务。
- **鉴权与网关**：内部 OAuth2 + JWT；外部请求经由 Kong/阿里云 API 网关做限流、签名校验与审计。

### 3.3 数据与模型服务

- **LLM 接入策略**：优先 DeepSeek-R1、智谱 GLM API；保留 OpenAI 兼容层以支持海外部署，必要时切换本地 vLLM/通义千问推理服务。
- **特征与向量存储**：Milvus/PGVector 存放新闻嵌入用于相似事件召回，ClickHouse `analytics.factors_snapshot` 存历史因子序列。
- **可观测性链路**：Prometheus + Grafana 监控核心服务指标，OpenTelemetry 收集链路耗时；LLM 调用日志写入 ClickHouse `analytics.llm_calls` 以便成本追踪。

---

## 4. 数据流详解

### 4.1 行情采集与存储
1. **Ingestor 服务**（24/7 云机）：按 5/15/60/240/1D 周期从外部 API 拉取数据，写入 Kafka Topic（按品种 + 周期划分）。
2. **Kafka → ClickHouse**：使用 Materialized View 将消息落地到 `market_data.ohlcv_{interval}` 表，保留原始 tick 7 天，多周期 K 线 30+ 天。
3. **Redis 缓存**：最近一小时关键行情写入 Redis，提供超低延迟访问；失效后回查 ClickHouse。

### 4.2 新闻与文本数据
1. 调用 FinancialModelingPrep 新闻接口获取 WTI 相关新闻。
2. 存储原始新闻 JSON 到 ClickHouse/对象存储，同时写入 Redis 用于短期复用。
3. `LLM_Trend_Summary` 对新闻按日期过滤，结合行情数据构建 LLM Prompt。

### 4.3 因子影响流水线
1. `get_factor_metrics` 检查 Redis 缓存是否在 7 天内；命中则直接返回。
2. 若缓存 stale：  
   - 调用 `LLM_Trend_Summary.get_llm_trend_summary` → 输出趋势段的 JSON（Uptrend/Downtrend，含新闻、统计信息）。  
   - 结果送入 `Oil_Impact_Metrics.get_oil_impact_from_existing_trends`，生成因子权重表、时间区间表。  
   - `Oil_Incremental_Update` 将新旧数据合并，并更新 Redis/ClickHouse 快照。
3. 返回 pandas DataFrame（impact_metrics_df / factor_time_df），供 API 层或 notebook 使用。

### 4.4 技术指标计算
1. 前端或 API 请求 `Tech_Index` 模块，如 `rsi.py`, `bollinger.py`, `liquidity.py`。
2. 指标模块从 ClickHouse 获取相应周期的 OHLCV 数据，输出信号、图表数据和文本解释。

---

## 5. 模块与目录说明

| 模块 | 路径 | 功能摘要 | 当前状态 |
|------|------|----------|----------|
| DataBase_Connection_Source | `RedisDatabaseStorage.py` | Redis 读写封装；支持 JSON / CSV / Text | 密钥硬编码，需迁移至 `.env` |
| Data_Source | `wti_news.py`, *(待补 `get_price.py`)* | 新闻采集、行情接口 | 行情模块缺失，需接入新 API |
| oil_factors_metrics | `get_factor_metrics.py` 等 | 核心因子流水线 | 可运行但依赖缺失模块 |
| Tech_Index | 各指标脚本 | RSI、Bollinger、RBF 等计算与解释 | 新增，尚未接入主 API |
| API 层 | *(待建)* | FastAPI/Convex 服务，封装数据接口 | 未实现 |
| 前端 | *(外部仓库/小程序)* | 因子表盘、黑天鹅预警、新闻板等 | 现成 UI，可复用 |

---

## 6. 数据存储与缓存策略

- **ClickHouse**：主时序数据库，建议表结构：
  - `market_data.ohlcv_{interval}`（ticker, interval, open, high, low, close, volume, ts）
  - `market_data.trend_snapshot`（ticker, run_id, trend_json, created_at）
  - `analytics.factors_snapshot`（ticker, run_id, macro_factors, micro_factors, beta, language, created_at）
- **Redis**：低延迟缓存；key 命名规范 `Crude_Oil:Future_Contract:{ticker}:{Dataset}`。
- **对象存储/OSS**（可选）：存放大体积 LLM 原始回答或附件。
- **Kafka**：实时数据管道，Topic 命名 `market.{ticker}.{interval}`。

---

## 7. 实时数据服务设计

- **采集守护进程**：Python/Go 脚本部署于云主机，使用 Async I/O 并发请求 API，失败自动退避重试。
- **调度策略**：
  - 高频（5s/10s）请求当前价，写入 Redis + Kafka。
  - 批量（1/5/15/60 分钟）生成 K 线，合并到 ClickHouse。
- **推送机制**：
  - REST：`GET /api/price?ticker=CL&interval=5m&limit=600`
  - WebSocket/SSE：订阅 `price:{ticker}:{interval}` 主题，推送最新值。
  - 轮询 fallback：前端保留 5–10 秒轮询模式。

---

## 8. 应用层设计

### 8.1 API 端点草案

| 方法 | 路径 | 描述 | 形参 | 备注 |
|------|------|------|------|------|
| GET | `/api/price` | 获取 OHLCV + summary | `ticker, days` | 返回时间序列 + 涨跌摘要 |
| GET | `/api/factors` | 因子权重 + 窗口 | `ticker, language, force_refresh` | 返回权重、方向、窗口摘要 |
| GET | `/api/news` | 新闻流 + 情绪标签 | `ticker, days, limit, offset, source, keyword` | 返回分页新闻 + 情绪 |
| GET | `/api/alerts` | 黑天鹅预警列表 | `ticker, severity` | 来自 LLM + 指标推理 |
| POST | `/api/assumptions` | 用户自定义假设推理 | `ticker, hypothesis` | 返回推理链、利多/利空 |

### 8.2 前端交互重点

- **因子仪表盘**：从 `/api/factors` 获取 macro/micro 因子，展示权重、风险回报、时间范围。支持点击弹窗（参考截图）显示时间轴。
- **实时新闻板**：拉取 `/api/news`，显示过滤后的新闻列表、利多/利空标签及 LLM 推理链。
- **价格预测界面**：请求 `/api/price` + `Tech_Index` 指标接口，展示多周期 K 线、买卖建议、图表注释。
- **黑天鹅预警**：订阅 `/api/alerts`，以树状图或流程图展示事件传播链路及概率等级。


### 8.3 前端交互规划（参考 Driven.ai）

- **价格总览卡片**：主屏呈现最新收盘价、涨跌幅、区间高低点，直接对应 `/api/price` 的 `summary` 字段。
- **多周期切换**：提供 7D/30D/90D/1Y tabs，前端根据用户选择调整 `days` 参数并重新拉取数据。
- **组合图层**：蜡烛图 + 成交量柱状图、移动均线叠加（未来由 `Tech_Index` API 提供），交互模式参考 Driven.ai 的 hover tooltip 与区间缩放。
- **情绪与事件联动**：列表展示 `/api/news`、`/api/alerts` 数据，选中后在图表上高亮对应日期节点，增强事件溯源能力。
- **因子瀑布图**：使用 `/api/factors` 的 `factors` 列表绘制正负向权重瀑布图，突出关键驱动；hover 展示 `commentary` 文字。
- **区间故事线**：基于 `windows` 数组渲染时间轴卡片，用户点击时联动价格图定位对应区间。
- **小程序适配**：沿用 Driven.ai 卡片分区布局，底部保留操作按钮（收藏、订阅预警），Taro 层通过 TanStack Query 缓存请求并下拉刷新。
---

- **新闻流情绪标签**：右侧新闻栏展示自 `/api/news` 获取的 sentiment chips（红/绿/灰），点击同步高亮价格曲线节点并展开全文。
## 9. 环境与配置管理

- 使用 `.env`/Secrets Manager 管理以下关键变量：
  - `REDIS_URL`, `REDIS_USERNAME`, `REDIS_PASSWORD`
  - `RINGSHELL_FMP_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`
  - `CLICKHOUSE_DSN`, `KAFKA_BROKERS`
- `settings.py` 或 Pydantic `BaseSettings` 统一加载配置，杜绝硬编码。
- 区分环境（local / staging / prod），通过 `.env.{env}` 或环境变量切换。

---

## 10. 安全与合规

- **凭据管理**：禁用硬编码；通过 CI 检查确保凭据未泄露。
- **网络访问控制**：API 服务部署时启用 IP 白名单或 OAuth，防止未经授权的调用。
- **数据合规**：确认外部 API 的使用条款（分钟级数据计费按天）；落地数据需遵守供应商许可。
- **日志脱敏**：日志中不得记录密钥、用户隐私数据。

---

## 11. 监控与运维

- **指标**：
  - 采集延迟、请求成功率、Redis 命中率、Kafka Lag、ClickHouse 写入失败数。
  - 因子流水线运行时长、LLM 调用耗时/成本。
- **工具**：Prometheus + Grafana，Sentry/Logfire 捕捉异常；Alertmanager 配置阈值告警。
- **备份策略**：ClickHouse 分区定期快照，Redis 采用 AOF/持久化；LLM 原始结果存储在对象存储防丢失。

---

## 12. 开发流程与测试

- **分支策略**：`main`（稳定）+ `feature/*`（开发），所有合并需经 PR Review。
- **测试体系**：
  - 单元测试：Redis 封装、行情拉取、指标计算、LLM 解析。
  - 集成测试：完整执行 `get_factor_metrics`，验证缓存/增量更新。
  - 合同测试：API 层通过 schema 校验，确保前后端一致。
- **CI/CD**：GitHub Actions 或自建 CI，执行 lint/test/docker build；通过后自动部署至 Cloud Run/Kubernetes。

---

## 13. 迭代路线图

| 阶段 | 时间 | 关键交付 |
|------|------|----------|
| **Phase 0** 配置梳理 | Week 0-1 | `.env` 接管、Redis 封装修复、基础单测 |
| **Phase 1** 行情基础 | Week 1-3 | 行情采集服务、Kafka→ClickHouse、Redis 缓存策略 |
| **Phase 2** 因子稳态 | Week 3-5 | 完整 `get_factor_metrics`、增量更新、日志化 |
| **Phase 3** 技术指标整合 | Week 4-6 | Tech_Index 接入、统一数据访问层 |
| **Phase 4** API & 实时服务 | Week 6-8 | FastAPI/WebSocket、黑天鹅预警端点 |
| **Phase 5** 前端联调 | Week 8-9 | 小程序/网页接入，Demo 可交付 |
| **Phase 6** 商业化准备 | Week 9-10 | Pitch Demo、运营文档、监控上线 |

---

## 14. 附录

### 14.1 关键文件索引
- `Ringshell_source_code/oil_factors_metrics/get_factor_metrics.py` – 因子流水线入口
- `Ringshell_source_code/oil_factors_metrics/LLM_Trend_Summary.py` – 趋势生成
- `Ringshell_source_code/oil_factors_metrics/Oil_Impact_Metrics.py` – 因子权重计算
- `Ringshell_source_code/oil_factors_metrics/Oil_Incremental_Update.py` – 增量更新
- `Ringshell_source_code/DataBase_Connection_Source/RedisDatabaseStorage.py` – Redis 封装
- `Ringshell_source_code/Tech_Index/` – 技术指标合集

### 14.2 术语表
- **LLM**：Large Language Model，大型语言模型。
- **ClickHouse**：列式数据库，适合时序与分析场景。
- **Kafka**：分布式消息队列，用于实时数据流传输。
- **SSE**：Server-Sent Events，服务端推送机制。
- **Convex**：Serverless 数据层，用于快速构建实时应用。

---

## 15. 国内部署适配方案

- **云资源与网络**：首选阿里云（ACK/Serverless K8s）或腾讯云（TKE + ECI）部署采集、计算、API 服务，使用专有网络（VPC）隔离生产环境；前端静态资源放置 OSS + CDN 并全站开启 HTTPS。
- **域名备案**：自研域名完成 ICP 备案，API 与前端域名拆分；若面向企业客户，同时提交公安机关网安备案。
- **第三方依赖替换**：引入金融数据源国内镜像（和讯、Wind 备选），LLM 调用优先 DeepSeek/智谱；热点新闻缓存 24h 减少跨境访问。
- **合规与日志**：关键访问日志接入阿里云日志服务或腾讯云 CLS，保存不少于 180 天；Kafka/ClickHouse 数据落地国内可用区，敏感字段按等保二级要求脱敏。
- **高可用与容灾**：核心服务部署多可用区副本，Redis 主从 + 哨兵，ClickHouse 使用 ReplicatedMergeTree；每周执行冷备份（OSS + 跨区域）。

---

## 16. 后续功能扩展规划

- **多资产扩展**：抽象行情采集与因子框架，逐步支持有色金属、化工与股指期货。
- **交易执行闭环**：对接易盛、直达期货等交易接口，记录策略执行与成交反馈。
- **协同工作台**：增加研报协作、标签评论、事件订阅推送（企业微信/钉钉 Bot）。
- **模型迭代**：上线自监督摘要与风控评分模型，使用 A/B Test + 回测评估准确率。
- **数据产品化**：开放 API Key 管理和调用额度计费，面向外部研究团队提供 SaaS 化服务。

---


如对本文档有补充或更新需求，请在仓库提交 PR 或联系项目维护人。


## 17. 前端开发环境

- 目录结构：`package.json` + `pnpm-workspace.yaml` 管理 `frontend/web` 应用，遵循 Next.js 14 App Router + Tailwind + React Query。
- 安装依赖：`pnpm install`（建议使用 `pnpm@9`），进入子项目运行 `pnpm dev --filter web` 启动本地调试，默认访问 `http://localhost:3000`。
- 环境变量：在 `frontend/web` 下创建 `.env.local`，配置 `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`，可根据部署环境切换。
- 数据流：页面初始加载同时请求 `/api/price` `/api/factors` `/api/news`，客户端用 React Query 支持多周期切换与自动刷新。
- UI 约束：遵循 Driven.ai 风格，价格区块 + 因子瀑布 + 新闻情绪标签，后续可在 `components/` 中扩展图表/交互。
