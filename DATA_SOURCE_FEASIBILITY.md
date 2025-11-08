# 数据源替换可行性分析

## 背景

- 当前系统的 K 线与信号数据来源是 Alpha Vantage（以及基于其数据派生的指标），主要通过 `backend/src/financial/data_sources/price_data.py` 暴露的 `get_yahoo_data_comprehensive`，再由 `backend/src/api/pricing.py` 聚合成 `/api/pricing/kline` 的响应，供前端 `usePricingKline` 钩子与 `KLineChart` 组件使用。
- 计划将数据源迁移到自建的行情接口 `http://47.108.177.50:8080/md/tick/<instrument_id>`，并希望在前端改用更高级的 TradingView 嵌入图表。

## 现状概述

### 前端（Next.js）
- `frontend/web/lib/hooks/usePricingKline.ts`：调用 `PRICING_KLINE_ENDPOINT`（默认 `/api/pricing/kline`）获取 180 天左右的 OHLC、ML 均线、信号数据，并转换为 K 线图所需的 `CandlestickPoint`、`LinePoint`、`VolumePoint`。
- `frontend/web/components/charts/KLineChart.tsx`：基于 lightweight-charts 渲染本地 K 线图，展示价格、成交量、ML 信号，支持点击信号点联动新闻抽屉。
- `frontend/web/app/news/real-time/page.tsx`：实时新闻页面复用上述 hook/组件，因此任何数据协议变动会直接影响该页面。

### 后端（FastAPI）
- `backend/src/api/pricing.py`：`/api/pricing/kline` 请求参数 `ticker`、`days`，流程：
  1. 调用 `get_yahoo_data_comprehensive` 获得最近若干天的日线数据。
  2. 将 pandas DataFrame 输入多个指标函数（布林、RSI、ML Moving Average 等），生成 `PricingKlineResponse`。
  3. 返回的数据结构与前端类型定义 `frontend/web/lib/api/pricing.ts` 匹配。
- `backend/src/financial/data_sources/price_data.py`：封装 Alpha Vantage 请求、缓存、数据清洗、OHLC 正规化。
- 额外还有 `backend/src/news/service.py` 依赖 Alpha Vantage 进行新闻抓取，但与 K 线功能耦合较低，只需在计划中记录未来是否也切源。

## 新信号 API 概述

- 调用方式：`GET http://47.108.177.50:8080/md/tick/{instrument_id}`。
- 样例（CL2512-NYM）：

```json
{
  "ok": true,
  "instrument_id": "CL2512-NYM",
  "last_price": 59.84,
  "volume": 230336,
  "trading_day": "20251107",
  "update_time": "06:00:00",
  "update_millisec": 830,
  "bid_price1": 59.8,
  "bid_volume1": 2,
  "ask_price1": 59.85,
  "ask_volume1": 5
}
```

- 特点：返回单个最新 tick（成交价、盘口一档、成交量、交易日时间戳）。接口未包含历史 OHLC 列表、也未提供批量/分页参数。

## 差异与影响

| 维度 | 现有 Alpha Vantage 流程 | 新信号 API | 影响 |
| --- | --- | --- | --- |
| 数据粒度 | 日线 OHLC（可达 500 根） | 单个实时 tick | 需要自行滚动聚合为 K 线，无法直接生成历史曲线 |
| 指标依赖 | ML 均线、布林、RSI 等全部基于 OHLC 序列 | 暂无历史序列 | `ml_moving_average_tool` 等无法运行，相关信号需重写或改用外部图表 |
| 访问频率 | 受 Alpha Vantage 限频，需缓存 | 自建 API，可高频轮询 | 需评估服务器承载量、是否支持 WebSocket/push |
| 认证/配置 | 依赖 API KEY，环境变量管理 | 当前示例无鉴权 | 若未来加鉴权需新增配置与 Secrets 管理 |
| 前端适配 | 依赖本地 API，返回结构固定 | 计划改用 TradingView + 自建 API | 需拆分：TradingView 负责展示，React 状态负责信号/新闻联动 |

## 可行性分析

