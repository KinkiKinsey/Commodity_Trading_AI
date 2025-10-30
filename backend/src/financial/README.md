# Financial Module

## Quick Start

### Update Functions
1. Edit functions in `analyzers/`, `indicators/`, or `data_sources/`
2. Update `__init__.py` exports if needed
3. Test changes

### Run Tests in Docker
```bash
# Test all financial tools
docker-compose run --rm backend pytest tests/test_financial_tools.py -s

# Test specific module
docker-compose run --rm backend python -m src.financial.analyzers.vix_analyzer
```

### Available Modules
- **analyzers/**: Market analysis (contango, VIX, liquidity, macro risk)
- **indicators/**: Technical indicators (RSI, Bollinger, ML MA, EQH/EQL)
- **data_sources/**: Data fetching (Yahoo Finance, WTI news)
- **Oil_Metrics/**: Redis read-only client for precomputed oil factor metrics

### Key Functions
- `ml_moving_average()`: ML-based moving average with trend analysis
- `firecrawl_search()`: Web search with time filtering
- `analyze_vix()`: VIX volatility analysis
- `get_yahoo_data()`: Price data from Yahoo Finance
- `oil_metrics_list_available_tickers()`: List tickers with stored oil metrics in Redis
- `oil_metrics_fetch_queries_csv(ticker)`: Fetch stored queries_df for a ticker as CSV text

### Oil Metrics (Read-Only) Usage

Use the LangChain tools exported by `src.financial.tools` or call the client directly.

1) List available tickers (LangChain tool)
```python
from src.financial.tools import oil_metrics_list_available_tickers
tickers = oil_metrics_list_available_tickers()
print(tickers)
```

2) Fetch queries_df CSV for one ticker (LangChain tool)
```python
from src.financial.tools import oil_metrics_fetch_queries_csv
csv_text = oil_metrics_fetch_queries_csv("CLZ25.NYM")
print(csv_text[:500])
```

3) Direct Python client (no LangChain)
```python
from Oil_Metrics.client import FactorMetrics_FrontendCheck, FactorMetrics_Queries_Call
availability_df = FactorMetrics_FrontendCheck()
queries_df = FactorMetrics_Queries_Call("CLZ25.NYM")
```

Redis keys per ticker (storage key = ticker with '.'/'=' replaced by '_'):
- `Crude_Oil:Future_Contract:{ticker_key}:Impact_Metrics.csv`
- `Crude_Oil:Future_Contract:{ticker_key}:Factor_Time.csv`
- `Crude_Oil:Future_Contract:{ticker_key}:Queries_DF.csv`
- `Crude_Oil:Future_Contract:{ticker_key}:LLM_Trend_Analyst_Result`
- `Crude_Oil:Future_Contract:{ticker_key}:Metadata`


