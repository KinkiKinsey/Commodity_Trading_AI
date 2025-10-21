# `/api/news/stream` 集成测试指引（阶段 3 草案）

> 目的：验证 SSE 推送遵循契约，并确保信号与新闻映射正确。

---

## 1. 运行方式

```bash
# 1. 启动后端容器（或本地 FastAPI 服务）
docker-compose up backend

# 2. 使用 curl 监听 SSE
curl -N -H "Accept: text/event-stream" http://localhost:8000/api/news/stream
```

- 观察返回的事件中是否存在 `event: heartbeat`，间隔 ≤10s。
- 捕获 `event: news` 的数据，保存到 `tmp/news-event.json` 以供验证。

---

## 2. JSON Schema 校验

```bash
# 需要 jq 与 ajv-cli（或 python jsonschema）
cat tmp/news-event.json | jq '.data' > tmp/payload.json
ajv validate -s docs/api/news_stream_contract.schema.json -d tmp/payload.json
```

> 如果使用 Python，可运行：
```python
from jsonschema import validate, ValidationError
import json

with open("docs/api/news_stream_contract.schema.json") as schema_file:
    schema = json.load(schema_file)
with open("tmp/payload.json") as payload_file:
    payload = json.load(payload_file)

validate(instance=payload, schema=schema)
```

---

## 3. 信号映射检查

1. 解析 `payload["signal"]["signalId"]` 与 `payload["eventId"]`。
2. 调用指数接口（如 `/api/price` 或 `/api/signals`）获取信号列表，确保存在相同 `signalId` 且 `newsId` 匹配。
3. 若 `signal` 字段缺失，应记录为警告，由后端确认是否允许。

---

## 4. 合规场景

- **Case 1：正常内容**
  - `complianceStatus = "clean"`，Modal 应正常展示；截图保存到 QA 报告。
- **Case 2：脱敏内容**
  - 后端造数据使 `complianceStatus = "masked"`，确认前端显示提示文字且链式推理仍可展开。
- **Case 3：屏蔽内容**
  - `complianceStatus = "blocked"`，前端应该显示“内容暂不可用”，并禁用“查看推理”按钮。

测试结果需记录并附上截图/日志，存放于 `tests/integration/artifacts/`。

---

## 5. 待完善

| 项目 | 说明 | 状态 |
|------|------|------|
| JSON Schema 文件 | `docs/api/news_stream_contract.schema.json` 尚未落地，需要后端根据文档导出 | ☐ |
| 自动化脚本 | 计划使用 pytest + httpx 实现自动化 SSE 验证 | ☐ |
| 假数据生成 | 需要后端提供 mock endpoint 或脚本 | ☐ |

---

> 测试完成后请在阶段计划中更新状态，并同步 QA。
