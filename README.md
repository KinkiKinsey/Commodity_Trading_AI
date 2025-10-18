# RingShell - AI-Powered Commodity Trading Analysis Platform

A sophisticated financial analysis platform combining LangGraph agents with comprehensive commodity market analysis tools. Built for intelligent trading decisions powered by real-time market data and AI-driven insights.

---

## 🎯 Overview

RingShell provides AI agents with advanced financial analysis capabilities through four core tools:
- **Contango/Backwardation Analysis** - Futures curve structure detection
- **Macro Risk Analysis** - Economic risk assessment for commodity markets
- **VIX Volatility Analysis** - Market sentiment and fear/greed gauge
- **Global Liquidity Monitor** - Early warning system for funding stress

---

## 🏗️ Project Structure

```
ringshell/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   └── commodity_agent.py          # LangGraph agent implementation
│   │
│   ├── financial/                      # Financial analysis tools
│   │   ├── __init__.py                 # Module exports
│   │   ├── functions.py                # Standard Python functions
│   │   ├── tools.py                    # LangChain tool wrappers
│   │   │
│   │   ├── analyzers/                  # Core analysis modules
│   │   │   ├── __init__.py
│   │   │   ├── contango_backwardation.py
│   │   │   ├── macro_risk.py
│   │   │   ├── vix_analyzer.py
│   │   │   └── liquidity_monitor.py
│   │   │
│   │   └── data_sources/               # Data fetching
│   │       ├── __init__.py
│   │       └── price_data.py           # Yahoo Finance integration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schema.py                   # Pydantic schemas
│   │
│   └── prompts/                        # Agent prompts
│
├── tests/
│   ├── __init__.py
│   ├── test_financial_tools.py         # Standard function tests
│   └── test_langchain_tools.py         # LangChain tool tests
│
├── ctp/                                # CTP Trading API (NOT USED)
│   └── ...                             # Chinese futures trading (disabled)
│
├── docker-compose.yml                  # Docker orchestration
├── Dockerfile                          # Main container definition
├── requirements.txt                    # Python dependencies
├── .dockerignore                       # Docker build exclusions
└── main.py                             # Application entry point
```

---

## 🐳 Docker Architecture

### Container Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Container: ringshell                                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  LangGraph Agent (commodity_agent.py)                   │ │
│  │  ├── Tool Selection & Execution                        │ │
│  │  ├── State Management                                  │ │
│  │  └── Response Generation                               │ │
│  │                                                        │ │
│  │  Financial Analysis Tools                             │ │
│  │  ├── contango_backwardation_analysis                  │ │
│  │  ├── macro_risk_analysis                              │ │
│  │  ├── vix_volatility_analysis                          │ │
│  │  └── global_liquidity_monitor                         │ │
│  │                                                        │ │
│  │  External Data Sources (via network)                  │ │
│  │  ├── Yahoo Finance API                                │ │
│  │  └── Redis Cloud Database                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Single Container Design

**Why single container?**
- Financial tools are **synchronous Python functions** (not services)
- Tools share common dependencies (pandas, numpy, yfinance)
- Direct function calls = zero network latency
- Simplified deployment and scaling

### External Services

The container connects to external services over the internet:
- **Yahoo Finance API** - Real-time and historical market data
- **Redis Cloud** - Cached macro economic analysis

**Note:** CTP (Chinese futures trading API) is included in the codebase but **NOT USED** in the current implementation.

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (for Mac/Windows) or Docker Engine (for Linux)
- 8GB+ RAM recommended
- Internet connection (for market data APIs)

### Build & Run

```bash
# Build the Docker image
docker-compose build

# Run tests
docker-compose run --rm app python tests/test_financial_tools.py
docker-compose run --rm app python tests/test_langchain_tools.py

# Start the application
docker-compose up

# Interactive shell
docker-compose run --rm app bash
```

---

## 📦 Dependencies