1. **维持现有 `/api/pricing/kline` 协议的难度高**  
   - 需要从 tick 数据自建一个历史数据库（例如将实时 tick 写入 Redis/Kafka/Postgres，再用批处理生成 1m/5m/1h/1d bar）。  
   - 指标计算、信号提取、ML 模型需要完整的时间序列输入。若只替换数据源而不改架构，现有函数无法工作。

2. **改用 TradingView 嵌入图表的可行性高**  
   - TradingView Advanced Chart 自带历史数据与指标，前端可直接嵌入，减轻后端生成 K 线的负担。  
   - 需要接受 TradingView 的数据来源（与自建信号不同步），若想展示自建信号，需要额外在图表外叠加 UI。

3. **折中方案**  
   - 短期：在新闻页引入 TradingView 组件展示行情；并在页面其他区域显示自建 API 返回的最新 tick、盘口、信号文案。  
   - 中期：在后端新增 `md/tick` 代理与缓存，把多个合约的实时数据写入数据库，积累至少 30~180 天的历史，再恢复自研指标链条。  
   - 长期：若要完全摆脱 TradingView，需要实现：数据落库 + bar 生成 + 指标/信号计算 + `/api/pricing/kline` 重构。

## 建议的改造步骤

1. **后端最小接入**
   - 新增 `backend/src/financial/data_sources/tick_api.py`，负责请求 `md/tick`、异常处理、缓存（例如 1 秒内命中内存）。  
   - 暴露新的 `/api/pricing/tick` 或 `/api/markets/realtime`，为前端提供最新价格、盘口、更新时间等字段。  
   - 在 `.env` 中新增 `MD_TICK_BASE_URL`，方便切换环境。

2. **前端改造**
   - 在 `frontend/web/components/charts` 新增 `TradingViewWidget.tsx`（用户提供代码），通过动态导入避免 SSR。  
   - 新闻页中用条件渲染：如果启用 TradingView，则隐藏原 `KLineChart`，同时在侧边卡片展示自建信号（可继续用 `usePricingKline` 的结构，但数据来自新 API）。

3. **数据累计与指标迁移（中期）**
   - 构建一个简单的 cron/worker，将 tick 写入持久化存储，再按 1 分钟/5 分钟/日聚合成 OHLC。  
   - 修改 `get_yahoo_data_comprehensive` 的实现：优先读取自建数据，如果缺失再回退 Alpha Vantage；完成后可以删除旧依赖。  
   - 复用现有指标函数，确保输出仍兼容 `PricingKlineResponse`，以便前端未来可以重新使用本地 lightweight-charts。

4. **测试与回归**
   - 单元测试：为新的数据源封装编写快照，验证空数据、超时、字段缺失等情况。  
   - 前端：对新闻页、油品信号页做截图/交互测试，确认 TradingView 加载与自建信号联动正常。  
   - 性能：压测 `md/tick` 代理接口，确保 QPS、延迟符合需求。

## 风险与注意事项

- **数据一致性**：TradingView 的行情与自建 API 可能出现价差，需要在 UI 中提示“图表数据来源于 TradingView，信号来源于自建 API”。  
- **实时性**：`md/tick` 返回的 `update_time` 精确到毫秒，需要考虑时区（返回看似是交易所本地时间）。建议在后端统一转换为 ISO8601。  
- **可用性**：目前接口无鉴权，若对外网开放可能有滥用风险。建议预留 token 或 IP 白名单机制。  
- **依赖拆分**：新闻服务、其他指标也可能引用 Alpha Vantage，迁移时需列出完整清单，避免遗漏导致运行时错误。

## 下一步建议

1. 确定阶段性目标：是先上 TradingView + 实时 tick 面板，还是同步搭建历史库。
2. 如果采用 TradingView，确定需要展示的合约列表、默认 symbol、样式主题，并封装配置为环境变量。
3. 设计 `md/tick` 的缓存/聚合策略，明确需要的历史长度和存储方案。
4. 为上述改造创建任务拆分（前端、后端、基础设施），并安排测试计划。

