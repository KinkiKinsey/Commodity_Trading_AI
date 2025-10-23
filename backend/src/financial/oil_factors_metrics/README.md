# Oil Factors Metrics System

A comprehensive AI-powered system for analyzing crude oil market factors and their impact on oil futures prices using LLM-driven trend analysis and quantitative impact metrics.

## 🎯 What It Does

The Oil Factors Metrics System analyzes WTI crude oil futures to:

- **Identify Market Drivers**: Extract macro and micro factors driving oil price movements
- **Quantify Impact**: Calculate statistical impact metrics for each factor
- **Time-Series Analysis**: Map factors to specific time periods and durations
- **Multi-Language Support**: Generate factor names in Chinese or English
- **Incremental Updates**: Efficiently update analysis with new data only
- **Risk Assessment**: Provide risk-reward ratios and volatility metrics

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   LLM Analysis  │    │  Impact Metrics │
│                 │    │                 │    │                 │
│ • Yahoo Finance │───▶│ • Trend Detection│───▶│ • Factor Mapping│
│ • WTI News API  │    │ • News Analysis │    │ • Impact Calc   │
│ • Redis Cache   │    │ • Driver ID     │    │ • Risk Metrics  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Price Data    │    │  LLM Trends     │    │  Final Output   │
│                 │    │                 │    │                 │
│ • 700 days      │    │ • Current       │    │ • Impact DF     │
│ • OHLCV data    │    │ • Historical    │    │ • Time DF       │
│ • SPY benchmark │    │ • Factor Names  │    │ • 7 Datasets    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Data Pipeline

### 1. **Data Collection Phase**
```
Yahoo Finance API → Price Data (700 days)
FMP News API → WTI News Articles
Redis Cache → Cached Analysis Results
```

### 2. **Trend Detection Phase**
```
Price Data → Local Extrema Detection → Trend Segments
News Data → Date Filtering → News-to-Trend Mapping
```

### 3. **LLM Analysis Phase**
```
Trend Segments → LLM API → Factor Identification
News Content → Driver Classification → Impact Hierarchy
```

### 4. **Impact Calculation Phase**
```
Factor Data → Statistical Analysis → Impact Metrics
Time Ranges → Duration Analysis → Risk Metrics
```

### 5. **Output Generation Phase**
```
Metrics → DataFrame Creation → CSV Storage → Redis Cache
```

## ⚙️ Core Mechanisms

### **Trend Detection Algorithm**
- Uses `argrelextrema` to find local minima/maxima in price data
- Creates trend segments between extrema points
- Maps news articles to specific trend periods
- Calculates price statistics for each trend

### **LLM Factor Analysis**
- **Hierarchy-Based Classification**: 6-level impact hierarchy (Supply/Demand → Financial → Macro → Policy → Sentiment → Other)
- **Expectation vs Delivery**: Classifies factors as anticipated vs actual events
- **Performance Comparison**: Evaluates if events exceeded/fell short of expectations
- **Multi-Language Processing**: Generates factor names in Chinese or English

### **Impact Metrics Calculation**
- **Beta-Adjusted Returns**: Uses CAPM model with market beta
- **Weighted Averages**: Duration-weighted impact calculations
- **Risk Metrics**: Variance, volatility, and risk-reward ratios
- **Statistical Significance**: Trend count and confidence metrics

### **Incremental Update System**
- **News Filtering**: Only processes news from last update date onwards
- **Factor Mapping**: Uses LLM to map new factors to existing ones
- **Weighted Merging**: Combines old and new metrics with duration weights
- **Efficient Processing**: Avoids reprocessing historical data

## 📥 Input Parameters

### **Primary Function**
```python
get_oil_factors(ticker="CLZ25.NYM", language="Chinese", force_refresh=False)
```

**Parameters:**
- `ticker` (str): Oil futures ticker symbol (default: "CLZ25.NYM")
- `language` (str): Output language - "Chinese" or "English" (default: "Chinese")
- `force_refresh` (bool): Force regeneration ignoring cache (default: False)

### **Incremental Update**
```python
incremental_update_oil_metrics(ticker, previous_update_time, old_metrics_df, old_time_df, language)
```

**Parameters:**
- `ticker` (str): Oil futures ticker
- `previous_update_time` (str): ISO timestamp of last update
- `old_metrics_df` (DataFrame): Previous impact metrics
- `old_time_df` (DataFrame): Previous time ranges
- `language` (str): Processing language

## 📤 Output Structure

### **Impact Metrics DataFrame**
```python
impact_metrics_df = {
    'factor': str,           # Factor name (Chinese/English)
    'scope': str,           # 'macro' or 'micro'
    'trend_count': int,     # Number of trends
    'weighted_mean': float, # Duration-weighted impact mean
    'weighted_variance': float, # Duration-weighted variance
    'risk_reward_ratio': float, # Risk/reward ratio
    'average_duration': float, # Average trend duration (days)
    'total_duration': int,  # Total duration across all trends
    'trend_weight_score': float, # Trend frequency score
    'score_weighted_mean': float, # Score-weighted impact
    'score_weighted_variance': float # Score-weighted variance
}
```

