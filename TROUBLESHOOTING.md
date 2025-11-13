方法 2：手动执行命令
如果你想手动控制每一步，按照以下顺序执行：
1️⃣ 构建 Backend 镜像
docker build -t ringshell-backend:local ./backend
2️⃣ 构建 Frontend 镜像
docker build -t ringshell-frontend:local ./frontend/web
3️⃣ 构建 Kafka Loader 镜像
docker build -t ringshell-kafka-loader:local -f Dockerfile.kafka-consumer .
4️⃣ 导出 Backend 镜像
docker save -o ringshell-backend-v1.tar ringshell-backend:local
5️⃣ 导出 Frontend 镜像
docker save -o ringshell-frontend-v1.tar ringshell-frontend:local
6️⃣ 导出 Kafka Loader 镜像
docker save -o ringshell-kafka-loader-v1.tar ringshell-kafka-loader:local
验证导出的文件
构建完成后，检查生成的 tar 文件：
dir ringshell-*.tar
你应该看到三个文件：
ringshell-backend-v1.tar
ringshell-frontend-v1.tar
ringshell-kafka-loader-v1.tar
上传到服务器
使用 scp 命令上传（或使用 WinSCP）：
scp ringshell-backend-v1.tar root@47.96.88.181:/root/
scp ringshell-frontend-v1.tar root@47.96.88.181:/root/
scp ringshell-kafka-loader-v1.tar root@47.96.88.181:/root/
💡 注意事项
确保在项目根目录 (D:\360MoveData\Users\juiceNo3\Desktop\ringshellV1) 执行命令
构建时间: Frontend 镜像可能需要 5-10 分钟（需要 npm install）
磁盘空间: 确保有足够空间（每个 tar 文件约 200MB-1GB）
网络连接: 构建 Frontend 时需要下载 npm 包
现在你可以执行 .\build-and-export.bat 或者手动执行上面的命令了！需要我帮你运行吗？
好的！那就只构建和导出 Frontend 镜像：
📦 构建和导出 Frontend 镜像
一条命令完成（推荐）
docker build -t ringshell-frontend:local ./frontend/web && docker save -o ringshell-frontend-v1.tar ringshell-frontend:local
或者分步执行
1️⃣ 构建 Frontend 镜像
docker build -t ringshell-frontend:local ./frontend/web
2️⃣ 导出为 tar 文件
docker save -o ringshell-frontend-v1.tar ringshell-frontend:local
验证导出的文件
dir ringshell-frontend-v1.tar
上传到服务器
scp ringshell-frontend-v1.tar root@47.96.88.181:/root/
💡 提示
构建时间: 大约 5-10 分钟（需要下载 npm 依赖）
文件大小: 约 200-300MB
确保在项目根目录执行命令
需要我帮你运行这个命令吗？# Ringshell 问题诊断与解决记录

## 日期: 2025-11-10

---

## 问题1: ClickHouse 连接泄漏 (严重) ⚠️

### 症状
- 后端日志显示大量 `ClickHouse HTTP error:` 错误
- CTP K线接口返回 `503 Service Unavailable`
- 使用 `netstat -ano | findstr :18123` 查看发现200+个 `CLOSE_WAIT` 连接
- 前端 CTP 合约追踪显示 "This operation was aborted"

### 根本原因
每次执行 ClickHouse 查询时都创建新的 `httpx.AsyncClient` 实例:
```python
# 问题代码
async with httpx.AsyncClient(timeout=cfg.timeout) as client:
    response = await client.post(...)
```

虽然使用了 `async with`,但在高并发场景下,连接没有被正确复用和关闭,导致:
- 每个请求创建新的TCP连接
- 连接在关闭时进入 CLOSE_WAIT 状态
- 最终耗尽系统连接资源

### 解决方案

**文件**: `backend/src/core/clickhouse.py`

#### 1. 创建全局单例 HTTP 客户端
```python
# Global httpx client to reuse connections
_http_client: httpx.AsyncClient | None = None

def _get_http_client() -> httpx.AsyncClient:
    """Get or create a singleton httpx client for ClickHouse queries."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        cfg = get_clickhouse_config()
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(cfg.timeout, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _http_client
```

