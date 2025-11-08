# CTP 实时 K 线方案（数据源可行性与实施计划）

> 目标：以 CTP 提供的行情数据为核心，构建一套基于 TradingView lightweight‑charts 的实时 K 线系统，稳定展示最新 6 个合约（CL2512、CL2601‑CL2605）。方案需兼顾指标叠加、周期切换、系列比较、Ringshell 水印、信号联动等一系列增强功能。

---

## 1. 数据流与存储

| 模块 | 现状 | 改造方案 |
| --- | --- | --- |
| **CTP Tick 拉取** | 仅有 `/md/tick/{instrument_id}` 单笔接口 | 新建后台 Aggregator：周期性（≤1s）访问 `/md/ticks?ids=...`（可批量）并写入缓存 + 队列；如批量接口不存在，则多线程串行请求后合并 |
| **合约窗口** | 6 个 CL 合约手动配置 | 通过 `generateContractIds()` 实时生成 `n=12` 的候选列表；过滤已过期合约，保证前端总能取到 6 条最新 |
| **历史 OHLC** | AlphaVantage 日线 | 后端新增 `bar_builder`：以 tick 流为输入，生成 1m/5m/15m/1h/1d bar（Kafka/Redis 事件 + Postgres/ClickHouse 存储）；若短期无法落库，可在内存中维护最近 N 分钟 bar，并周期落盘 |
| **指标/信号** | ML 均线、布林等依赖历史数据 | 解析 `INDEX1.xlsx` 为指标配置（JSON/CSV），后台定时计算/缓存；输出统一 `indicatorSeries`（timestamp,value） |
| **API** | `/api/pricing/kline` 返回 Alpha 数据 | 新增 `/api/ctp/kline`：返回 bar 数据 + 指标 + 实时信号；保持字段与前端类型兼容，便于渐进迁移 |

### 数据结构示例
```jsonc
{
  "symbol": "CL2512-NYM",
  "bars": [{ "time": 1731042000, "open": 78.1, "high": 79.2, "low": 77.8, "close": 78.76, "volume": 12039 }],
  "indicators": {
    "ml_ma": [{ "time": 1731042000, "value": 77.3 }],
    "boll_upper": [],
    "...": []
  },
  "signals": [
    { "time": 1731042300, "type": "bearish", "confidence": 0.78, "text": "BEARISH trend..." }
  ],
  "realtime": {
    "bid": 78.70,
    "bidSize": 12,
    "ask": 78.80,
    "askSize": 15,
    "last": 78.76,
    "lastUpdate": "2025-11-08T11:40:00Z"
  }
}
```

### 1.1 实时刷新验证

为确认 `md/tick` 的刷新频率，新增采样脚本 `scripts/ctp_tick_probe.py`，以 1 秒周期抓取 6 次：

```bash
python scripts/ctp_tick_probe.py CL2512-NYM 6 1
```

输出示例：

```
{'local_time': '20:09:13', 'update_time': '06:00:00', 'update_millisec': 830, 'last_price': 59.84}
...
20:09:17 -> update 06:00:00.830 price 59.84
```

**结论**：接口可被高频访问，但在无成交变化时返回同一笔（`update_time` 未变）。因此：

1. 仍需按 ≥1 秒频率采集，确保任何跳变都被记录；
2. 采集器需将 `local_time` 与 `update_time` 同时落库，方便后续分析延迟；
3. 与 CTP 供应商确认是否提供推送式接口（WebSocket）以减轻轮询压力。

---

## 2. 前端总体结构

### 2.1 状态管理
- `contractsStore`（Zustand）：维护最新 6 个合约、前一版本 tick、更新状态。
- `chartStore`: 记录当前合约、比较系列、周期、指标开关、信号过滤等。
- React Query 对 `/api/ctp/kline`、`/api/ctp/realtime` 做轮询与缓存，允许 fall‑back 到最后成功值。

### 2.2 组件划分
| 组件 | 说明 |
| --- | --- |
| `CtpRealtimePanel` | 左侧卡片，展示 6 个合约的 tick 信息（已在现有页面实现，可继续迭代） |
| `ChartShell` | 对 lightweight-charts 做统一封装：主题、尺寸响应式、Ringshell 水印、tooltip、自定义图层（**放置位置：新闻实时页现有 TradingView 区块下方、石油因子模块上方**） |
| `CtpKline` | 调用 ChartShell 渲染主 K 线、比较线、指标线、信号标记等；包含工具栏（周期、指标、比较、导出等） |
| `IndicatorPanel` | 解析 INDEX1 指标配置，提供开关、样式设置（颜色、Pane） |
| `SignalTimeline` | 图形下方列出信号列表，点击可定位到 chart marker |

