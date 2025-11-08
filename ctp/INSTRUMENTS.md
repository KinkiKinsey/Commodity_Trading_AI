# CTP 合约品种分类

## 📊 支持的交易所

根据 BHCT001 券商，支持以下交易所：

| 交易所 | 名称 | 合约数量 | 主要品种 |
|--------|------|---------|---------|
| **CME** | 芝加哥商品交易所 | 5,471 | 股指、外汇、利率 |
| **ICE** | 洲际交易所 | 2,591 | 能源、农产品 |
| **NYM** | 纽约商品交易所 | 2,536 | 能源（原油、天然气） |
| **CBT** | 芝加哥期货交易所 | 2,193 | 农产品（大豆、玉米） |
| **SGX** | 新加坡交易所 | 95 | 亚洲股指 |

**总计**：12,886 个合约

---

## 🏷️ 主要品种代码

### 1. 能源类 (Energy)

| 品种 | 代码 | 交易所 | 示例合约 |
|------|------|--------|---------|
| 原油 | CL | NYMEX | `CL2512-NYM` |
| 布伦特原油 | BRN | ICE | `BRN2512-ICE` |
| 天然气 | NG | NYMEX | `NG2512-NYM` |
| 汽油 | RB | NYMEX | `RB2512-NYM` |
| 取暖油 | HO | NYMEX | `HO2512-NYM` |

### 2. 贵金属 (Precious Metals)

| 品种 | 代码 | 交易所 | 示例合约 |
|------|------|--------|---------|
| 黄金 | GC | COMEX (CME) | `GC2512-CME` |
| 白银 | SI | COMEX (CME) | `SI2512-CME` |
| 铂金 | PL | NYMEX | `PL2512-NYM` |
| 钯金 | PA | NYMEX | `PA2512-NYM` |

### 3. 基础金属 (Base Metals)

| 品种 | 代码 | 交易所 | 示例合约 |
|------|------|--------|---------|
| 铜 | HG | COMEX (CME) | `HG2512-CME` |

### 4. 农产品 (Agriculture)

| 品种 | 代码 | 交易所 | 示例合约 |
|------|------|--------|---------|
| 大豆 | ZS | CBOT | `ZS2511-CBT` |
| 玉米 | ZC | CBOT | `ZC2512-CBT` |
| 小麦 | ZW | CBOT | `ZW2512-CBT` |
| 豆油 | ZL | CBOT | `ZL2512-CBT` |
| 豆粕 | ZM | CBOT | `ZM2512-CBT` |
| 燕麦 | ZO | CBOT | `ZO2512-CBT` |
| 糙米 | ZR | CBOT | `ZR2512-CBT` |

### 5. 股指期货 (Equity Index)

| 品种 | 代码 | 交易所 | 示例合约 |
|------|------|--------|---------|
| E-mini 标普500 | ES | CME | `ES2512-CME` |
| E-mini 纳斯达克100 | NQ | CME | `NQ2512-CME` |
| E-mini 道琼斯 | YM | CBOT | `YM2512-CBT` |
| E-mini 罗素2000 | RTY | CME | `RTY2512-CME` |

### 6. 外汇 (FX)

| 品种 | 代码 | 交易所 | 示例合约 |
|------|------|--------|---------|
| 欧元 | 6E | CME | `6E2512-CME` |
| 日元 | 6J | CME | `6J2512-CME` |
| 英镑 | 6B | CME | `6B2512-CME` |
| 瑞郎 | 6S | CME | `6S2512-CME` |
| 澳元 | 6A | CME | `6A2512-CME` |
| 加元 | 6C | CME | `6C2512-CME` |

### 7. 利率 (Interest Rates)

| 品种 | 代码 | 交易所 | 示例合约 |
|------|------|--------|---------|
| 10年期美债 | ZN | CBOT | `ZN2512-CBT` |
| 5年期美债 | ZF | CBOT | `ZF2512-CBT` |
| 2年期美债 | ZT | CBOT | `ZT2512-CBT` |
| 30年期美债 | ZB | CBOT | `ZB2512-CBT` |

---

## 🔍 合约命名规则

### 格式说明

```
{品种代码}{年月}-{交易所}
```

**示例**：
- `GC2512-CME` = 黄金 2025年12月到期 (CME交易所)
- `CL2601-NYM` = 原油 2026年1月到期 (NYMEX)
- `ZS2511-CBT` = 大豆 2025年11月到期 (CBOT)

### 期权合约

```
O_{标的}_{年月}_{类型}{价格}-{交易所}
```

