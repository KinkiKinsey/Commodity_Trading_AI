# Bloomberg WTI Reference Snapshot

This directory stores locally captured assets from the public Bloomberg WTI quote page for UI research. The aim is to inspect layout, typography, and interaction patterns while keeping the product’s own functionality intact.

## Capture Method

Primary workflow uses PowerShell’s `Invoke-WebRequest` to save a static HTML snapshot. The steps executed by `fetch_bloomberg_wti.ps1` are:

1. Create/ensure the directory: `reference/bloomberg_wti/`
2. Fetch page markup at `https://www.bloomberg.com/quote/WTI:US`
3. Save the response to `raw/wti_quote.html`
4. Append timestamped metadata to `fetch_log.md`

> Bloomberg 会对自动化请求做反爬虫校验。如果脚本返回 403 或提示需要验证码，请在桌面浏览器中打开该页面，使用 “保存网页 (Webpage, complete)” 功能，并将生成的 `*.html` 及资源文件移动到 `raw/` 目录中。所有资产仅供内部分析，不得对外分发。

## Update Instructions (PowerShell)

```powershell
pwsh -File reference/bloomberg_wti/fetch_bloomberg_wti.ps1
```

This downloads the latest HTML, stores it under `raw/wti_quote.html`, and logs the outcome.

## Directory Layout

```
reference/bloomberg_wti/
├── README.md
├── fetch_bloomberg_wti.ps1
├── fetch_log.md
└── raw/
    └── wti_quote.html
```

You may place additional analysis artifacts here (e.g., annotated screenshots, CSS token lists) to support the Bloomberg-style redesign documented in `Bloomberg_Frontend_Redesign.md`.
