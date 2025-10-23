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
- **oil_factors_metrics/**: AI-powered oil factor analysis and impact metrics

### Key Functions
- `ml_moving_average()`: ML-based moving average with trend analysis
- `firecrawl_search()`: Web search with time filtering
- `analyze_vix()`: VIX volatility analysis
- `get_yahoo_data()`: Price data from Yahoo Finance
- `oil_factor_analysis()`: AI-driven oil market factor analysis with impact metrics


