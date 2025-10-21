# RingShell – AI Commodity Market Analyst

RingShell 是一套面向大宗商品研究与交易团队的智能分析平台，结合 LangGraph 代理、实时资讯与金融指标，为用户提供方向判断、链式推理与高频行情信号。

---

## 目录结构

```
ringshell/
├── backend/                      # Python 服务层（LangGraph Agent / FastAPI）
│   ├── src/                      # 业务源码
│   │   ├── core/                 # Agent 编排与工具
│   │   ├── financial/            # 金融指标与数据源
│   │   ├── models/               # Pydantic/TypedDict 定义
│   │   └── prompts/              # Prompt 与模板
│   ├── tests/                    # 后端测试（pytest）
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── .env.example
├── frontend/                     # 前端工程（Next.js 等，占位）
│   └── web/
├── services/                     # 外部集成与旁路服务
│   └── ctp/                      # 期货交易适配（原生代码）
├── docs/                         # 项目文档（计划、IA、API 契约等）
├── docker-compose.yml            # 编排后端/服务容器
├── .env                          # Docker Compose 环境变量（本地自备）
└── PROJECT_DOCUMENTATION.md      # 项目背景与技术说明
```

---

## 本地快速启动（后端）

### 前置准备
- 安装 Docker Desktop
- 在项目根目录复制 `backend/.env.example` 为 `.env`，并填写真实的 `OPENAI_API_KEY`、`FIRECRAWL_API_KEY` 等

### 启动

```bash
# 构建并启动后端容器
docker-compose up backend

# 后台运行
docker-compose up -d backend

# 查看日志
docker-compose logs -f backend
```

容器启动后会自动执行 `backend/main.py`，调用 LangGraph Agent 进行示例推理。若 API Key 未配置，会在日志中提示 401 错误，可在 `.env` 修正。

### 运行测试

```bash
# 在容器内运行 pytest
docker-compose exec backend python -m pytest
```

---

## 重要目录说明

- **backend/src/core/**：`commodity_agent.py` 定义了 LangGraph 状态机，`utils.py` 提供 Firecrawl 搜索工具等。
- **backend/src/models/**：新增 `NewsStreamEvent`、`ChainOfThoughtStep` 等模型，用于实时新闻 SSE 契约。
- **backend/tests/**：包含金融工具与 LangChain 工具的单元测试，后续会扩展 SSE 集成测试。
- **frontend/web/**：预留给 Next.js 前端工程，设计规范详见 `docs/design/ai_news_information_architecture.md`。
- **docs/api/**：存放 `/api/news/stream` 等接口契约，确保前后端一致。
- **services/ctp/**：提供期货交易通道配置及 Dockerfile，可按需启用。

---

## 配置说明

1. 在 `backend/.env.example` 中列出了必须的密钥与可选配置。
2. 须在根目录放置 `.env`（不纳入版本控制），供 `docker-compose` 渲染镜像时使用。
3. 运行时代码使用 `python-dotenv` 自动加载同目录下的 `.env`，本地调试时可直接运行 `backend/main.py`。

---

## 规划与文档

- **项目计划**：`AI_real_time_news_plan.md` 描述了阶段性任务、验收标准与风险。
- **需求简表**：`docs/news_module_requirements.md` 汇总了实时新闻板块的输入/输出与合规约束。
- **信息架构**：`docs/design/ai_news_information_architecture.md` 提供三端布局、组件树与主题规范。
- **API 契约**：`docs/api/news_stream_contract.md` 定义了 SSE 推送格式及示例。

请在每个阶段完成后更新文档与计划，以便后续功能扩展（例如：Web 前端实现、更多数据源接入、交易执行闭环等）。

---

## 常见问题

| 问题 | 排查建议 |
|------|----------|
| 容器启动报 401 | 检查 `.env` 中的 OpenAI/Firecrawl Key 是否正确 |
| SSE 契约不匹配 | 参考 `docs/api/news_stream_contract.md` 更新后端序列化逻辑 |
| LangSmith 报 403 | 默认配置开启了 LangSmith，可在 `.env` 中关闭 `LANGSMITH_TRACING` |
| 需要本地直接调试 | 进入 `backend` 创建虚拟环境，`pip install -r requirements.txt` 后运行 `python main.py` |

---

Copyright © Ringshell.
