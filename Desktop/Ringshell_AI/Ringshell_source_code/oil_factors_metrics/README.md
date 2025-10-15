# Oil Factor Metrics System

Complete incremental update system for crude oil factor analysis with LLM-based merging.

---

## 🚀 Quick Start (For Next Engineer)

### **Simple Usage:**

```python
from oil_factor_api import get_oil_factors

# Async context:
impact_df, time_df = await get_oil_factors("CLZ25.NYM")

# Sync context:
from oil_factor_api import get_oil_factors_sync
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")
```

**That's it! Everything else is automatic.**

---

## 📁 File Structure

```
oil_factors_metrics/
├── oil_factor_api.py          ⭐ USE THIS! Simple wrapper
├── get_factor_metrics.py      🔧 Main logic (called by api.py)
├── Oil_Incremental_Update.py  🤖 Merge engine (called internally)
├── LLM_Trend_Summary.py        📰 Trend generation (called internally)
├── Oil_Impact_Metrics.py       📊 Metrics calculation (called internally)
│
├── Test.ipynb                  💻 Testing notebook
└── README.md                   📖 This file
```

---

## 🎯 What It Does

### **Automatic Smart Caching:**

- **Cache < 14 days:** Returns cached data (0.1 seconds)
- **Cache ≥ 14 days:** Incremental update (30-60 seconds)
- **No cache:** Full generation (60-90 seconds)

### **Incremental Update Process:**

1. Retrieves previous update date from Redis metadata
2. Fetches NEW news from previous date to today
3. Creates NEW LLM trends from filtered news
4. Generates NEW impact metrics + factor time
5. Uses LLM to map new factors → old factors
6. Merges with weighted average
7. Stores updated data to Redis

---

## 📊 Inputs & Outputs

### **Input:**
```python
ticker = "CLZ25.NYM"  # Oil futures ticker
language = "Chinese"   # or "English"
```

### **Output:**
```python
impact_metrics_df (DataFrame):
  - factor: Factor name
  - scope: "macro" or "micro"
  - trend_count: Number of trends
  - weighted_mean: Impact mean
  - weighted_variance: Impact variance
  - risk_reward_ratio: Risk/reward ratio
  - average_duration: Average days
  - total_duration: Total days

factor_time_df (DataFrame):
  - factor_name: Factor name
  - scope: "macro" or "micro"
  - start_date: Period start
  - end_date: Period end
  - duration_days: Period length
  - time_interval: Date range string
```

---

## 🔧 System Features

### **1. News Sources (Enhanced):**
- ✅ WTI Stock News (direct oil news)
- ✅ General Market News (57 keywords):
  - Oil keywords (9): oil, crude, opec, energy...
  - Macro keywords (12): fed, inflation, economy...
  - Dollar keywords (9): dollar, usd, forex...
  - Geo keywords (16): russia, iran, middle east...
  - China keywords (7): china, stimulus...
  - Market keywords (6): commodities, futures...

### **2. Incremental Update:**
- ✅ LLM factor mapping (cross-language support)
- ✅ Weighted average merging
- ✅ Automatic deduplication
- ✅ Version tracking in metadata

### **3. Data Storage (Redis):**
```
Crude_Oil:Future_Contract:{TICKER}:Impact_Metrics.csv
Crude_Oil:Future_Contract:{TICKER}:Factor_Time.csv
Crude_Oil:Future_Contract:{TICKER}:Metadata
Crude_Oil:Future_Contract:{TICKER}:LLM_Trend_Analyst_Result
```

---

## 📖 Usage Examples

### **Example 1: Basic Usage**

```python
from oil_factor_api import get_oil_factors_sync

# Get factors
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")

print(f"Total factors: {len(impact_df)}")
print(impact_df.head())
```

### **Example 2: With Language**

```python
# English factors
impact_df, time_df = await get_oil_factors("CLZ25.NYM", language="English")

# Chinese factors
impact_df, time_df = await get_oil_factors("CLZ25.NYM", language="Chinese")
```

### **Example 3: Force Refresh**

```python
# Bypass cache, regenerate everything
impact_df, time_df = await get_oil_factors("CLZ25.NYM", force_refresh=True)
```

---

## ⚙️ Configuration

### **Cache Settings:**
- Freshness threshold: 14 days
- News cache: 24 hours
- Redis TTL: 7 days

### **API Keys Required:**
- FMP API (in `wti_news.py`)
- DeepSeek API (in `LLM_Trend_Summary.py`)

### **Redis Connection:**
- Configured in `RedisDatabaseStorage.py`

---

## 🔄 System Flow

```
User Call: get_oil_factors(ticker)
     ↓
Check Redis Cache
     ↓
├─ Cache Fresh (<14 days) → Return Cache (Fast: 0.1s)
│
└─ Cache Stale (≥14 days) → Incremental Update:
    ├─ Fetch news (previous → today)
    ├─ Create NEW LLM trends
    ├─ Generate NEW metrics
    ├─ LLM map & merge
    ├─ Store to Redis
    └─ Return merged data (Slow: 30-60s)
```

---

## 📊 Data Verification

All operations verified with:
- ✅ Real pandas DataFrame operations
- ✅ Actual data comparisons
- ✅ Mathematical validation
- ✅ No data loss checks
- ✅ Duplicate detection
- ✅ NULL value checks

---

## 🎯 For Next Engineer

### **What You Need to Know:**

1. **Import ONE file:** `oil_factor_api.py`
2. **Call ONE function:** `get_oil_factors(ticker)`
3. **Get TWO DataFrames:** `impact_df, time_df`

### **The system handles:**
- News fetching (WTI + General)
- Trend analysis (LLM)
- Factor extraction (LLM)
- Impact calculation (CAPM)
- Incremental updates (LLM mapping + weighted merge)
- Redis storage (CSV + Metadata)

### **You don't need to understand:**
- How news is filtered
- How trends are created
- How factors are mapped
- How merging works
- How caching works

**Just call the function and get the data!**

---

## 📝 Notes

- System uses DeepSeek LLM for all analysis
- Supports cross-language factor matching (CN ↔ EN)
- Auto-updates every 14 days
- News auto-refreshes every 24 hours
- All data stored in Redis with 7-day expiration

---

## ✅ System Status

**Status:** Production Ready  
**Last Updated:** October 7, 2025  
**Version:** 2.0 (Incremental Update System)  
**Language:** Python 3.10+  
**Dependencies:** pandas, numpy, requests, asyncio, langchain  

---

**Questions? Check `Test.ipynb` for examples.**