#### 2. 修改查询函数使用单例客户端
```python
async def run_clickhouse_query(sql: str) -> List[Dict[str, Any]]:
    # ... 配置代码 ...

    client = _get_http_client()  # 使用单例客户端

    try:
        response = await client.post(cfg.url, params=params, content=query, auth=auth)
    except httpx.HTTPError as exc:
        logger.error(f"ClickHouse HTTP error: {exc}")
        raise ClickHouseError(f"ClickHouse request failed: {exc}") from exc

    # ... 处理响应 ...
```

### 关键改进
1. **连接复用**: 所有查询共享同一个HTTP客户端
2. **连接池限制**:
   - `max_keepalive_connections=5`: 最多保持5个活跃连接
   - `max_connections=10`: 最多创建10个并发连接
3. **连接超时**: `connect=5.0` 秒连接超时

### 验证方法
```bash
# 检查 ClickHouse 连接状态
netstat -ano | findstr :18123

# 健康状态应该只有少量 ESTABLISHED 连接,没有 CLOSE_WAIT
```

### 预防措施
- ✅ 使用单例模式管理长连接客户端
- ✅ 设置合理的连接池限制
- ✅ 定期监控连接状态
- ❌ 避免在每次请求时创建新的HTTP客户端

---

## 问题2: CTP 实时数据请求超时

### 症状
- 前端所有 CTP 合约卡片显示 "This operation was aborted"
- 后端日志显示: `Failed to fetch from relay server, falling back to ClickHouse`
- 每个请求耗时5秒以上

### 根本原因
代码尝试先从 Relay Server (`http://47.108.177.50:8080`) 获取实时数据,但该服务器:
- 响应缓慢或不可达
- 每次请求等待5秒超时才回退到 ClickHouse
- 前端请求在后端响应之前就被取消(abort)

### 解决方案

**文件**: `backend/src/api/ctp.py`

#### 完全禁用 Relay Server,直接使用 ClickHouse

```python
async def _fetch_latest_tick(symbol: str) -> Optional[dict]:
    """Fetch latest tick from ClickHouse (relay server disabled due to timeout issues)."""
    # Relay server disabled - directly use ClickHouse for better performance
    # Original relay URL: http://47.108.177.50:8080/md/tick/{symbol}

    sql = f"""
        SELECT
            symbol,
            local_ts,
            exchange_ts,
            update_time,
            update_millisec,
            last_price,
            bid_price1,
            bid_volume1,
            ask_price1,
            ask_volume1,
            volume
        FROM ctp.ctp_ticks
        WHERE symbol = '{symbol}'
        ORDER BY local_ts DESC
        LIMIT 1
    """
    rows = await run_clickhouse_query(sql)
    return rows[0] if rows else None
```

### 性能对比
| 数据源 | 响应时间 | 稳定性 |
|--------|----------|--------|
| Relay Server | 5s+ (超时) | ❌ 不稳定 |
| ClickHouse | <100ms | ✅ 稳定 |

### 如果需要重新启用 Relay Server
1. 确认 Relay Server 可达: `curl http://47.108.177.50:8080/md/tick/CL2512-NYM`
2. 减少超时时间: `timeout=1.0` 秒
3. 添加健康检查机制

---

## 问题3: 油因子图表时间戳重复错误

### 症状
前端报错:
```
Error: Assertion failed: data must be asc ordered by time,
index=1, time=1736899200, prev time=1736899200
```

### 根本原因
LightweightCharts 库要求:
- 数据必须按时间升序排列
- 时间戳必须唯一,不能有重复

后端返回的油因子数据包含重复的时间戳。

### 解决方案

**文件**: `frontend/web/components/charts/OilFactorsOverlayChart.tsx`

#### 使用 Map 进行强制去重和排序

