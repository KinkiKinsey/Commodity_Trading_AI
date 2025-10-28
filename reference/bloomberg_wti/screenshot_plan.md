# Bloomberg WTI Screenshot Plan

> 如果脚本无法绕过 Bloomberg 的机器人验证，可先手动登录，再在浏览器保持会话后执行脚本。

## 目标截图

| 名称 | 目标区域 | 输出文件 |
|------|----------|----------|
| `nav-top.png` | 顶部 logo + subscribe + user + search + quote-nav | `screenshots/nav-top.png` |
| `hero-overview.png` | 行情头条 + 3×2 指标网格 + 操作按钮 | `screenshots/hero-overview.png` |
| `chart-tools.png` | 时间粒度按钮、指标、多资产比较、Full Screen、Download | `screenshots/chart-tools.png` |
| `chart-area.png` | 主图（含十字线） + 成交量 | `screenshots/chart-area.png` |
| `news-top-stories.png` | Top Stories 卡片 | `screenshots/news-top-stories.png` |
| `news-latest.png` | Latest News 列表 | `screenshots/news-latest.png` |
| `right-rail.png` | Company Profile / Executives / Key Statistics 折叠块 | `screenshots/right-rail.png` |
| `footer-ticker.png` | 底部行情带（若可见） | `screenshots/footer-ticker.png` |

同时导出页面结构摘要（模块位置、按钮文本、样式信息等），保存为 `metadata/layout.json`。

## 运行方式

```bash
npm install playwright
npx playwright install chromium
node reference/bloomberg_wti/capture_bloomberg.js
```

脚本将：
1. 启动 Chromium 非无头模式打开 `https://www.bloomberg.com/quote/WTI:US`；
2. 等待页面加载并允许手动处理验证码；
3. 自动滚动到目标区域并截取截图；
4. 将主要 DOM 信息（如按钮标签、文本、颜色）写入 `metadata/layout.json`；
5. 关闭浏览器。

输出位于：
```
reference/bloomberg_wti/
├── screenshots/
├── metadata/
└── capture_bloomberg.js
```

如需更新，只需重新运行脚本，旧文件会被覆盖。***
