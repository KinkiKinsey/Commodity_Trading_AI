# 🚀 Oil Factor API - How to Use

**Super simple guide for getting oil factor metrics.**

---

## 📦 Step 1: Import

```python
from oil_factor_api import get_oil_factors_sync
```

**That's the ONLY import you need!**

---

## 🎯 Step 2: Call the Function

```python
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")
```

**That's it! You get two DataFrames.**

---

## 📊 Inputs & Outputs

### **INPUTS:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `ticker` | str | "CLZ25.NYM" | ✅ Yes | Oil futures ticker |
| `language` | str | "Chinese" | ❌ No | Factor language (English/Chinese) |
| `force_refresh` | bool | False | ❌ No | Skip cache, regenerate |

### **OUTPUTS:**

Two pandas DataFrames:

#### **Output 1: `impact_metrics_df`**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `factor` | str | Factor name | "OPEC+增产预期" |
| `scope` | str | Factor type | "macro" or "micro" |
| `trend_count` | int | Number of trends | 5 |
| `weighted_mean` | float | Average impact | 0.003456 |
| `weighted_variance` | float | Impact variance | 0.000234 |
| `risk_reward_ratio` | float | Risk/reward | 0.654 |
| `average_duration` | float | Avg days per trend | 12.5 |
| `total_duration` | int | Total days | 65 |

**Size:** 12-20 rows (factors) × 8 columns

#### **Output 2: `factor_time_df`**

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `factor_name` | str | Factor name | "OPEC+增产预期" |
| `scope` | str | Factor type | "macro" or "micro" |
| `start_date` | str | Period start | "2025-05-10" |
| `end_date` | str | Period end | "2025-05-25" |
| `duration_days` | int | Period length | 15 |
| `time_interval` | str | Date range | "2025-05-10 to 2025-05-25" |

**Size:** 60-80 rows (intervals) × 6 columns

---

## 💻 Complete Examples

### **Example 1: Basic Python Script**

```python
# File: my_oil_analysis.py
from oil_factor_api import get_oil_factors_sync

# Get data
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")

# Use the data
print(f"Total factors: {len(impact_df)}")
print(f"\nTop 5 factors:")
print(impact_df.head())

# Save to CSV
impact_df.to_csv('oil_impact_metrics.csv', index=False)
time_df.to_csv('oil_factor_time.csv', index=False)
```

### **Example 2: Jupyter Notebook**

```python
# Cell 1: Import
from oil_factor_api import get_oil_factors

# Cell 2: Get data (async)
impact_df, time_df = await get_oil_factors("CLZ25.NYM", language="Chinese")

# Cell 3: Display
display(impact_df)
display(time_df)
```

### **Example 3: With Different Language**

```python
# Get factors in English
impact_df, time_df = get_oil_factors_sync(
    ticker="CLZ25.NYM",
    language="English"
)

print(impact_df['factor'].tolist())
# Output: ['Fed Rate Cut Expectation', 'OPEC Production Cut', ...]
```

### **Example 4: Force Refresh**

```python
# Bypass cache, regenerate everything
impact_df, time_df = get_oil_factors_sync(
    ticker="CLZ25.NYM",
    force_refresh=True
)
# Takes 60-90 seconds (fresh generation)
```

---

## ⏱️ Performance

| Scenario | Time | Description |
|----------|------|-------------|
| **Cache hit** | 0.1s | Data < 14 days old |
| **Incremental update** | 30-60s | Data ≥ 14 days old |
| **Force refresh** | 60-90s | `force_refresh=True` |

---

## 🔑 What Happens Behind the Scenes

### **When You Call the Function:**

```
1. Check Redis for cached data
   ↓
2. If cache < 14 days old:
   → Return cached data (FAST!)
   
3. If cache ≥ 14 days old:
   → Fetch NEW news (from last update to today)
   → Create NEW trends (LLM analysis)
   → Generate NEW metrics
   → LLM maps new → old factors
   → Merge with weighted average
   → Store to Redis
   → Return merged data
   
4. If no cache:
   → Generate full 700 days of data
   → Store to Redis
   → Return data
```

**You don't need to manage any of this - it's automatic!**

---

## 📖 Understanding the Data

### **Impact Metrics DataFrame:**

```
factor                    | scope | trend_count | weighted_mean | ...
--------------------------|-------|-------------|---------------|----
OPEC+增产预期              | micro | 5           | -0.004600     | ...
美联储鹰派政策预期          | macro | 5           | 0.000308      | ...
库存下降优于预期            | micro | 5           | 0.004526      | ...
```

**Interpretation:**
- `weighted_mean > 0`: Positive impact on oil prices
- `weighted_mean < 0`: Negative impact on oil prices
- `trend_count`: How often this factor appeared
- `risk_reward_ratio`: Higher = better risk/reward

### **Factor Time DataFrame:**

```
factor_name               | start_date  | end_date    | duration_days
--------------------------|-------------|-------------|---------------
OPEC+增产预期              | 2025-05-10  | 2025-05-25  | 15
OPEC+增产预期              | 2025-07-01  | 2025-07-15  | 14
美联储鹰派政策预期          | 2025-06-01  | 2025-06-10  | 9
```

**Interpretation:**
- Each row = one time period when the factor was active
- Same factor can have multiple time periods
- Use this to see when factors impact oil prices

---

## ⚠️ Important Notes

### **Cache Behavior:**

- ✅ First call: Generates data (slow)
- ✅ Subsequent calls (< 14 days): Uses cache (fast)
- ✅ After 14 days: Auto-updates (smart merge)

### **Language Consistency:**

- System remembers the language you used
- Incremental updates use SAME language
- Cross-language LLM mapping works automatically

### **News Updates:**

- WTI news auto-refreshes every 24 hours
- Includes WTI stock news + General market news
- 57 keywords filter (oil, macro, dollar, geopolitical, etc.)

---

## 🐛 Troubleshooting

### **Issue: KeyError 'last_update'**

**Cause:** Old cache without metadata

**Fix:**
```python
# Force regenerate to create metadata
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM", force_refresh=True)
```

### **Issue: Slow on first call**

**Cause:** No cache, generating fresh data

**Expected:** 60-90 seconds (normal for first call)

### **Issue: Different factor count each time**

**Cause:** Incremental updates add new factors

**Expected:** Factors increase over time (12 → 15 → 18...)

---

## 📞 Support

For questions, check:
1. `Test.ipynb` - Working examples
2. `README.md` - System overview
3. Source code - Well documented

---

## ✅ Quick Reference

```python
# Simplest usage:
from oil_factor_api import get_oil_factors_sync
impact_df, time_df = get_oil_factors_sync("CLZ25.NYM")

# That's all you need to know!
```

**Input:** Ticker string  
**Output:** Two DataFrames (impact metrics + factor time)  
**Time:** 0.1s (cached) or 30-90s (update/fresh)  

---

**System ready for production use! 🎊**

