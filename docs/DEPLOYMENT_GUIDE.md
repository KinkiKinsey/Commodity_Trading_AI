# Ringshell 部署指南（阿里云版）

> 目标：将 Ringshell 的前端、后端及行情数据管线在阿里云上线运行，遵循“Web 层 / 数据层”解耦的最优实践，方便后续团队协作与扩缩。

---

## 1. 拓扑概览

| 层级 | 组件 | 说明 |
| --- | --- | --- |
| Web 层（对外入口） | FastAPI (`backend/src/api`) | 通过 uvicorn 提供 `/api/*`、SSE `/api/news/stream`、CTP/K 线 REST。 |
|  | Next.js (`frontend/web`) | 交付 Bloomberg 风格实时新闻页与 Oil Factors 页，依赖 React Query + SSE。 |
|  | 反向代理 | 建议使用 Nginx 或阿里云 SLB + WAF，负责 TLS 终止、SSE 透传。 |
| 数据层（内部网络） | Kafka + Zookeeper | 承载 tick 流。可换成阿里云消息队列 Kafka 版。 |
|  | ClickHouse | 存储 tick/聚合 bars/指标。可换成阿里云 ClickHouse（AnalyticDB PostgreSQL 版兼容）。 |
|  | Tick Collector (`scripts/ctp_collector.py`) | 轮询 `/md/tick` 并写入 Kafka。 |
|  | Kafka → ClickHouse Consumer (`scripts/kafka_to_clickhouse.py`) | 批量刷写 `ctp.ctp_ticks`。 |
| *备注* | 本版部署不包含 Redis 与 CTP Service | 如需扩展可再行补充。 |

---

## 2. 前置条件

1. **阿里云账号 & 资源**
   - ECS：建议分为 *web 节点*（2C4G 起）与 *data 节点*（4C8G+SSD，用于 Kafka/ClickHouse）。也可改用 ACK（Kubernetes）+ 节点池。
   - VPC：创建私网子网，Web 层与数据层同 VPC，外网访问由 SLB/NAT 控制。
   - 安全组：放通 Web 80/443，对内放通 Kafka/ClickHouse 端口；限制 `/md/tick` 采集器的出站。
2. **镜像仓库**
   - 使用阿里云 ACR（容器镜像服务）托管 `ringshell-backend`, `ringshell-frontend`, `ringshell-collector`, `ringshell-kafka-loader` 等镜像。
3. **外部依赖**
   - OpenAI、Firecrawl、AlphaVantage/FMP、LangSmith、Redis Cloud（如继续使用）等 API Key。
   - `/md/tick` 上游（若自建 CTP 服务需对应证书/动态库）。
4. **运维工具**
   - Docker 24+ / Docker Compose v2（本地构建/调试）。
   - Terraform/Ansible/ACK（可选）用于基础设施即代码。

---

## 3. 环境变量与密钥管理

建议使用阿里云 **密钥管家（KMS）** 或 **参数服务（OTS/ACM）** 管理敏感数据，通过 `docker run --env-file` 或 ACK Secret 注入。核心变量：

| 变量 | 描述 | 位置 |
| --- | --- | --- |
| `OPENAI_API_KEY` | LangGraph/翻译模型密钥 | backend、collector（若调用 LLM）。 |
| `FIRECRAWL_API_KEY` | Firecrawl 搜索 | backend |
| `FMP_API_KEY` & `ALPHAVANTAGE_API_KEY` | 行情拉取 | backend |
| `LANGSMITH_*` | LangSmith 追踪 | backend |
| `MD_TICK_BASE_URL` | tick 上游地址 | backend、collector |
| `CLICKHOUSE_*` | ClickHouse 连接信息 | backend、kafka_loader、diagnostics |
| `KAFKA_BOOTSTRAP_SERVERS` & `KAFKA_TICK_TOPIC` | Kafka 地址 / Topic | collector、kafka_loader |
| `CTP_*` | 期货账户配置 | 若采集器要求登录，可在 collector `.env` 中配置 |
| `NEXT_PUBLIC_*` | 前端访问的 API Endpoint | frontend |

