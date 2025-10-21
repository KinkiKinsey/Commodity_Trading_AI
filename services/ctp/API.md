# CTP Service API Documentation

## 🎯 概述

CTP Service 提供了一个简洁的 REST API 来访问 CTP（China Trading Platform）的市场数据和合约信息。

**核心特性**：
- ✅ **只登录一次**：守护进程保持长连接，避免重复登录
- ✅ **自动订阅**：首次查询自动订阅合约
- ✅ **实时推送**：服务器推送的最新数据自动缓存
- ✅ **并发安全**：支持多个并发请求
- ✅ **简洁易用**：RESTful API 设计

---

## 📡 API 端点

### 1. 健康检查

```bash
GET /health
```

**响应示例**：
```json
{
  "status": "ok",
  "md_daemon": {
    "ok": true,
    "logged_in": true,
    "subscribed_count": 2,
    "cached_count": 2
  },
  "broker_id": "BHCT001",
  "md_server": "tcp://118.143.139.137:31213"
}
```

---

### 2. 行情服务状态

```bash
GET /md/status
```

**响应示例**：
```json
{
  "ok": true,
  "logged_in": true,
  "subscribed_count": 2,
  "cached_count": 2,
  "subscribed": ["CU3M-LME", "AL3M-LME"]
}
```

---

### 3. 获取单个合约行情

```bash
GET /md/tick/{instrument_id}
```

**特性**：
- 自动订阅未订阅的合约
- 返回最新的 tick 数据
- 响应速度：已订阅 < 10ms，首次订阅 ~3秒

**请求示例**：
```bash
curl http://localhost:8080/md/tick/CU3M-LME
```

**响应示例**：
```json
{
  "ok": true,
  "instrument_id": "CU3M-LME",
  "last_price": 10481.5,
  "volume": 23637,
  "trading_day": "20251002",
  "update_time": "02:00:00",
  "update_millisec": 185,
  "bid_price1": 10476,
  "bid_volume1": 1,
  "ask_price1": 10485,
  "ask_volume1": 1
}
```

**字段说明**：
- `last_price`: 最新成交价
- `volume`: 累计成交量
- `trading_day`: 交易日
- `update_time`: 更新时间（HH:MM:SS）
- `update_millisec`: 更新毫秒数
- `bid_price1`: 买一价
- `bid_volume1`: 买一量
- `ask_price1`: 卖一价
- `ask_volume1`: 卖一量

---

### 4. 批量查询行情

```bash
GET /md/ticks?ids={instrument_ids}
```

**参数**：
- `ids`: 逗号分隔的合约代码，最多 50 个

**请求示例**：
```bash
curl "http://localhost:8080/md/ticks?ids=CU3M-LME,AL3M-LME,ZN3M-LME"
```

**响应示例**：
```json
{
  "ticks": {
    "CU3M-LME": {
      "ok": true,
      "instrument_id": "CU3M-LME",
      "last_price": 10481.5,
      "volume": 23637,
      ...
    },
    "AL3M-LME": {
      "ok": true,
      "instrument_id": "AL3M-LME",
      "last_price": 2687,
      "volume": 15297,
      ...
    }
  },
  "errors": {
    "ZN3M-LME": "timeout waiting for tick data"
  }
}
```

---

### 5. 订阅合约（明确订阅）

```bash
POST /md/subscribe
Content-Type: application/json

{
  "instrument_ids": ["CU3M-LME", "AL3M-LME"]
}
```

**响应示例**：
```json
{
  "ok": true,
  "subscribed": ["CU3M-LME", "AL3M-LME"],
  "failed": null
}
```

**说明**：
- 明确订阅的合约会持久保留
- 不需要手动订阅，查询时会自动订阅

---

### 6. 取消订阅

```bash
POST /md/unsubscribe
Content-Type: application/json

{
  "instrument_ids": ["CU3M-LME"]
}
```

**响应示例**：
```json
{
  "ok": true,
  "unsubscribed": ["CU3M-LME"],
  "failed": null
}
```

---

### 7. 查询所有合约

```bash
GET /instruments
```

**响应示例**：
```json
{
  "ok": true,
  "count": 5234,
  "instruments": [
    "CU3M-LME",
    "AL3M-LME",
    "ZN3M-LME",
    "O_GC2512_C3000-CME",
    ...
  ]
}
```

**说明**：
- 使用 TraderApi 查询
- 返回所有可交易的合约代码
- 响应时间：~30秒（首次）

---

## 🚀 使用示例

### Python 客户端示例