### **Factor Time DataFrame**
```python
factor_time_df = {
    'factor_name': str,     # Factor name
    'scope': str,          # 'macro' or 'micro'
    'start_date': str,     # Period start date
    'end_date': str,       # Period end date
    'duration_days': int,  # Period length in days
    'time_interval': str   # Date range string
}
```

### **7 Additional Datasets**
1. **Risk Share Index**: Factor risk contribution percentages
2. **Macro Volatility DF**: Macro factor volatility metrics
3. **Micro Volatility DF**: Micro factor volatility metrics
4. **Impact Metrics DF**: Core impact metrics (same as above)
5. **Macro Total Impact DF**: Macro factor total impact
6. **Micro Total Impact DF**: Micro factor total impact
7. **Factor Risk Reward DF**: Risk-reward analysis by factor

## 🗂️ File Structure

```
oil_factors_metrics/
├── README.md                    # This documentation
├── oil_factor_api.py           # Main API interface
├── get_factor_metrics.py       # Core metrics generation
├── LLM_Trend_Summary.py        # LLM trend analysis
├── Oil_Impact_Metrics.py       # Impact calculations
├── Oil_Incremental_Update.py   # Incremental update system
├── Oil_LLM_Source/            # LLM integration
│   ├── LLM_Call_Agent.py      # LLM API client
│   └── shared_clients.py      # Shared client pool
└── HANDOFF_GUIDE.md           # Development handoff guide
```

## 🔌 Dependencies & APIs

### **External APIs**
- **Yahoo Finance API**: Price data for oil futures and SPY benchmark
- **FMP (Financial Modeling Prep) API**: WTI news articles
- **DeepSeek API**: LLM analysis for factor identification
- **OpenAI API**: Alternative LLM provider (optional)

### **Python Dependencies**
```python
# Core Data Processing
pandas>=1.5.0
numpy>=1.21.0
scipy>=1.9.0

# API Clients
requests>=2.28.0
yfinance>=0.2.0
redis>=4.0.0

# LangChain Integration
langchain-core>=0.3.0
langchain-openai>=0.1.0

# Environment
python-dotenv>=0.19.0
```

### **Environment Variables**
```bash
# Required
RINGSHELL_FMP_API_KEY=your_fmp_api_key
RINGSHELL_REDIS_HOST=your_redis_host
RINGSHELL_REDIS_PORT=6379
RINGSHELL_REDIS_USERNAME=your_redis_username
RINGSHELL_REDIS_PASSWORD=your_redis_password

# Optional
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
```

## 🚀 Usage Examples

### **Basic Usage**
```python
from oil_factors_metrics.oil_factor_api import get_oil_factors_sync

# Get oil factors
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM", "Chinese")
print(f"Got {len(impact_df)} factors and {len(time_df)} time ranges")
```

### **LangChain Tool Integration**
```python
from src.financial.tools import oil_factor_analysis

# Use as LangChain tool
result = oil_factor_analysis.invoke({
    'ticker': 'CLZ25.NYM',
    'language': 'English'
})
```

### **Incremental Update**
```python
from oil_factors_metrics.Oil_Incremental_Update import incremental_update_oil_metrics

# Update with new data only
updated_impact_df, updated_time_df = await incremental_update_oil_metrics(
    ticker="CLZ25.NYM",
    previous_update_time="2025-10-08T15:26:47",
    old_impact_metrics_df=old_df,
    old_factor_time_df=old_time_df,
    language="Chinese"
)
```

## 📈 Performance Characteristics

- **Processing Time**: ~30-60 seconds for full analysis (700 days)
- **Cache Efficiency**: <5 seconds for cached results
- **Memory Usage**: ~200MB peak during LLM processing
- **API Calls**: ~50-100 LLM API calls per analysis
- **Data Volume**: ~12 factors, ~36 time ranges typical output

## 🔧 Configuration

### **Trend Detection Parameters**
- **Lookback Period**: 700 days (configurable)
- **Extrema Order**: 5 (sensitivity of trend detection)
- **News Keywords**: 57 keywords across 6 categories

### **LLM Analysis Parameters**
- **Batch Size**: 4 trends per LLM call
- **Max Tokens**: 1000 per response
- **Temperature**: 0.2 (low randomness)
- **Timeout**: 30 seconds per API call

### **Caching Strategy**
- **Cache Duration**: 7 days for impact metrics
- **Refresh Threshold**: 24 hours for LLM trends
- **Storage Format**: CSV strings in Redis

## 🛠️ Development Notes

- **Error Handling**: Comprehensive try-catch with fallback mechanisms
- **Logging**: Detailed progress logging with emoji indicators
- **Testing**: Removed test code for production deployment
- **Scalability**: Designed for horizontal scaling with Redis
- **Maintenance**: Self-updating with incremental processing

## 📞 Support

For technical support or questions about the Oil Factors Metrics System, refer to the `HANDOFF_GUIDE.md` file or contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Status**: Production Ready ✅