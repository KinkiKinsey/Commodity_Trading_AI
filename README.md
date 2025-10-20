# RingShell - AI Commodity Market Analyst

An AI-powered commodity trading analysis platform using LangGraph agents with real-time market intelligence and financial analysis tools.

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- `.env` file (see Configuration section)

### Run

```bash
# Start the application
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests
docker-compose exec app python tests/test_financial_tools.py
```

---

## 📁 Project Structure

```
ringshell/
├── src/
│   ├── core/
│   │   ├── commodity_agent.py      # LangGraph agent with search & analysis
│   │   └── utils.py                # Helper functions
│   │
│   ├── financial/                  # Financial analysis tools
│   │   ├── analyzers/              # Market analysis modules
│   │   │   ├── contango_backwardation.py
│   │   │   ├── macro_risk.py
│   │   │   ├── vix_analyzer.py
│   │   │   └── liquidity_monitor.py
│   │   ├── functions.py            # Core functions
│   │   └── tools.py                # LangChain tool wrappers
│   │
│   ├── models/
│   │   └── schema.py               # Pydantic schemas & state definitions
│   │
│   └── prompts/
│       └── templates.py            # Agent prompts & instructions
│
├── tests/                          # Test suites
├── main.py                         # Entry point
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-proj-...
FIRECRAWL_API_KEY=fc-...

# Redis (for macro analysis)
RINGSHELL_REDIS_HOST=your-redis-host
RINGSHELL_REDIS_PORT=14275
RINGSHELL_REDIS_USERNAME=default
RINGSHELL_REDIS_PASSWORD=your-password

# Optional: LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=ringshell
```

**Note:** `.env` is automatically loaded via `load_dotenv()` in the code. Never commit `.env` to git!

---

## 🤖 Commodity Agent Architecture

### Agent Workflow

```
User Query → LLM Analysis → Tool Calls → Research Synthesis → Structured Output
```

The agent uses:
- **firecrawl_search**: Web search for real-time market news
- **think_tool**: Strategic reflection and planning
- **Financial tools**: Market structure & macro analysis

### Output Schema

```python
class SOCommodity(BaseModel):
    direction: Literal["bullish", "bearish", "neutral"]
    confidence: float  # 0.0 to 1.0
    chain_of_thought: List[str]
    citations: List[str]
```

### Analysis Framework

The agent considers 8 key dimensions:
1. **Geopolitics** - OPEC/Russia/China relations
2. **Inventory** - EIA reports, storage levels
3. **Supply** - Production data
4. **Demand** - Global consumption trends
5. **Inflation** - Price pressures
6. **Markets** - Stock/energy correlation
7. **USD Rate** - Dollar strength
8. **Industry** - Manufacturing, EV adoption

---

## 🛠️ Financial Tools

| Tool | Purpose | Data Source |
|------|---------|-------------|
| **Contango/Backwardation** | Futures curve structure | Yahoo Finance |
| **Macro Risk Analysis** | Economic risk assessment | Redis Cache |
| **VIX Volatility** | Market sentiment gauge | Yahoo Finance |
| **Global Liquidity** | Funding stress monitor | Yahoo Finance |

### Usage Example

```python
from src.core.commodity_agent import commodity_agent
from langchain_core.messages import HumanMessage

result = await commodity_agent.ainvoke({
    "messages": [HumanMessage(content="分析原油市场走势")]
})

print(result["analysis"])  # SOCommodity object
```

---

## 📦 Dependencies

```
# Core
langgraph>=0.2.0
langchain>=0.3.0
langchain-openai>=0.2.0
firecrawl-py>=0.0.16

# Financial
pandas>=2.0.0
yfinance>=0.2.28
redis>=5.0.0
```

See `requirements.txt` for complete list.

---

## 🧪 Testing

```bash
# Standard function tests
docker-compose exec app python tests/test_financial_tools.py

# LangChain tool tests
docker-compose exec app python tests/test_langchain_tools.py
```

---

## 🐳 Docker Development

### Live Code Editing

The `docker-compose.yml` mounts your code directory:
```yaml
volumes:
  - .:/app  # Changes reflect immediately
```

No rebuild needed for code changes. Just save and restart.

### Rebuild (when requirements.txt changes)

```bash
docker-compose up --build
```

### Interactive Shell

```bash
docker-compose exec app bash
# or
docker-compose run --rm app bash
```

---

## 🔒 Security

- ✅ `.env` in `.gitignore` (never commit secrets)
- ✅ Environment variables via `load_dotenv()`
- ✅ No hardcoded credentials in code
- ⚠️ Use different credentials for dev/prod

---

## 📈 Performance

| Tool | Response Time | Network Calls |
|------|--------------|---------------|
| Contango Analysis | ~5-10s | 15 (Yahoo Finance) |
| Macro Risk | ~0.5s | 1 (Redis) |
| VIX Analysis | ~2-3s | 1 (Yahoo Finance) |
| Liquidity Monitor | ~8-12s | 4 (Yahoo Finance) |

---

## 🚫 Not Used

- **CTP Trading API** (`ctp/` directory) - Chinese futures trading integration (commented out in docker-compose.yml)

Enable if needed for live trading on Chinese markets.

---

## 🐛 Troubleshooting

### Container won't start
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Environment variables not loading
- Ensure `.env` exists in project root
- Check `load_dotenv()` is called in `commodity_agent.py`
- Verify file is not in `.dockerignore`

### Network errors
```bash
# Test connectivity
docker-compose exec app python -c "import yfinance as yf; print(yf.download('^VIX', period='1d'))"
```

---

## 📄 License

Proprietary - All rights reserved

---

**Built for intelligent commodity market analysis** 🛢️📊