### 2.3 TradingView lightweight‑charts 集成
1. 将 `C:\Users\juiceNo3\Downloads\lightweight-charts-master` 引入 workspace（如 `frontend/web/libs/lightweight-charts`）。
2. 在 `ChartShell` 中 `import { createChart } from "@/libs/lightweight-charts"`。
3. 自定义主题：背景、网格、刻度、十字线、tooltip 均使用 Ringshell 的中性配色。
4. Watermark：在 `chart.subscribeCrosshairMove` 或 `applyOptions` 中，利用 `paneWidget` 画自定义 canvas（`Ringshell • AI Markets`）。
5. 允许添加多 `series`：`candlestickSeries`、`baselineSeries`（比较）、`lineSeries`（指标）、`histogram`（成交流）、`series.createPriceLine`（基准线）。

---

## 3. 指标与信号（INDEX1.xlsx）

1. **预处理**：后端 cron 读取 `INDEX1.xlsx`，转换为 JSON：`[{symbol, timestamp, indicatorKey, value}]`。
2. **注册系统**：
   ```ts
   const indicatorRegistry = {
     ml_ma: { label: "ML 均线", type: "line", color: "#5B8FF9" },
     boll_upper: { label: "Boll 上轨", type: "line", color: "#FF7875" },
     spread_score: { label: "价差得分", type: "histogram", pane: "lower" },
     ...
   };
   ```
3. **渲染逻辑**：用户勾选 -> `ChartShell` 根据 type/pane 添加 series；指标值随 `/api/ctp/kline` 返回。
4. **信号联动**：`signals` 数组转为 `chartSeries.setMarkers()` 并在 SignalTimeline 中列出。点击 marker 可打开 Tooltip/Drawer 展示详细 AI 结论、置信度等。

---

## 4. 功能列表

| 功能 | 描述 |
| --- | --- |
| 周期切换器 | 支持 1m/5m/15m/1h/1d，切换时重新请求 `/api/ctp/kline?interval=` |
| 系列比较 | 在工具栏选择其他合约，添加 baseline/line 系列并同步 legend |
| 国际化 | labels 复用 `IntlContext`，中文/英文对映完整 |
| 信号过滤 | 按类型/置信度过滤 marker；勾选“仅显示 AI 结论/仅显示研判” |
| 自动刷新 | 显示 “上次更新（xx:xx） · 正在刷新/失败” 并允许手动刷新或暂停 |
| 截图导出 | 使用 `chart.takeScreenshot()` 或 `html2canvas` 输出 PNG |
| 快捷键 | 方向键切换合约/周期，`F` 聚焦最新，提升操控效率 |
| 性能优化 | 使用 `requestAnimationFrame` 去抖 resize，缓存 500 根以内数据，超出时裁剪 |

---

## 5. 实施步骤（细化）

### Phase A · 数据采集与 API（预计 3 天）
1. ✅ `ctp_sampler` Daemon：`scripts/ctp_collector.py` 已实现（支持动态合约、1s 轮询、失败告警、Kafka/CSV 输出、`--dry-run/--max-cycles` 调试参数）。后续可直接用于 Docker 部署或接 Kafka。
2. ✅ Docker 基础环境：新增 `Dockerfile.collector` 与 `docker-compose.ctp.yml`，本地一条命令即可启动 `zookeeper + kafka + clickhouse + collector`；准备好与生产环境一致的编排模板。
3. ✅ Kafka 写入链路：collector 以 6 合约窗口每秒推送 `ctp_ticks` topic，并附带 `local_time / update_time / bid/ask/last` 字段；通过 `docker compose -f docker-compose.ctp.yml exec kafka kafka-console-consumer ...` 已验证消息持续产出，报警逻辑也在脚本内记录连续失败。
4. ✅ ClickHouse 初始化 + 消费：`scripts/clickhouse_init.sql` 已在容器内执行完毕，`scripts/kafka_to_clickhouse.py` 现运行于 compose 网络中，`ctp.ctp_ticks` 行数持续增加，证明 Kafka→ClickHouse 写入闭环可用。
5. 设计 `ctp_bars_<interval>` 物化视图：按 1m/5m/15m/1h/1d 聚合 OHLCV，供 `/api/ctp/kline` 直接查询；如历史不足可先返回 mock 数据。