```typescript
function toLine(points: OverlayDataPoint[]): LineData[] {
  if (!points || points.length === 0) return [];

  // Use Map to ensure unique timestamps, keeping the last value for duplicates
  const uniqueMap = new Map<number, number>();
  points.forEach(point => {
    const timeNum = Number(point.time);
    uniqueMap.set(timeNum, point.value);
  });

  // Convert to array and sort by time
  const result = Array.from(uniqueMap.entries())
    .map(([time, value]) => ({ time: time as Time, value }))
    .sort((a, b) => Number(a.time) - Number(b.time));

  return result;
}

function toHistogram(points: OverlayDataPoint[]): HistogramData[] {
  if (!points || points.length === 0) return [];

  // Use Map to ensure unique timestamps
  const uniqueMap = new Map<number, { value: number }>();
  points.forEach(point => {
    const timeNum = Number(point.time);
    uniqueMap.set(timeNum, { value: point.value });
  });

  // Convert to array and sort by time
  const result = Array.from(uniqueMap.entries())
    .map(([time, data]) => ({
      time: time as Time,
      value: data.value,
      color: data.value >= 0 ? MICRO_POSITIVE : MICRO_NEGATIVE
    }))
    .sort((a, b) => Number(a.time) - Number(b.time));

  return result;
}
```

### 为什么使用 Map
1. **自动去重**: Map 的键是唯一的,相同时间戳会自动覆盖
2. **性能好**: O(n) 时间复杂度
3. **保留最新值**: 后面的值会覆盖前面的值

### 前端缓存刷新
如果修改后错误仍然出现:
```bash
# 删除 Next.js 缓存
cd frontend/web
Remove-Item -Recurse -Force .next

# 重启前端
npm run dev
```

浏览器硬刷新: `Ctrl + Shift + R`

---

## 问题4: CORS 预检请求失败

### 症状
- 后端日志显示: `OPTIONS /api/pricing/tick?... HTTP/1.1" 400 Bad Request`
- 浏览器控制台显示 CORS 错误

### 根本原因
CORS 中间件的添加顺序不正确,在路由注册之前添加了中间件。

### 解决方案

**文件**: `backend/src/api/__init__.py`

#### 正确的顺序: 先注册路由,再添加 CORS 中间件

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="Ringshell Pricing API",
        version="0.1.0",
    )

    # 配置 CORS origins
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if not allowed_origins:
        allowed_origins = ["*"]

    allow_origin_regex_env = os.getenv("CORS_ALLOW_ORIGIN_REGEX")
    allow_origin_regex = allow_origin_regex_env if allow_origin_regex_env else None

    # 1️⃣ 先注册路由
    app.include_router(pricing_router)
    app.include_router(news_router)
    app.include_router(oil_factors_router)
    app.include_router(ctp_router)

    # 2️⃣ 再添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],  # 允许暴露所有响应头
    )

    return app
```

### 关键配置
- `allow_credentials=True`: 允许发送凭证
- `allow_methods=["*"]`: 允许所有 HTTP 方法(包括 OPTIONS)
- `expose_headers=["*"]`: 允许前端访问所有响应头

---

## 问题5: OpenAI API 速率限制

### 症状
- 后端日志显示: `429 Too Many Requests` 错误
- 自动翻译和 AI 分析功能阻塞其他请求

### 根本原因
- 自动翻译每条新闻标题和内容
- 自动 AI 分析每条新闻
- OpenAI API 有速率限制(RPM, TPM)

### 解决方案

**文件**: `backend/src/api/news.py`

#### 1. 禁用自动翻译

```python
@router.post("/api/news/translate")
async def translate_news(payload: TranslationPayload) -> JSONResponse:
    # Translation disabled - return original text to avoid OpenAI blocking
    if not payload.items:
        return JSONResponse({"translations": {}}, status_code=200)

    unique_items: Dict[str, str] = {}
    for item in payload.items:
        if item.id not in unique_items:
            unique_items[item.id] = item.text

    # Return original text without translation
    return JSONResponse({"translations": unique_items})
```

#### 2. 禁用自动 AI 分析

**文件**: `backend/src/news/service.py`

```python
events: list[dict] = [event for event, _ in processed]

# Automatic AI processing disabled to prevent OpenAI rate limiting and blocking
# Users can manually trigger AI analysis via /api/news/analyze endpoint
# chain_count = min(CHAIN_OF_THOUGHT_LIMIT, len(processed))
# if chain_count:
#     ... [注释掉的自动分析代码] ...

return events
```

### 手动触发方式
前端可以通过点击按钮手动触发:
```typescript
// POST /api/news/analyze
{
  "text": "新闻全文",
  "headline": "新闻标题",
  "summary": "新闻摘要"
}
```

---

## 通用诊断流程

### 1. 检查后端状态
```bash
# 检查端口占用
netstat -ano | findstr :8000

