# 🎯 Oil Factor Metrics System - Handoff Guide

**Complete system for crude oil factor analysis with automatic incremental updates.**

---

## 🚀 Quick Start (< 2 minutes)

### **1. Install Dependencies:**

```bash
cd oil_factors_metrics
pip install -r requirements.txt
```

### **2. Use the API:**

```python
from oil_factor_api import get_oil_factors_sync

# Input: Ticker
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")

# Output: Two DataFrames
print(impact_df)  # Factor metrics
print(time_df)    # Factor time ranges
```

**Done! That's all you need.**

---

## 📊 What You Get

### **Input:**
```python
ticker = "CLZ25.NYM"  # String - Oil futures ticker
```

### **Output:**

**DataFrame 1: `impact_metrics_df`**
```
Rows: 12-20 factors
Columns: 8
  - factor (str): Factor name (e.g., "OPEC+增产预期")
  - scope (str): "macro" or "micro"
  - trend_count (int): Number of occurrences (e.g., 5)
  - weighted_mean (float): Average impact (e.g., 0.003456)
  - weighted_variance (float): Impact variance (e.g., 0.000234)
  - risk_reward_ratio (float): Risk/reward (e.g., 0.654)
  - average_duration (float): Avg days (e.g., 12.5)
  - total_duration (int): Total days (e.g., 65)
```

**DataFrame 2: `factor_time_df`**
```
Rows: 60-80 intervals
Columns: 6
  - factor_name (str): Factor name
  - scope (str): "macro" or "micro"
  - start_date (str): "2025-05-10"
  - end_date (str): "2025-05-25"
  - duration_days (int): 15
  - time_interval (str): "2025-05-10 to 2025-05-25"
```

---

## ⚙️ System Configuration

### **Required API Keys:**

**Already configured in code:**
- FMP API: `9dfbbfa29d93f4793f246e8fb5ca5e74`
- DeepSeek API: `sk-43e9043c7ab8480393d34367f2ae997e`

### **Redis Connection:**

**Already configured in:**
- `DataBase_Connection_Source/RedisDatabaseStorage.py`

**No setup needed - works out of the box!**

---

## 🔄 How It Works (Automatic)

### **Smart Caching:**

```
First Call:
  → Generates data (60s)
  → Stores to Redis
  → Returns data

Second Call (within 14 days):
  → Reads from Redis (0.1s) ← FAST!
  → Returns cached data

Call After 14 Days:
  → Incremental update (30s)
  → Merges new + old data
  → Stores to Redis
  → Returns updated data
```

**You don't manage this - it's automatic!**

---

## 📖 File Reference

| File | Purpose | Touch? |
|------|---------|--------|
| `oil_factor_api.py` | ⭐ Your API | ✅ Use |
| `HOW_TO_USE.md` | Usage examples | ✅ Read |
| `README.md` | System overview | ✅ Read |
| `requirements.txt` | Dependencies | ✅ Install |
| `get_factor_metrics.py` | Core logic | ❌ Don't touch |
| `Oil_Incremental_Update.py` | Merge engine | ❌ Don't touch |
| `LLM_Trend_Summary.py` | Trend generation | ❌ Don't touch |
| `Oil_Impact_Metrics.py` | Calculation | ❌ Don't touch |
| `Test.ipynb` | Testing | ✅ Optional |

---

## 🎯 Usage Examples

### **Example 1: Get Data**
```python
from oil_factor_api import get_oil_factors_sync

impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")
print(f"Got {len(impact_df)} factors")
```

### **Example 2: Different Language**
```python
# English
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM", language="English")

# Chinese
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM", language="Chinese")
```

### **Example 3: Force Refresh**
```python
# Bypass cache
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM", force_refresh=True)
```

---

## ✅ System Features

**Automatic:**
- ✅ Fetches WTI + General news (755+ articles)
- ✅ Creates LLM trend analysis
- ✅ Generates impact metrics
- ✅ Updates when cache is stale (>14 days)
- ✅ LLM-based factor merging
- ✅ Weighted average updates
- ✅ Multi-language support

**Data Sources:**
- ✅ Yahoo Finance (price data)
- ✅ FMP API (WTI news)
- ✅ FMP API (General news with 57 keywords)
- ✅ DeepSeek LLM (analysis)

---

## 📝 Quick Reference

```python
# Import
from oil_factor_api import get_oil_factors_sync

# Call
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")

# Use
print(impact_df.head())
print(time_df.head())
```

**Input:** Ticker string  
**Output:** 2 DataFrames  
**Time:** 0.1s (cached) or 30-90s (update)  

---

## 🎊 Ready for Production

- ✅ All dependencies in `requirements.txt`
- ✅ API keys pre-configured
- ✅ Redis connection ready
- ✅ Documentation complete
- ✅ Examples provided
- ✅ Code tested and verified

**Just install requirements and use `oil_factor_api.py`!**

---

**Questions? Check `HOW_TO_USE.md` or `README.md`**