> Tip：对公私网地址分开管理（例如 `KAFKA_BOOTSTRAP_SERVERS=internal-kafka:9092`），避免硬编码 `localhost`。

---

## 4. 镜像构建

### 4.1 Backend（FastAPI + LangGraph）
1. 修改 `backend/Dockerfile` 入口：
   ```dockerfile
   CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
2. 构建并推送：
   ```bash
   docker build -t registry.cn-<region>.aliyuncs.com/ringshell/backend:latest ./backend
   docker push registry.cn-<region>.aliyuncs.com/ringshell/backend:latest
   ```

### 4.2 Frontend（Next.js 14）
1. 在 `frontend/web` 目录新增 Dockerfile（示例）：
   ```dockerfile
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY package.json package-lock.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   FROM node:20-alpine
   WORKDIR /app
   ENV NODE_ENV=production
   COPY --from=builder /app ./
   EXPOSE 3000
   CMD ["npm", "run", "start"]
   ```
2. 构建/推送同理。

### 4.3 Tick Collector & Kafka Loader
- `scripts/ctp_collector.py` 已有 `Dockerfile.collector` 示例，可直接构建。
- 新增 `Dockerfile.kafka_loader`（调用 `scripts/kafka_to_clickhouse.py`）：
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY scripts/kafka_to_clickhouse.py .
  RUN pip install --no-cache-dir kafka-python==2.0.2 clickhouse-connect==0.7.0
  CMD ["python", "kafka_to_clickhouse.py"]
  ```

### 4.4 可选：CTP Service
- `services/ctp/Dockerfile` 需携带券商提供的 `.so`/头文件。部署时确保合规，并设置 `LD_LIBRARY_PATH`。

---

## 5. 部署拆分

### 5.1 Web Stack（建议 `deploy/web/docker-compose.yml`）
```yaml
services:
  backend:
    image: registry.cn-<region>.aliyuncs.com/ringshell/backend:latest
    env_file: .env.backend   # 仅包含 Web 层所需密钥
    ports:
      - "8000:8000"
    networks:
      - web

  frontend:
    image: registry.cn-<region>.aliyuncs.com/ringshell/frontend:latest
    environment:
      - NEXT_PUBLIC_API_BASE_URL=https://api.ringshell.example
    ports:
      - "3000:3000"
    networks:
      - web

networks:
  web:
    external: false
```
> 上线时通常把 backend/ frontend 部署到 ECS/ACK，并将 80/443 暴露给 SLB。本方案默认不部署 Redis，如需缓存层可单独扩展。

### 5.2 Data Stack（`deploy/data/docker-compose.yml`）
```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    networks: [data]

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on: [zookeeper]
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"
    networks: [data]

  clickhouse:
    image: clickhouse/clickhouse-server:23.8
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    ports:
      - "8123:8123"
    networks: [data]

  tick-collector:
    image: registry.cn-<region>.aliyuncs.com/ringshell/collector:latest
    environment:
      - CTP_TICK_BASE_URL=http://<vendor-host>/md/tick
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_TICK_TOPIC=ctp_ticks
    networks: [data]

  kafka-loader:
    image: registry.cn-<region>.aliyuncs.com/ringshell/kafka-loader:latest
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_TICK_TOPIC=ctp_ticks
      - CLICKHOUSE_URL=http://clickhouse:8123
      - CLICKHOUSE_USER=default
      - CLICKHOUSE_PASSWORD=
    networks: [data]

volumes:
  clickhouse_data:

networks:
  data:
    external: false
```
> 生产环境建议：Kafka & ClickHouse 使用阿里云托管，collector / loader 以 ECS/ACK 中的容器运行，挂载 CloudMonitor/ARMS 采集日志。

