# Bloomberg S&P 500 Index (SPX:IND) Reference Notes

## 1. 页面来源
- **URL**: https://www.bloomberg.com/quote/SPX:IND  
- **数据时间**: As of 4:55 PM EDT, 10/24/25  
- **页面类型**: Bloomberg Markets - React SPA（动态渲染）  
- **截图来源**: 手动截取得到完整渲染页面，因为 Puppeteer / Playwright 在静态 HTML 阶段 selector 失效。

---

## 2. 截图对应区域

### hero-overview.png
**描述**：页面顶部行情与折线图区域  
**包含内容**：
- 指数标题：`S&P 500 INDEX`  
- 代码：`SPX:IND`  
- 市场状态：`(USD) · Market closed`  
- 当前数值：`6,791.69`  
- 涨跌幅：`+53.25 (+0.79%)`  
- 时间：`As of 4:55 PM EDT 10/24/25`  
- 折线图：绿色填充曲线，显示单日行情波动  
- 工具栏：
  - 时间区间按钮：`1D, 1M, 6M, YTD, 1Y, 5Y`
  - 切换项：`News` toggle
  - 搜索框：`Add a comparison`
- 图表 Tooltip 示例：`6,796.82 USD at 12:44`

---

### overview-key-stats.png
**描述**：页面下半部分的指标与统计数据区块  
**包含模块**：

#### Overview
| 指标 | 数值 |
|-------|------|
| Open | 6,772.07 |
| Prev. Close | 6,738.44 |
| 1 Year Return | 18.43% |
| YTD Return | 15.47% |
| Day Range | 6,772.07 – 6,807.11 |
| 52 Week Range | 4,835.04 – 6,807.11 |

#### Key Statistics
| 指标 | 数值 |
|-------|------|
| P/E Ratio | 28.25 |
| Price to Book Ratio | 5.55 |
| Price to Sales Ratio | 3.38 |
| 30 Day Avg Volume | 898,003,508.80 |
| EPS | 261.83 |
| Last Dividend Reported | 0.2968998358981782 |

右侧为 “Markets at a Glance” 模块，显示：
- Dow Jones Industrial：47,207.12 (+1.01%)  
- NASDAQ Composite：23,204.87 (+1.15%)  
- S&P 500：6,791.69 (+0.79%)  
- Bloomberg 500：2,461.96 (+0.79%)  
- 其他区域指数如 S&P/TSX、S&P/BMV IPC 等。

---

## 3. 视觉特征
- **主色调**：白底 + 黑色主字 + Bloomberg 品牌深灰 / 蓝色点缀  
- **涨跌颜色**：  
  - 上涨：绿色 `#00A65A`  
  - 下跌：红色 `#E94F37`  
- **字体**：Bloomberg Sans / Helvetica Neue  
  - 标题字号约 `18–20px`  
  - 表格内容约 `14–16px`
- **布局**：
  - 模块间距约 24px  
  - 双列表格对齐  
  - 右侧栏包含“Markets at a Glance”与广告位
- **交互点**：
  - 折线图 hover tooltip  
  - 时间区间切换  
  - “Add a comparison” 输入框  
  - “News” toggle 控制新闻面板

---

## 4. 技术与脚本说明
- 页面由 **React 动态渲染**，DOM 在客户端 hydrate 之后才加载主要内容。
- Puppeteer 抓取静态 HTML 时 selector 会 miss。  
- 手动截图用于视觉参考及设计还原。  
- 脚本改进建议：

```js
// 在 capture_bloomberg.js 中等待 React hydrate
await page.waitForFunction('document.querySelector("div[data-reactroot]")');
await page.waitForTimeout(3000);
```

或检测 `window.__NEXT_DATA__` 是否加载完成，以确保页面完全渲染。

---

## 5. 后续可复现点
- 若需自动化获取最新行情截图，可结合：
  - `page.screenshot({ fullPage: true })`  
  - `waitForSelector("section:has-text('Overview')")`  
- 若 Bloomberg 页面结构变化，可通过 DevTools 重新确认：
  - `div[data-component="QuotePage"]`  
  - `section[data-component="KeyStatistics"]`

---

## 6. 附件文件结构参考
```
reference/
└── bloomberg_wti/
    ├── screenshots/
    │   ├── hero-overview.png
    │   └── overview-key-stats.png
    └── notes.md
```

---

## 7. 未来可补充截图模块
- Related News 区块  
- Markets at a Glance 完整区域（含国际指数）  
- 页脚广告区参考  
- 顶部导航与搜索栏结构截图

---

> 本文档作为视觉还原与爬取调试说明文件，可直接供设计或自动化工程参考。
