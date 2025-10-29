# Oil Factor Metrics System - Complete Documentation

## 📋 Overview

The Oil Factor Metrics System is an AI-powered analysis pipeline that identifies, quantifies, and explains factors driving crude oil futures price movements. The system outputs a **Queries DataFrame (`queries_df`)** - a unified dataset that combines impact metrics, time ranges, and LLM-generated explanations for each factor.

**Key Innovation:** Instead of returning multiple separate DataFrames, the system provides a single `queries_df` that contains all factor information in one place, making it easy for frontend developers and other modules to consume.

---

## 🎯 What is `queries_df`?

The `queries_df` is a **flattened pandas DataFrame** that merges three data sources:

1. **Impact Metrics** - Statistical measures of how each factor affects oil prices
2. **Factor Time Ranges** - When and how long each factor was active
3. **LLM Trend Analysis** - AI-generated explanations of what drove each price movement

**One row** in `queries_df` = **One factor** active during **one specific time period** with its **impact metrics** and **AI explanation**.

---

## 📥 Input Parameters

### Primary Function

```python
from oil_factors_metrics.oil_factor_api import get_oil_factors, get_oil_factors_sync

# Async version
queries_df = await get_oil_factors(
    ticker="CLZ25.NYM",        # Oil futures ticker symbol
    language="Chinese",         # "Chinese" or "English"
    force_refresh=False        # Skip cache if True
)

# Synchronous version (for non-async contexts)
queries_df = get_oil_factors_sync(
    ticker="CLZ25.NYM",
    language="Chinese",
    force_refresh=False
)
```

### Parameters Explained

| Parameter | Type | Default | Description | Examples |
|-----------|------|---------|-------------|----------|
| `ticker` | `str` | `"CLZ25.NYM"` | Oil futures ticker symbol | `"CLZ25.NYM"`, `"CLH26.NYM"`, `"CL=F"` |
| `language` | `str` | `"Chinese"` | Output language for factor names | `"Chinese"`, `"English"` |
| `force_refresh` | `bool` | `False` | Force regeneration, bypass cache | `True`, `False` |

---

## 📤 Output Structure: `queries_df`

### DataFrame Schema

The `queries_df` contains the following columns:

#### **Core Factor Columns**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `factor` | `str` | Factor name (in specified language) | `"OPEC+增产预期"` or `"OPEC+ Production Increase Expectation"` |
| `scope` | `str` | Factor scope/category | `"macro"` or `"micro"` |

#### **Impact Metrics Columns** (from Impact_Metrics)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `trend_count` | `int` | Number of time periods this factor appeared | `3` |
| `weighted_mean` | `float` | Duration-weighted average price impact | `0.003456` |
| `weighted_variance` | `float` | Duration-weighted variance of impact | `0.000234` |
| `risk_reward_ratio` | `float` | Risk-adjusted return ratio | `0.654` |
| `average_duration` | `float` | Average duration per trend (days) | `12.5` |
| `total_duration` | `int` | Total duration across all trends (days) | `65` |

#### **Time Range Columns** (from Factor_Time)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `start_date` | `str` | Start date of this specific time period | `"2025-05-10"` |
| `end_date` | `str` | End date of this specific time period | `"2025-05-25"` |
| `duration_days` | `int` | Length of this specific period (days) | `15` |
| `time_interval` | `str` | Human-readable date range | `"2025-05-10 to 2025-05-25"` |

#### **LLM Analysis Columns** (from LLM_Trend_Summary)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `driver_type` | `str` | Primary driver category | `"Supply Disruptions"`, `"Inventory Levels"`, `"Demand Surges"` |
| `AI_Reason` | `str` | AI-generated explanation of price movement | `"OPEC+ announced production cut of 1.2M barrels/day, driving WTI price from $68 to $72..."` |

### Example Row