**示例**：
- `O_GC2512_C3000-CME` = 黄金2025年12月看涨期权，行权价3000
- `O_GC2512_P2900-CME` = 黄金2025年12月看跌期权，行权价2900

**类型**：
- `C` = Call (看涨期权)
- `P` = Put (看跌期权)

---

## 📡 API 使用示例

### 1. 查询所有交易所

```bash
curl http://localhost:8080/instruments | jq '{exchanges, total_count}'
```

**响应**：
```json
{
  "exchanges": ["CME", "ICE", "NYM", "CBT", "SGX"],
  "total_count": 12886
}
```

### 2. 查询特定交易所的合约

```bash
# CME 的所有合约
curl "http://localhost:8080/instruments?exchange=CME" | jq '.count'

# NYMEX 的所有合约
curl "http://localhost:8080/instruments?exchange=NYM" | jq '.instruments[:10]'
```

### 3. 查找特定品种

```bash
# 黄金合约
curl "http://localhost:8080/instruments?exchange=CME" | \
  jq '.instruments | map(select(startswith("GC")))'

# 原油合约
curl "http://localhost:8080/instruments?exchange=NYM" | \
  jq '.instruments | map(select(startswith("CL")))'

# 大豆合约
curl "http://localhost:8080/instruments?exchange=CBT" | \
  jq '.instruments | map(select(startswith("ZS")))'
```

### 4. 获取合约行情

```bash
# 黄金2025年12月合约
curl http://localhost:8080/md/tick/GC2512-CME

# 原油2025年12月合约
curl http://localhost:8080/md/tick/CL2512-NYM

# 批量查询
curl "http://localhost:8080/md/ticks?ids=GC2512-CME,CL2512-NYM,ZS2511-CBT"
```

---

## 🎯 常用品种查询命令

### 能源品种

```bash
# NYMEX 原油系列
curl -s "http://localhost:8080/instruments?exchange=NYM" | \
  jq '.instruments | map(select(startswith("CL"))) | .[0:10]'

# ICE 布伦特原油
curl -s "http://localhost:8080/instruments?exchange=ICE" | \
  jq '.instruments | map(select(startswith("BRN"))) | .[0:10]'
```

### 金属品种

```bash
# CME 黄金
curl -s "http://localhost:8080/instruments?exchange=CME" | \
  jq '.instruments | map(select(startswith("GC"))) | .[0:10]'

# CME 白银
curl -s "http://localhost:8080/instruments?exchange=CME" | \
  jq '.instruments | map(select(startswith("SI"))) | .[0:10]'
```

### 农产品

```bash
# CBOT 大豆
curl -s "http://localhost:8080/instruments?exchange=CBT" | \
  jq '.instruments | map(select(startswith("ZS"))) | .[0:10]'

# CBOT 玉米
curl -s "http://localhost:8080/instruments?exchange=CBT" | \
  jq '.instruments | map(select(startswith("ZC"))) | .[0:10]'
```

### 股指期货

```bash
# CME E-mini 纳斯达克
curl -s "http://localhost:8080/instruments?exchange=CME" | \
  jq '.instruments | map(select(startswith("NQ"))) | .[0:10]'

# CME E-mini 标普500
curl -s "http://localhost:8080/instruments?exchange=CME" | \
  jq '.instruments | map(select(startswith("ES"))) | .[0:10]'
```

---

## 📝 Python 使用示例

```python
import requests

BASE_URL = "http://localhost:8080"

# 1. 查询所有交易所
response = requests.get(f"{BASE_URL}/instruments")
data = response.json()
print(f"支持的交易所: {data['exchanges']}")
print(f"总合约数: {data['total_count']}")

# 2. 查询 CME 的黄金合约
response = requests.get(f"{BASE_URL}/instruments", params={"exchange": "CME"})
instruments = response.json()["instruments"]
gold_contracts = [i for i in instruments if i.startswith("GC")]
print(f"CME 黄金合约: {gold_contracts[:10]}")

# 3. 获取黄金行情
response = requests.get(f"{BASE_URL}/md/tick/GC2512-CME")
tick = response.json()
print(f"黄金价格: {tick['last_price']}")

# 4. 监控多个品种
instruments = ["GC2512-CME", "CL2512-NYM", "ZS2511-CBT"]
response = requests.get(
    f"{BASE_URL}/md/ticks",
    params={"ids": ",".join(instruments)}
)
ticks = response.json()["ticks"]
for inst_id, data in ticks.items():
    print(f"{inst_id}: {data['last_price']}")
```

---

## 📚 参考资料

- [CME Group](https://www.cmegroup.com/)
- [ICE](https://www.theice.com/)
- [CTP API 文档](./API.md)