### Core Dependencies
```
langgraph>=0.2.0          # Agent framework
langchain>=0.3.0          # LLM orchestration
langchain-core>=0.3.0
langchain-community>=0.3.0
langchain-tavily>=0.2.0   # Web search
httpx>=0.27.0
```

### Financial Analysis Dependencies
```
pandas>=2.0.0             # Data manipulation
numpy>=1.24.0             # Numerical computing
yfinance>=0.2.28          # Yahoo Finance API
redis>=5.0.0              # Redis database client
requests>=2.31.0          # HTTP requests
```

### Performance Optimization
```
uvloop>=0.19.0            # Fast event loop (Unix only)
```

---

## 🔧 Configuration

### Environment Variables

Configure in `docker-compose.yml`:

```yaml
environment:
  # Redis Configuration (for macro risk analysis)
  - RINGSHELL_REDIS_HOST=redis-14275.c83.us-east-1-2.ec2.redns.redis-cloud.com
  - RINGSHELL_REDIS_PORT=14275
  - RINGSHELL_REDIS_USERNAME=default
  - RINGSHELL_REDIS_PASSWORD=<your_password>
  
  # Python Configuration
  - PYTHONUNBUFFERED=1
  - PYTHONPATH=/app
```

---

## 🛠️ Financial Tools

### 1. Contango/Backwardation Analysis

**Purpose:** Detect futures market structure to identify trading opportunities

**Supported Commodities:**
- Crude Oil (CL)
- Gold (GC)
- Natural Gas (NG)
- Gasoline/RBOB (RB)

**Usage:**
```python
from src.financial import contango_backwardation_analysis

# LangChain tool
result = contango_backwardation_analysis.invoke({"sector": "oil"})

# Standard function
from src.financial import contango_backwardation_tool
result = contango_backwardation_tool("oil")
```

**Returns:**
- Market structure (Contango/Backwardation/Flat)
- Price gaps between contract months
- Trading implications (storage plays, roll yield, arbitrage)

---

### 2. Macro Risk Analysis

**Purpose:** Comprehensive macro economic risk assessment for commodity markets

**Data Source:** Redis Cloud (pre-computed analysis)

**Usage:**
```python
from src.financial import macro_risk_analysis

# LangChain tool
analysis = macro_risk_analysis.invoke({})

# Standard function
from src.financial import macro_risk_analysis_tool
analysis = macro_risk_analysis_tool()
```

**Returns:**
- US GDP Growth trends
- Unemployment and inflation analysis
- Business cycle phase
- Three risk path scenarios
- Commodity market implications

---

### 3. VIX Volatility Analysis

**Purpose:** Market sentiment gauge (fear vs greed)

**Data Source:** Yahoo Finance (^VIX)

**Usage:**
```python
from src.financial import vix_volatility_analysis

# LangChain tool
report = vix_volatility_analysis.invoke({"days": 5000})

# Standard function
from src.financial import vix_analysis_tool
report = vix_analysis_tool(5000)
```

**Returns:**
- Current VIX level and status
- Z-score analysis (long-term & short-term)
- Historical context
- Trading implications

---

### 4. Global Liquidity Monitor

**Purpose:** Early warning system for global funding stress

**Indicators Monitored:**
- DXY (Dollar Index) - USD strength
- HYG (High Yield ETF) - Credit stress
- XLF (U.S. Banks) - Domestic banking
- IXG (Global Banks) - International banking

**Usage:**
```python
from src.financial import global_liquidity_monitor

# LangChain tool
report = global_liquidity_monitor.invoke({"days": 180})

# Standard function
from src.financial import liquidity_monitor_tool
report = liquidity_monitor_tool(180)
```

**Returns:**
- Composite stress score
- Individual indicator z-scores
- Liquidity condition assessment
- Risk recommendations

---

## 🧪 Testing

### Run All Tests

```bash
# Standard function tests
docker-compose run --rm app python tests/test_financial_tools.py

# LangChain tool tests
docker-compose run --rm app python tests/test_langchain_tools.py
```

### Test Results

```
Standard Functions: 4/4 ✅
LangChain Tools: 5/5 ✅
```