```python
{
    'factor': 'OPEC+增产预期',
    'scope': 'micro',
    'trend_count': 3,
    'weighted_mean': -0.004306,
    'weighted_variance': 0.000646,
    'risk_reward_ratio': 0.169434,
    'average_duration': 9.0,
    'total_duration': 27,
    'start_date': '2024-11-22',
    'end_date': '2024-12-03',
    'duration_days': 11,
    'time_interval': '2024-11-22 to 2024-12-03',
    'driver_type': '需求担忧',
    'AI_Reason': '欧洲公布的制造业PMI数据低于预期，显示经济活动放缓，导致原油价格从68.34美元跌至67.37美元（跌幅1.42%），市场担忧全球石油需求减弱成为主要下跌驱动因素。'
}
```

### Typical Output Size

- **Rows**: 30-80 (one per factor-time range combination)
- **Columns**: 14 columns total
- **Factors**: 12-20 unique factors
- **Time Ranges**: 3-5 time ranges per factor on average

---

## 🔄 Complete Data Pipeline

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: Ticker, Language                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Data Collection & Cache Check                         │
│  • Check Redis cache for existing data                          │
│  • If cache < 14 days old: Use cached data                     │
│  • If cache >= 14 days: Trigger incremental update              │
│  • If no cache or force_refresh: Generate fresh data           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Price Data & News Collection                           │
│  • Yahoo Finance API: Fetch 700 days OHLCV data                 │
│  • FMP News API: Fetch WTI-related news articles              │
│  • Filter news by price data date range                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Trend Detection                                         │
│  • Use scipy.argrelextrema to find local minima/maxima          │
│  • Create trend segments (uptrends/downtrends)                  │
│  • Map news articles to specific trend periods                  │
│  • Calculate price statistics for each trend                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: LLM Trend Analysis                                     │
│  • Batch process trends (4 per batch)                           │
│  • LLM API (DeepSeek/OpenAI) identifies:                        │
│    - Primary driver (Supply/Demand/Inventory/etc.)              │
│    - Driver type classification                                 │
│    - Explanation with numerical context                         │
│  • Store in Redis as JSON                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Impact Metrics Calculation                             │
│  • Group trends by identified factors                          │
│  • Calculate beta-adjusted returns (CAPM model)                  │
│  • Compute weighted averages (duration-weighted)                │
│  • Generate risk metrics (variance, risk-reward ratio)          │
│  • Create Impact_Metrics DataFrame                              │
│  • Create Factor_Time DataFrame                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Merge to Queries DataFrame                            │
│  • Left join Impact_Metrics + Factor_Time (on factor name)       │
│  • Match time ranges to LLM trends (by start/end dates)          │
│  • Extract driver_type and AI_Reason from matched trends        │
│  • Create unified queries_df                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: Storage & Return                                       │
│  • Store queries_df as CSV in Redis (7-day expiry)              │
│  • Store Impact_Metrics.csv in Redis                             │
│  • Store Factor_Time.csv in Redis                                │
│  • Store Metadata (last_update, beta, language)                  │
│  • Return queries_df to caller                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT: queries_df                            │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Pipeline Steps

#### **Step 1: Cache Management**

The system uses Redis for intelligent caching:

- **Cache Keys**:
  - `Crude_Oil:Future_Contract:{ticker}:Impact_Metrics.csv`
  - `Crude_Oil:Future_Contract:{ticker}:Factor_Time.csv`
  - `Crude_Oil:Future_Contract:{ticker}:Queries_DF.csv`
  - `Crude_Oil:Future_Contract:{ticker}:LLM_Trend_Analyst_Result` (JSON)
  - `Crude_Oil:Future_Contract:{ticker}:Metadata` (JSON)

- **Cache Strategy**:
  - **Impact/Factor Time Data**: 7-day expiry
  - **LLM Trends**: 24-hour freshness check
  - **Incremental Updates**: Automatic when cache >= 14 days old
  - **Force Refresh**: Bypasses all caches

#### **Step 2: Data Sources**

1. **Yahoo Finance API** (`yfinance`)
   - Fetches OHLCV data for oil futures ticker
   - Default: 700 days of historical data
   - Also fetches SPY (market benchmark) for beta calculation