### Phase B · ChartShell & 前端基础（预计 4 天）
1. ✅ `ChartShell` 封装完成：基于本地 lightweight-charts 源码实现主题、Ringshell 水印、响应式、markers/多 series 及导出 API，供后续 K 线组件统一调用。
2. ✅ `CtpKlineCard`（mock 数据）已在新闻实时页 **TradingView 图块下方、石油因子上方** 渲染，默认提供周期/合约切换，并与 TradingView 并存，等待真实 `/api/ctp/kline` 数据接入。
3. ✅ 工具栏增强：新闻页中的 `CtpKlineCard` 现包含周期/合约切换、最后更新时间、手动 + 15s 自动刷新状态，方便在接入真数据前验证交互；ChartShell 已验证可同时绘制 K 线 + 叠加线。

### Phase C · 后端 API（预计 3 天）
1. 实现 `/api/ctp/kline`：参数 `symbol/interval/count`，查询 ClickHouse 的 bar + 指标表，返回统一结构。
2. 实现 `/api/ctp/realtime`：返回最新 tick（含盘口、信号），供左侧实时面板与 ChartShell tooltip 使用。
3. 增加缓存/速率限制/健康检查，确保前端高频轮询仍可承受。

### Phase D · 前端集成（预计 4 天）
1. `useCtpKline` hook：支持周期切换、比较系列、指标配置等功能。
2. 新的 ChartShell（lightweight-charts）在指定位置新增，与 TradingView 并存，附 Ringshell 水印、信号 marker、指标叠加、导出工具。
3. 侧栏/工具栏：实现周期切换器、合约比较、指标面板、信号过滤、自动刷新提示等交互。

### Phase E · 指标/信号（预计 3 天）
1. 解析 `INDEX1.xlsx` → JSON → 定时写入 ClickHouse `ctp_indicators` 表。
2. `/api/ctp/kline` 返回指标数据；前端 IndicatorPanel 控制显示/隐藏。
3. 信号 marker 与 SignalTimeline 联动，点击可定位并打开抽屉查看详情。

### Phase F · 测试与上线（预计 3 天）
1. 单元测试：Kafka/ClickHouse 写入链路、API 输出、前端 hooks & 组件 snapshot。
2. 性能压测：tick 采集、API 并发、ChartShell 多指标/比较系列情景。
3. 灰度上线：小流量验证 → 全量切换，AlphaVantage 作为可配置 fallback。

### DevOps & 部署备注
- 本地与服务器统一通过 `docker compose -f docker-compose.ctp.yml up -d` 启动 `zookeeper + kafka + clickhouse + collector + kafka_to_clickhouse`，确保开发 / 测试 / 线上环境一致；必要时脚本模式仅作单次诊断使用。
- `Dockerfile.collector` 直接封装守护进程（python:3.10-slim + requirements），后续上线可将同一镜像挂入 Compose/Swarm/K8s，并使用 `.env` 管理 CTP/Kafka/ClickHouse 的地址与凭证。
- CTP 服务已部署在外部服务器，经脚本与容器双重验证可稳定连接；在 Docker 环境只需配置正确 URL/Key，即可长期采集。

--- 

## 6. 风险 & 对策

| 风险 | 说明 | 对策 |
| --- | --- | --- |
| CTP 接口不可用 | 无历史、无批量 | 后端本地落库 + 缓存；必要时加入第三方备用数据源 |
| 指标计算成本高 | Excel 列表不断扩充 | 定期批处理 + 缓存，必要时拆分微服务 |
| TradingView 适配差异 | 本地 lightweight-charts 版本需升级 | 从官方 repo 引入最新版本，并编写封装防止 breaking changes |
| UI/性能 | 多 series 可能卡顿 | 限制最多 5 条指标 + 3 条比较，使用 `series.priceScale().applyOptions` 调优 |

---

## 7. 结论

- 以 lightweight-charts + CTP tick 构建全新 K 线系统是可行的，但需要 **后端数据累积** 与 **前端组件重构** 同步推进。  
- 短期可先落地 TradingView + 实时 tick 面板，中期逐步接入自建 bar & 指标，最终完全替换 AlphaVantage 依赖。  
- 本文所列的分阶段计划与组件设计，可直接作为实施蓝图。下一步即开始 Phase A，并为 Phase B/C 准备 mock 数据与 UI 原型。  