### 5.3 网络互通
- Web 层通过专用 VPC 子网访问数据层（Kafka/ClickHouse）。在 Compose 方案中，可通过 `docker network connect` 把 backend 连接到 `data` 网络，或在 ACK 中用 Service/ClusterIP。
- 对外只暴露 Web 层 80/443。Kafka/ClickHouse 端口仅在内网开放。

---

## 6. 数据初始化与运维任务

1. **ClickHouse 建表**
   ```bash
   curl -X POST http://clickhouse:8123 --data-binary @scripts/clickhouse_init.sql
   ```
2. **指标回填**
   - 运行 `scripts/backfill_indicator_series.py --symbols "CL2512-NYM,CL2601-NYM" --bars 2000 --url http://clickhouse:8123`.
   - 可包装成 CronJob（ACK）或 ECS 定时任务。
3. **诊断脚本**
   - `backend/scripts/diagnose_docker.ps1` / `diagnose_full.ps1` 可改写成 shell 版本，在容器内执行以验证 ClickHouse/Kafka 连通。
4. **日志与监控**
   - 使用阿里云 Log Service 收集 backend/frontend/collector/loader 日志。
   - ClickHouse 自带 `system.metrics`; Kafka 监控可接入 CloudMonitor。
   - 对 SSE `/api/news/stream` 建立探针（如 `curl --no-buffer`）验证心跳。

---

## 7. 可选扩展

| 功能 | 建议做法 |
| --- | --- |
| 自建 CTP `/md/tick` | *当前版本不包含*。如需自建，可复用 `services/ctp` 镜像并在 collector 中切换 `CTP_TICK_BASE_URL`。 |
| Redis 缓存 | *未启用*。若后续需要，可接入阿里云 Tair 并更新 backend 配置。 |
| Kubernetes | 将 Web/Data compose 转换为 Helm Chart；使用 ACK 的 NodePool 区分 Web/Data。 |
| CI/CD | 使用 GitHub Actions 构建镜像 → 推 ACR → 触发 ACK/ECS 滚动更新。 |

---

## 8. 标准操作流程

1. **本地验证**
   - 分别执行 `docker compose -f deploy/web/docker-compose.yml up` 与 `docker compose -f deploy/data/docker-compose.yml up`，确认端口与日志正常。
2. **推送镜像**：每次变更前后端/采集器代码后，重新构建并 push 到 ACR。
3. **部署**
   - ECS：通过 `docker compose up -d` 或 systemd unit 管理；保障 `/var/lib/docker` 有足够空间。
   - ACK：使用 `kubectl apply -f`，把敏感配置写入 Secret/ConfigMap。
4. **监控 & 报警**
   - 针对 ClickHouse freshness（`/api/ctp/healthz`）、SSE 心跳、Kafka lag、容器健康状况设置告警。
5. **扩容**
   - Web 层通过 SLB + 多实例扩展；数据层根据吞吐在 Kafka/ClickHouse 侧加节点。
6. **回滚**
   - 镜像按语义版本管理，使用 `:prev` tag 迅速回退。

---

## 9. 附录

- 参考文件
  - `docker-compose.yml`, `docker-compose.ctp.yml`
  - `scripts/clickhouse_init.sql`, `scripts/ctp_collector.py`, `scripts/kafka_to_clickhouse.py`
  - `docs/Bloomberg_Frontend_Redesign.md`, `DATA_SOURCE_FEASIBILITY.md`
- 常见问题
  1. **SSE 断连**：确保 Nginx `proxy_read_timeout` > 60s，且未启用响应缓存。
  2. **Kafka lag 累积**：检查 collector 是否获取不到 `/md/tick` 或 ClickHouse insert 失败，必要时提升 `kafka-loader` 并发。
  3. **ClickHouse schema 变更**：统一通过 `scripts/clickhouse_init.sql` 维护，并在 CI 中做 schema drift 检测。

> 完成以上配置后，即可按照“前端/后端 + 数据管线”两条流水线各自迭代，同事只需关注对应 compose/k8s 模块即可。