2. **FMP News API** (Financial Modeling Prep)
   - Fetches WTI/crude oil related news articles
   - Filters by keywords (57 keywords across 6 categories)
   - Date range: Matches price data period

#### **Step 3: Trend Detection Algorithm**

```python
# Uses scipy.argrelextrema to find local extrema
local_min = argrelextrema(prices, np.less, order=5)[0]
local_max = argrelextrema(prices, np.greater, order=5)[0]

# Creates trend segments between extrema points
# Maps news articles to trend periods
# Calculates price statistics (returns, volatility, SPY correlation)
```

#### **Step 4: LLM Analysis Process**

1. **Batch Processing**: Trends processed in batches of 4
2. **LLM Prompt**: Includes:
   - Price statistics (start/end price, returns, volatility)
   - News articles from the trend period
   - Impact hierarchy guidance
3. **Output Extraction**: 
   - Primary driver identification
   - Driver type classification
   - Detailed explanation with context

#### **Step 5: Impact Calculation**

Uses CAPM model with market beta:
- **Beta Calculation**: Correlation with SPY benchmark
- **Risk-Adjusted Returns**: `return = beta * market_return + alpha`
- **Weighted Metrics**: Duration-weighted averages
- **Risk Metrics**: Variance, volatility, risk-reward ratios

#### **Step 6: Queries DataFrame Creation**

The `create_queries_df()` function:

1. **Merges** `impact_metrics_df` with `factor_time_df` (left join on factor name)
2. **Matches** each time range to LLM trends (by start/end dates, with 1-day tolerance)
3. **Extracts** `driver_type` and `AI_Reason` from matched trends
4. **Returns** flattened DataFrame

---

## 🗄️ Database Structure (Redis)

### Redis Key Naming Convention

```
Crude_Oil:Future_Contract:{ticker}:{dataset_name}
```

Where:
- `{ticker}`: Normalized ticker (e.g., `CLZ25_NYM` for `"CLZ25.NYM"`)
- `{dataset_name}`: One of:
  - `Impact_Metrics.csv` - Impact metrics DataFrame (CSV format)
  - `Factor_Time.csv` - Factor time ranges DataFrame (CSV format)
  - `Queries_DF.csv` - Final queries DataFrame (CSV format)
  - `LLM_Trend_Analyst_Result` - LLM analysis results (JSON format)
  - `Metadata` - System metadata (JSON format)

### Redis Data Formats

1. **CSV Data**: Stored as strings, converted back to DataFrame on retrieval
2. **JSON Data**: Stored as JSON strings, parsed on retrieval
3. **Expiration**: 7 days for CSV datasets, 24 hours freshness check for LLM trends

### Example Redis Keys

```
Crude_Oil:Future_Contract:CLZ25_NYM:Impact_Metrics.csv
Crude_Oil:Future_Contract:CLZ25_NYM:Factor_Time.csv
Crude_Oil:Future_Contract:CLZ25_NYM:Queries_DF.csv
Crude_Oil:Future_Contract:CLZ25_NYM:LLM_Trend_Analyst_Result
Crude_Oil:Future_Contract:CLZ25_NYM:Metadata
```

---

## 🔌 API Integration

### Python API

```python
# Main entry point
from oil_factors_metrics.oil_factor_api import get_oil_factors, get_oil_factors_sync

# Async usage
queries_df = await get_oil_factors("CLZ25.NYM", language="Chinese")

# Sync usage
queries_df = get_oil_factors_sync("CLZ25.NYM", language="English")
```

### LangChain Tool Integration

```python
from src.financial.tools import oil_factor_analysis

# Use as LangChain tool in agent workflows
result = oil_factor_analysis.invoke({
    'ticker': 'CLZ25.NYM',
    'language': 'English'
})
```

---

## 🌐 Frontend Usage

### React/Next.js Example

```typescript
// Fetch queries_df via API
const response = await fetch('/api/oil-factors?ticker=CLZ25.NYM&language=English');
const queriesData = await response.json();

// queriesData is an array of query objects
queriesData.forEach(query => {
  console.log(`Factor: ${query.factor}`);
  console.log(`Period: ${query.start_date} to ${query.end_date}`);
  console.log(`Impact: ${query.weighted_mean}`);
  console.log(`Driver: ${query.driver_type}`);
  console.log(`Explanation: ${query.AI_Reason}`);
});
```