# 检查后端进程
tasklist | findstr python

# 查看后端日志
# 在后端终端查看实时输出
```

### 2. 检查 ClickHouse 状态
```bash
# 检查 ClickHouse 是否运行
curl http://localhost:18123/ping
# 期望输出: Ok.

# 检查连接状态
netstat -ano | findstr :18123
# 健康状态: 少量 ESTABLISHED, 无 CLOSE_WAIT
```

### 3. 检查前端连接
```bash
# 测试 API 可达性
curl http://localhost:8000/healthz
# 期望输出: {"status":"ok"}

# 测试具体接口
curl http://localhost:8000/api/ctp/realtime?symbol=CL2512-NYM
```

### 4. 前端问题排查
- 打开浏览器开发者工具 (F12)
- 查看 Console 标签页的错误
- 查看 Network 标签页的请求状态
- 检查请求是否发送,响应状态码

---

## 重启步骤

### 完全重启后端
```powershell
# 1. 找到所有后端进程
netstat -ano | findstr :8000

# 2. 杀掉所有进程
taskkill /F /PID <进程ID>

# 3. 重新启动
cd D:\360MoveData\Users\juiceNo3\Desktop\ringshellV1\backend
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

### 重启前端
```powershell
# 1. 停止前端 (Ctrl+C)

# 2. 清除缓存
cd D:\360MoveData\Users\juiceNo3\Desktop\ringshellV1\frontend\web
Remove-Item -Recurse -Force .next

# 3. 重新启动
npm run dev
```

### 重启 ClickHouse (如果需要)
```bash
# 根据你的 ClickHouse 安装方式
# Docker:
docker restart clickhouse-server

# Windows 服务:
net stop clickhouse
net start clickhouse
```

---

## 性能优化配置

### ClickHouse 连接池
```python
# backend/src/core/clickhouse.py
httpx.Limits(
    max_keepalive_connections=5,  # 保持活跃的连接数
    max_connections=10,           # 最大连接数
)
```

### 超时配置
```python
# backend/.env
CLICKHOUSE_TIMEOUT_SECONDS=30.0  # ClickHouse 查询超时
CTP_REALTIME_CACHE_SECONDS=1.0   # CTP 实时数据缓存时间
CTP_REALTIME_MIN_INTERVAL_SECONDS=0.3  # 最小请求间隔
```

---

## 预防性维护

### 每日检查清单
- [ ] 检查 ClickHouse 连接数: `netstat -ano | findstr :18123 | findstr CLOSE_WAIT`
- [ ] 检查后端日志是否有重复错误
- [ ] 检查前端是否所有功能正常
- [ ] 检查 Redis 内存使用情况

### 每周检查清单
- [ ] 清理 ClickHouse 旧数据
- [ ] 检查磁盘空间
- [ ] 更新依赖包
- [ ] 备份配置文件

---

## 相关文件清单

### 关键修改文件
| 文件 | 问题 | 修改内容 |
|------|------|----------|
| `backend/src/core/clickhouse.py` | 连接泄漏 | 单例HTTP客户端 |
| `backend/src/api/ctp.py` | 请求超时 | 禁用relay server |
| `backend/src/api/__init__.py` | CORS错误 | 调整middleware顺序 |
| `backend/src/api/news.py` | OpenAI限流 | 禁用自动翻译 |
| `backend/src/news/service.py` | OpenAI限流 | 禁用自动AI分析 |
| `frontend/web/components/charts/OilFactorsOverlayChart.tsx` | 时间戳重复 | Map去重 |

### 配置文件
- `backend/.env` - 环境变量配置
- `frontend/web/.env.local` - 前端API端点配置

---

## 联系与支持

如果遇到新的问题:
1. 检查本文档中是否有类似问题
2. 按照诊断流程逐步排查
3. 记录详细的错误日志和复现步骤

---

## 问题6: Kafka 和 kafka-to-clickhouse 服务异常重启

### 症状
- Docker 显示 `kafka-to-clickhouse` 容器状态为 "Restarting"
- Kafka 容器状态为 "Exited (1)"
- 前端 CTP 合约显示巨大延迟（200000+ 秒，相当于几十小时）
- 最后一个合约显示 "延迟 · 0s"，其他合约显示旧数据