---

## 🔌 Integration with LangGraph

### Add Tools to Agent

```python
# In src/core/commodity_agent.py

from src.financial import (
    contango_backwardation_analysis,
    macro_risk_analysis,
    vix_volatility_analysis,
    global_liquidity_monitor
)

def _get_tools():
    """Get all tools for the commodity agent."""
    global _tools, _tools_by_name
    if _tools is None:
        tavily_search = TavilySearch(max_results=3, search_depth="basic")
        
        _tools = [
            # Web search
            tavily_search,
            
            # Financial analysis tools
            contango_backwardation_analysis,
            macro_risk_analysis,
            vix_volatility_analysis,
            global_liquidity_monitor
        ]
        
        _tools_by_name = {tool.name: tool for tool in _tools}
    return _tools, _tools_by_name
```

### Agent Workflow Example

```
User: "Should I buy crude oil futures?"

Agent: "Let me analyze the oil market..."
  ↓
Calls: contango_backwardation_analysis(sector="oil")
  ↓
Result: "Market shows backwardation, indicating tight supply..."
  ↓
Calls: vix_volatility_analysis(days=5000)
  ↓
Result: "VIX at 20.78 (neutral), no extreme fear..."
  ↓
Calls: global_liquidity_monitor(days=180)
  ↓
Result: "Stable liquidity environment, no funding stress..."
  ↓
Agent: "Based on backwardation structure and stable market conditions,
       crude oil futures show positive signals for long positions..."
```

---

## 📊 Performance Characteristics

| Tool | Avg Response Time | Data Points | Network Calls |
|------|------------------|-------------|---------------|
| Contango/Backwardation | ~5-10s | 14 contracts | 15 Yahoo Finance |
| Macro Risk Analysis | ~0.5s | Cached | 1 Redis |
| VIX Analysis | ~2-3s | 688 days | 1 Yahoo Finance |
| Liquidity Monitor | ~8-12s | 4 indicators | 4 Yahoo Finance |

---

## 🚫 What's NOT Used

### CTP Trading API

The `ctp/` directory contains a Chinese futures trading API integration that is **NOT CURRENTLY USED**:

```
ctp/                    # ❌ NOT USED
├── Dockerfile          # CTP service container (disabled)
├── src/                # C++ trading binaries
└── lib/                # CTP libraries
```

**Why disabled?**
- Currently commented out in `docker-compose.yml`
- Not required for financial analysis tools
- Can be enabled later if needed for live trading

To enable CTP service, uncomment the `ctp-service` section in `docker-compose.yml`.

---

## 🔒 Security Notes

- Redis credentials are configured via environment variables
- Use `.env` file for production (not committed to git)
- API keys should be stored securely
- Network access is required for external data sources

---

## 📈 Roadmap

- [ ] Add more commodity sectors (metals, agriculture)
- [ ] Implement real-time streaming data
- [ ] Add technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Create FastAPI endpoints for tool access
- [ ] Add authentication and rate limiting
- [ ] Implement caching layer for frequently accessed data
- [ ] Add monitoring and logging dashboards

---

## 🤝 Contributing

This is a private project. For questions or suggestions, please contact the development team.

---

## 📄 License

Proprietary - All rights reserved

---

## 🆘 Troubleshooting

### Docker Build Issues

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Network Issues

```bash
# Test external connectivity
docker-compose run --rm app python -c "import yfinance as yf; print(yf.download('^VIX', period='1d'))"
```

### Redis Connection Issues

```bash
# Test Redis connection
docker-compose run --rm app python -c "import redis; r = redis.Redis(host='redis-14275.c83.us-east-1-2.ec2.redns.redis-cloud.com', port=14275); print(r.ping())"
```

---

## 📞 Support

For technical support or questions:
- Check the test results: `docker-compose run --rm app python tests/test_financial_tools.py`
- Review logs: `docker-compose logs app`
- Verify environment variables in `docker-compose.yml`

---

**Built with ❤️ for intelligent commodity trading analysis**