### Data Visualization Use Cases

1. **Factor Impact Chart**: Plot `weighted_mean` by `factor`
2. **Time Series View**: Show factors over time using `start_date`/`end_date`
3. **Risk Analysis**: Visualize `risk_reward_ratio` by `scope` (macro vs micro)
4. **Driver Distribution**: Count factors by `driver_type`
5. **Detailed Tooltips**: Show `AI_Reason` on hover for each factor period

### Filtering & Querying

```typescript
// Filter by scope
const macroFactors = queriesData.filter(q => q.scope === 'macro');

// Filter by date range
const recentFactors = queriesData.filter(q => 
  new Date(q.start_date) >= new Date('2025-01-01')
);

// Group by factor
const factorsByType = queriesData.reduce((acc, q) => {
  if (!acc[q.factor]) acc[q.factor] = [];
  acc[q.factor].push(q);
  return acc;
}, {});

// Sort by impact
const sortedByImpact = queriesData.sort((a, b) => 
  Math.abs(b.weighted_mean) - Math.abs(a.weighted_mean)
);
```

---

## 🔧 Other Modules Usage

### Backend Analysis Module

```python
from oil_factors_metrics.oil_factor_api import get_oil_factors_sync
import pandas as pd

# Get data
queries_df = get_oil_factors_sync("CLZ25.NYM", language="English")

# Analyze factors
high_impact = queries_df[queries_df['weighted_mean'].abs() > 0.005]
recent_factors = queries_df[queries_df['start_date'] >= '2025-01-01']

# Group analysis
by_scope = queries_df.groupby('scope')['weighted_mean'].mean()
by_driver = queries_df.groupby('driver_type').size()

# Export for further analysis
queries_df.to_csv('analysis_output.csv', index=False)
```

### Reporting Module

```python
# Generate factor report
queries_df = get_oil_factors_sync("CLZ25.NYM")

report = {
    'total_factors': queries_df['factor'].nunique(),
    'total_periods': len(queries_df),
    'avg_impact': queries_df['weighted_mean'].mean(),
    'top_factor': queries_df.loc[queries_df['weighted_mean'].idxmax(), 'factor'],
    'recent_explanations': queries_df.nlargest(5, 'start_date')['AI_Reason'].tolist()
}
```

### API Endpoint Example

```python
# FastAPI endpoint
from fastapi import FastAPI
from oil_factors_metrics.oil_factor_api import get_oil_factors_sync

app = FastAPI()

@app.get("/api/oil-factors/{ticker}")
async def get_oil_factors_api(ticker: str, language: str = "English"):
    queries_df = get_oil_factors_sync(ticker, language)
    return queries_df.to_dict('records')  # Convert to JSON-serializable format
```

---

## 📊 Data Structure Deep Dive

### Factor Scope Classification

- **`macro`**: Macroeconomic factors (monetary policy, geopolitical, trade tensions)
- **`micro`**: Micro-level factors (inventory, supply disruptions, specific company news)

### Driver Type Categories

Based on LLM impact hierarchy:

1. **Level 0-1**: Physical Supply/Demand Shocks
   - `Supply Disruptions` - OPEC+ cuts, wars, refinery outages
   - `Demand Surges` - Economic expansion, seasonal effects
   - `Inventory Levels` - EIA/IEA reports, SPR purchases

2. **Level 2-3**: Financial & Market Mechanisms
   - `Futures Market Positioning` - Speculation, backwardation/contango
   - `Currency & Inflation Effects` - USD strength, interest rates

3. **Level 4-5**: Macroeconomic & Policy
   - `Fiscal & Monetary Stimulus` - Central bank policy, QE
   - `Energy & Climate Policy` - ESG constraints, carbon taxes
   - `Geopolitical Strategy` - Sanctions, regional tensions