```python
import requests

BASE_URL = "http://localhost:8080"

# 1. 检查服务状态
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. 获取单个行情
response = requests.get(f"{BASE_URL}/md/tick/CU3M-LME")
tick = response.json()
print(f"铜价: {tick['last_price']}")

# 3. 批量查询
instruments = ["CU3M-LME", "AL3M-LME", "ZN3M-LME"]
response = requests.get(
    f"{BASE_URL}/md/ticks",
    params={"ids": ",".join(instruments)}
)
ticks = response.json()["ticks"]

for inst_id, data in ticks.items():
    print(f"{inst_id}: {data['last_price']}")

# 4. 查询所有合约
response = requests.get(f"{BASE_URL}/instruments")
instruments = response.json()["instruments"]
print(f"可交易合约数: {len(instruments)}")
```

### curl 示例

```bash
# 健康检查
curl http://localhost:8080/health | jq .

# 获取单个行情
curl http://localhost:8080/md/tick/CU3M-LME | jq .

# 批量查询
curl "http://localhost:8080/md/ticks?ids=CU3M-LME,AL3M-LME" | jq .

# 查询状态
curl http://localhost:8080/md/status | jq .

# 订阅
curl -X POST http://localhost:8080/md/subscribe \
  -H "Content-Type: application/json" \
  -d '{"instrument_ids": ["CU3M-LME", "AL3M-LME"]}' | jq .

# 取消订阅
curl -X POST http://localhost:8080/md/unsubscribe \
  -H "Content-Type: application/json" \
  -d '{"instrument_ids": ["CU3M-LME"]}' | jq .

# 查询所有合约
curl http://localhost:8080/instruments | jq '.instruments[:10]'
```

---

## 🏗️ 架构说明

### 系统架构

```
┌─────────────────────────────────────────┐
│  Client (Agent / Application)           │
└──────────────┬──────────────────────────┘
               │ HTTP REST API
               ↓
┌─────────────────────────────────────────┐
│  FastAPI Service (service.py)           │
│  - API 路由                              │
│  - 请求处理                              │
└──────────────┬──────────────────────────┘
               │ stdin/stdout (JSON)
               ↓
┌─────────────────────────────────────────┐
│  MdDaemon (md_daemon.cpp)               │
│  - 只登录一次 ✅                         │
│  - 保持长连接                            │
│  - 自动订阅管理                          │
│  - 实时数据缓存                          │
└──────────────┬──────────────────────────┘
               │ TCP 长连接
               ↓
        CTP 服务器
```

### 核心特性

1. **守护进程模式**：
   - `md_daemon` 在应用启动时启动
   - 保持与 CTP 服务器的长连接
   - 进程存活期间，登录会话永久有效

2. **自动订阅**：
   - 首次查询合约时自动订阅
   - 订阅后持续接收推送数据
   - 数据缓存在内存中，查询速度 < 10ms

3. **并发安全**：
   - 守护进程是单例，避免多次登录冲突
   - 线程安全的命令队列和缓存

4. **简洁 API**：
   - RESTful 设计
   - 自动处理订阅逻辑
   - 统一的错误响应

---

## ⚙️ 配置

### 环境变量

```bash
CTP_BROKER_ID=BHCT001              # 券商代码
CTP_USER_ID=bhcttyw                # 用户ID
CTP_PASSWORD=gK^D9V%m              # 密码
CTP_MD_SERVER=tcp://IP:PORT        # 行情服务器地址
CTP_TRADE_SERVER=tcp://IP:PORT     # 交易服务器地址
```

### Docker Compose 启动

```bash
docker-compose up -d ctp-service
```

---

## 📊 性能指标

| 操作 | 响应时间 | 说明 |
|------|---------|------|
| 已订阅行情查询 | < 10ms | 从内存缓存读取 |
| 首次订阅 | ~3秒 | 需要订阅+等待首次数据 |
| 批量查询（已订阅） | < 50ms | 并发从缓存读取 |
| 查询所有合约 | ~30秒 | TraderApi 查询，仅首次慢 |

---

## 🔧 故障排除

### 1. 守护进程未启动

**症状**：`/health` 返回 "degraded"

**解决**：
```bash
# 查看日志
docker logs ctp-service

# 重启服务
docker-compose restart ctp-service
```

### 2. 订阅失败

**症状**：GET `/md/tick/{id}` 返回 "not subscribed"

**原因**：合约代码错误或服务器不支持

**解决**：
- 检查合约代码格式（如 `CU3M-LME`）
- 使用 `/instruments` 查询可用合约

### 3. IP 白名单问题

**症状**：登录超时或 "账户已登录"

**解决**：
- 联系券商添加公网 IP 到白名单
- 检查 IP 是否变化（动态IP）

---

## 📝 TODO / 未来改进

- [ ] 断线重连自动恢复
- [ ] 更多行情字段（开高低收、持仓量等）
- [ ] WebSocket 推送支持
- [ ] 行情数据持久化
- [ ] 性能监控和统计

---

## 📄 许可证

MIT License



