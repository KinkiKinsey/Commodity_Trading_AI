# Oil Metrics (Redis Read Client)

This module provides two small functions that read pre-computed Oil Factor Metrics from Redis for frontend and backend consumers. It does not generate metrics.

## Functions

### FactorMetrics_FrontendCheck() -> pandas.DataFrame
List which tickers have stored oil metrics in Redis.

- Output columns:
  - ticker (storage key form: dots/equals replaced with underscore)
  - has_impact_metrics (bool)
  - has_factor_time (bool)
  - has_queries_df (bool)
  - has_llm_summary (bool)
  - has_metadata (bool)
- Example:
```python
from Oil_Metrics.client import FactorMetrics_FrontendCheck
availability_df = FactorMetrics_FrontendCheck()
print(availability_df)
```
- Redis keys checked per ticker:
  - Crude_Oil:Future_Contract:{ticker_key}:Impact_Metrics.csv
  - Crude_Oil:Future_Contract:{ticker_key}:Factor_Time.csv
  - Crude_Oil:Future_Contract:{ticker_key}:Queries_DF.csv
  - Crude_Oil:Future_Contract:{ticker_key}:LLM_Trend_Analyst_Result
  - Crude_Oil:Future_Contract:{ticker_key}:Metadata

Notes:
- ticker_key = ticker.replace('.', '_').replace('=', '_')

### FactorMetrics_Queries_Call(ticker: str) -> pandas.DataFrame
Fetch the merged queries_df for a ticker from Redis.

- Input: ticker like "CLZ25.NYM"
- Output: pandas DataFrame (parsed from stored CSV)
- Raises: FileNotFoundError if not present
- Example:
```python
from Oil_Metrics.client import FactorMetrics_Queries_Call
queries_df = FactorMetrics_Queries_Call("CLZ25.NYM")
print(queries_df.head())
```

## Frontend Usage
- Build the ticker list: call FactorMetrics_FrontendCheck() and filter has_queries_df == True.
- When a user selects a ticker: call FactorMetrics_Queries_Call(ticker) and render the table.
- queries_df includes:
  - Impact metrics: factor, scope, trend_count, weighted_mean, weighted_variance, risk_reward_ratio, average_duration, total_duration
  - Time fields: start_date, end_date, duration_days, time_interval
  - LLM fields: driver_type, AI_Reason (one concise Chinese sentence with numerical evidence)

## Backend Usage
- Expose read-only endpoints wrapping these functions:
  - GET /oil-metrics/available → JSON list from FactorMetrics_FrontendCheck() where has_queries_df=True
  - GET /oil-metrics/{ticker}/queries → CSV or JSON from FactorMetrics_Queries_Call(ticker)
- Do not compute/generate here; this module is read-only.

## Data Pipeline Context (Upstream)
Stored data was produced upstream by a pipeline that:
1) fetched prices (Yahoo) and news (FMP),
2) segmented trends and built LLM prompts,
3) called DeepSeek to classify drivers and produce AI_Reason (Chinese, no “层级/level”),
4) computed impact metrics,
5) merged metrics + time ranges + LLM trends into queries_df,
6) wrote artifacts to Redis (keys below).

## Redis Keys
Base: Crude_Oil:Future_Contract:{ticker_key}:
- Impact_Metrics.csv
- Factor_Time.csv
- Queries_DF.csv (canonical for frontend)
- LLM_Trend_Analyst_Result
- Metadata

## Environment
- RINGSHELL_REDIS_HOST, RINGSHELL_REDIS_PORT, RINGSHELL_REDIS_USERNAME, RINGSHELL_REDIS_PASSWORD
- Requires: redis, pandas, python-dotenv

## Error Handling
- FactorMetrics_Queries_Call raises FileNotFoundError if the CSV is missing.
- FactorMetrics_FrontendCheck returns an empty DataFrame if no keys found.