4. **Level 6**: Sentiment & Expectations
   - `Market Sentiment` - Risk-on/risk-off, momentum
   - `Substitution & Correlation` - Natural gas prices, shipping costs

### AI_Reason Structure

Each `AI_Reason` contains:
- **Numerical Context**: Price changes, percentages, inventory numbers, dates
- **Key Entities**: OPEC+, EIA, country names, leaders, companies
- **Specific Events**: What happened and why it drove the price movement
- **Plain Language**: No technical jargon, natural explanation

---

## ⚙️ Configuration & Environment

### Required Environment Variables

```bash
# Redis Configuration
RINGSHELL_REDIS_HOST=your_redis_host
RINGSHELL_REDIS_PORT=6379
RINGSHELL_REDIS_USERNAME=your_username
RINGSHELL_REDIS_PASSWORD=your_password

# API Keys
RINGSHELL_FMP_API_KEY=your_fmp_api_key
DEEPSEEK_API_KEY=your_deepseek_key  # Optional, for LLM calls
OPENAI_API_KEY=your_openai_key  # Optional, fallback LLM
```

### Python Dependencies

```txt
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.9.0
yfinance>=0.2.0
redis>=4.0.0
requests>=2.28.0
langchain-core>=0.3.0
python-dotenv>=0.19.0
```

---

## 🚀 Performance Characteristics

- **First Call** (no cache): 30-60 seconds
- **Cached Call** (< 14 days): < 5 seconds
- **Incremental Update**: 20-40 seconds
- **Memory Usage**: ~200MB peak during LLM processing
- **API Calls**: ~50-100 LLM API calls per full analysis
- **Output Size**: 30-80 rows × 14 columns

---

## 💡 Usage Examples

### Example 1: Basic Python Script

```python
from oil_factors_metrics.oil_factor_api import get_oil_factors_sync

# Get data
queries_df = get_oil_factors_sync("CLZ25.NYM", language="Chinese")

# Print summary
print(f"Total queries: {len(queries_df)}")
print(f"Unique factors: {queries_df['factor'].nunique()}")
print(f"\nTop 5 factors by impact:")
print(queries_df.nlargest(5, 'weighted_mean')[['factor', 'weighted_mean', 'driver_type']])
```

### Example 2: Filter by Date

```python
queries_df = get_oil_factors_sync("CLZ25.NYM")

# Get factors from last 3 months
from datetime import datetime, timedelta
cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
recent = queries_df[queries_df['start_date'] >= cutoff_date]

print(f"Recent factors: {len(recent)}")
```

### Example 3: Analyze by Driver Type

```python
queries_df = get_oil_factors_sync("CLZ25.NYM")

# Group by driver type
by_driver = queries_df.groupby('driver_type').agg({
    'weighted_mean': 'mean',
    'factor': 'count'
}).sort_values('weighted_mean', ascending=False)

print(by_driver)
```

### Example 4: Export for Frontend

```python
import json

queries_df = get_oil_factors_sync("CLZ25.NYM", language="English")

# Convert to JSON for API response
json_data = queries_df.to_dict('records')

# Save to file
with open('oil_factors.json', 'w') as f:
    json.dump(json_data, f, indent=2)
```

---

## 🔍 Troubleshooting

### Empty DataFrame Returned

- **Cause**: LLM trend analysis not found in Redis
- **Solution**: Ensure `get_llm_trend_summary()` has been called, or use `force_refresh=True`

### Cache Not Updating

- **Cause**: Cache age check might be allowing stale data
- **Solution**: Use `force_refresh=True` to bypass cache

### Missing `driver_type` or `AI_Reason`

- **Cause**: Time range matching failed (dates don't align)
- **Solution**: Check LLM trend summary dates match factor time ranges

---

## 📞 Support & Further Reading

- **HANDOFF_GUIDE.md**: Development handoff documentation
- **HOW_TO_USE.md**: Quick start guide
- **MERGE_PLAN.md**: Technical details on queries_df creation

---

**Version**: 2.0.0  
**Last Updated**: October 2025  
**Status**: Production Ready ✅
