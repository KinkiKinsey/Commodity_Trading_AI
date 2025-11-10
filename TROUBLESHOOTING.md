# Ringshell 问题诊断与解决记录

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

**文档版本**: 1.0
**最后更新**: 2025-11-10
**维护者**: Claude AI Assistant