### 根本原因
1. **Kafka 服务停止**: Kafka 容器意外退出，可能由于系统重启或资源不足
2. **kafka-to-clickhouse 无法连接**: 由于 Kafka 不可用，导致消费者不断重试并崩溃
   - 错误日志: `NoBrokersAvailable`
   - 错误日志: `DNS lookup failed for kafka:9092`
3. **数据流中断**: Collector → Kafka → ClickHouse 数据管道断裂
4. **ClickHouse 数据陈旧**: 由于数据没有写入，前端读取到的都是很久之前的数据

### 诊断方法

#### 1. 检查容器状态
```bash
docker ps -a | findstr kafka
docker ps -a | findstr clickhouse
docker ps -a | findstr collector
```

#### 2. 查看 kafka-to-clickhouse 日志
```bash
docker logs ringshellv1-kafka-to-clickhouse-1 --tail 50
```

预期错误日志:
```
[ERROR] DNS lookup failed for kafka:9092 (0)
kafka.errors.NoBrokersAvailable: NoBrokersAvailable
```

#### 3. 检查 Kafka 状态
```bash
docker ps | findstr kafka
# 如果显示 "Exited (1)"，说明 Kafka 已停止
```

### 解决方案

#### 1. 重启 Kafka 服务
```bash
docker-compose -f docker-compose.ctp.yml restart kafka
```

#### 2. 重启 kafka-to-clickhouse 服务
```bash
docker-compose -f docker-compose.ctp.yml restart kafka-to-clickhouse
```

#### 3. 验证服务状态
```bash
# 检查容器是否运行
docker ps | findstr kafka

# 预期输出:
# ringshellv1-kafka-1                  Up X seconds
# ringshellv1-kafka-to-clickhouse-1    Up X seconds
```

#### 4. 验证 kafka-to-clickhouse 连接成功
```bash
docker logs ringshellv1-kafka-to-clickhouse-1 --tail 20
```

预期成功日志:
```
[INFO] Broker version identified as 2.6.0
[INFO] Successfully joined group ctp-clickhouse-consumer
[INFO] Setting newly assigned partitions {TopicPartition(topic='ctp_ticks', partition=0)}
```

#### 5. 验证 Collector 正常工作
```bash
docker logs ringshellv1-collector-1 --tail 10
```

预期日志:
```
[INFO] cycle 105 ok (4 rows)
[INFO] cycle 106 ok (5 rows)
```

### 数据恢复时间
- 重启服务后，等待 **1-2 分钟**
- 新数据开始写入 ClickHouse
- 前端刷新后，延迟降至 **0-5 秒**

### 预防措施

#### 1. 配置自动重启策略
在 `docker-compose.ctp.yml` 中已配置:
```yaml
services:
  kafka:
    restart: unless-stopped

  kafka-to-clickhouse:
    restart: unless-stopped

  collector:
    restart: unless-stopped
```

#### 2. 监控容器健康状态
创建健康检查脚本:
```bash
#!/bin/bash
# check-services.sh

echo "Checking Kafka services..."
docker ps | grep -E "(kafka|collector|clickhouse)" || echo "⚠️  Some services are down!"
```

#### 3. 定期检查日志
```bash
# 每天检查是否有重启记录
docker ps -a | findstr "Restarting"
```

### 系统架构说明

**正常数据流**:
```
CTP API (外部)
    ↓ HTTP 请求
Collector (每3秒)
    ↓ Kafka Producer
Kafka (消息队列)
    ↓ Kafka Consumer
kafka-to-clickhouse (批量写入)
    ↓ INSERT
ClickHouse (数据库)
    ↓ HTTP 查询
Backend API
    ↓ HTTP Response
Frontend (实时显示)
```

**故障点识别**:
- ✅ Collector: 日志显示 "cycle X ok"
- ❌ Kafka: 容器 Exited
- ❌ kafka-to-clickhouse: 不断 Restarting
- ✅ ClickHouse: 正常运行但数据陈旧
- ✅ Backend/Frontend: 正常运行但显示旧数据

---

## 问题7: Collector 采集合约数量不足

### 症状
- Collector 日志显示部分合约超时: `[WARNING] failed to fetch CL2511-NYM (timed out)`
- 每个周期只采集到 4-5 个合约，而不是期望的 6 个
- 前端只显示少于 6 个合约卡片
- 某些合约（如 CL2511）可能已过期或不可用

### 根本原因
1. **固定合约列表**: Collector 生成固定的 N 个合约 ID（从下个月开始）
2. **合约过期**: 第一个合约可能已经过期或暂时不可用
3. **没有补充机制**: 如果某个合约失败，不会尝试下一个可用合约

原始逻辑:
```python
# 只生成 6 个合约
symbols = generate_contract_ids(6)  # CL2512, CL2601, CL2602, CL2603, CL2604, CL2605

# 如果 CL2511 超时，只剩 5 个
for symbol in symbols:
    try:
        fetch_tick(symbol)
    except:
        continue  # 跳过失败的合约
```

### 解决方案

**文件**: `scripts/ctp_collector.py`

#### 1. 生成更多候选合约
```python
def run(self):
    # Generate extra candidates to handle expired/failed contracts
    # Try up to 2x the target to ensure we get enough valid contracts
    candidate_count = self.config.contract_count * 2  # 生成 12 个候选
    symbols = generate_contract_ids(candidate_count)
```

#### 2. 收集到足够数量后停止
```python
def _collect_once(self, symbols: Iterable[str]) -> List[Dict[str, Optional[float]]]:
    rows: List[Dict[str, Optional[float]]] = []
    target_count = self.config.contract_count

    for symbol in symbols:
        # Stop if we already have enough valid contracts
        if len(rows) >= target_count:
            break

        try:
            payload = fetch_tick(symbol)
            rows.append(payload)
        except Exception as exc:
            logging.warning("failed to fetch %s (%s)", symbol, exc)
            continue  # 尝试下一个合约

    return rows
```

#### 3. 添加警告日志
```python
if len(rows) < self.config.contract_count:
    logging.warning("only collected %d/%d contracts (some may be expired)",
                   len(rows), self.config.contract_count)
```

### 工作流程

**改进后的逻辑**:
```
1. 生成 12 个候选合约: CL2512, CL2601, ..., CL2611
2. 依次尝试抓取:
   - CL2511 → 超时 ❌ (跳过)
   - CL2512 → 成功 ✅ (1/6)
   - CL2601 → 成功 ✅ (2/6)
   - CL2602 → 成功 ✅ (3/6)
   - CL2603 → 成功 ✅ (4/6)
   - CL2604 → 成功 ✅ (5/6)
   - CL2605 → 成功 ✅ (6/6) → 停止
3. 结果: 成功采集 6 个合约
```

### 验证方法

#### 1. 查看 Collector 日志
```bash
docker logs ringshellv1-collector-1 --tail 20
```

预期输出:
```
[WARNING] failed to fetch CL2511-NYM (timed out)
[INFO] cycle 108 ok (6 rows)  ← 确保有 6 rows
```

#### 2. 检查前端显示
刷新页面，确认显示 6 个合约卡片

#### 3. 检查 ClickHouse 数据
```sql
SELECT symbol, COUNT(*)
FROM ctp.ctp_ticks
WHERE local_ts > now() - INTERVAL 1 MINUTE
GROUP BY symbol
ORDER BY symbol;
```

预期结果: 至少 6 个不同的 symbol

### 配置参数

如果需要调整合约数量，修改 Collector 启动参数:
```bash
# docker-compose.ctp.yml
environment:
  - CONTRACTS=8  # 增加到 8 个合约
```

或在代码中修改默认值:
```python
DEFAULT_CONTRACTS = 8  # 增加默认合约数
```

### 性能影响
- **更多候选合约**: 每个周期最多尝试 12 次 HTTP 请求（而不是 6 次）
- **更快完成**: 一旦收集到 6 个就停止，通常只需 7-8 次请求
- **轻微延迟**: 如果多个合约失败，可能增加 2-3 秒延迟

### 预防措施
1. ✅ 定期检查 Collector 日志中的警告
2. ✅ 监控采集到的合约数量
3. ✅ 如果长期只有 4-5 个合约，考虑：
   - 增加候选合约数量（`candidate_count = self.config.contract_count * 3`）
   - 检查 CTP API 服务稳定性
   - 调整超时时间（当前 3 秒）

---

**文档版本**: 1.1
**最后更新**: 2025-11-13
**维护者**: Claude AI Assistant
