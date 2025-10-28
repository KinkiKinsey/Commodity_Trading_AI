# Claude Code 快速参考卡片
## Ringshell Bloomberg 风格前端重构

---

## 🎯 核心任务
重构 `frontend/web/app/news/real-time/page.tsx`，实现 Bloomberg Terminal 风格的实时新闻和 AI 分析界面。

---

## 📁 关键文件路径

```
frontend/web/
├── app/news/real-time/page.tsx         ← 主页面入口
├── components/
│   ├── layout/GlobalNavbar.tsx         ← 顶部导航
│   ├── news/NewsCard.tsx               ← 新闻卡片
│   ├── news/ChainOfThoughtDrawer.tsx   ← AI 推理抽屉
│   └── charts/KLineChart.tsx           ← K 线图
├── lib/
│   ├── hooks/useNewsStream.ts          ← SSE 实时数据
│   ├── stores/newsStreamStore.ts       ← 状态管理
│   └── types/news.ts                   ← TypeScript 类型
└── styles/globals.css                  ← 全局样式
```

---

## 🎨 设计规范速查

### 颜色变量
```css
--bloomberg-black: #000000       /* 导航背景 */
--bloomberg-orange: #FF6600      /* 品牌色 */
--bg-primary: #0D0D0D           /* 页面背景 */
--bg-card: #1C1C1C              /* 卡片背景 */
--text-primary: #FFFFFF         /* 主文字 */
--text-secondary: #A0A0A0       /* 次要文字 */
--color-positive: #00C805       /* 上涨/多头 */
--color-negative: #FF3347       /* 下跌/空头 */
```

### 字体
```css
--font-body: 'Inter', sans-serif           /* 正文 */
--font-data: 'IBM Plex Mono', monospace    /* 数据/数字 */
```

### 间距
```css
--space-2: 8px
--space-4: 16px
--space-6: 24px
```

---

## 🔌 API 端点

### 实时新闻流（SSE）
```
GET /api/news/stream
Content-Type: text/event-stream

事件类型:
- event: news      → 新闻推送
- event: heartbeat → 心跳（30秒）
```

### K 线数据
```
GET /api/pricing/kline?ticker=CLZ25.NYM&days=90

返回: { series[], mlMovingAverage{}, indicators[], signals[] }
```

### 市场概览
```
GET /api/markets/overview

返回: { data: MarketOverview[], lastUpdate: string }
```

---

## 📊 核心数据结构

### NewsItem
```typescript
interface NewsItem {
  id: string;
  headline: string;              // 标题
  summary: string;               // 摘要
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;            // 0-100
  sentiment: number;             // -1 to 1
  timestamp: string;
  tags: string[];
  chainOfThought: ChainOfThoughtStep[];
  citations: Citation[];
  relatedSignals: AISignal[];
}
```

### AISignal
```typescript
interface AISignal {
  id: string;
  type: 'buy' | 'sell' | 'hold';
  price: number;
  timestamp: string;
  confidence: number;            // 0-1
  newsId?: string;
  reasonTag?: string;
}
```

---

## 🧩 组件接口

### NewsCard
```tsx
<NewsCard
  news={newsItem}
  onClick={(news) => openModal(news)}
/>
```

### KLineChart
```tsx
<KLineChart
  data={klineData}
  height={500}
  showMLTrend={true}
  onSignalClick={(signal) => showNews(signal.newsId)}
/>
```

### ChainOfThoughtDrawer
```tsx
<ChainOfThoughtDrawer
  isOpen={isOpen}
  onClose={closeDrawer}
  steps={news.chainOfThought}
  title={news.headline}
/>
```

---

## 🔧 常用工具函数

### 格式化相对时间
```typescript
function formatRelativeTime(timestamp: string): string {
  const diffMins = Math.floor((Date.now() - new Date(timestamp).getTime()) / 60000);
  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins} 分钟前`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)} 小时前`;
  return `${Math.floor(diffMins / 1440)} 天前`;
}
```

### 格式化货币
```typescript
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
}
```

---

## 🎯 实现优先级

### P0 - 必须实现
- [x] Bloomberg 暗色主题
- [x] 三列响应式布局
- [ ] SSE 实时新闻流
- [ ] 新闻卡片展示
- [ ] AI 推理链抽屉
- [ ] K 线图基础展示

### P1 - 重要功能
- [ ] 信号点击联动新闻
- [ ] 新闻过滤和搜索
- [ ] 情绪仪表盘
- [ ] 引用列表
- [ ] 错误处理和重连

### P2 - 优化增强
- [ ] 虚拟滚动优化
- [ ] 键盘导航
- [ ] 色盲模式
- [ ] 性能监控

---

## 🐛 常见问题快速修复

### SSE 连接断开
```typescript
// 添加自动重连逻辑
eventSource.onerror = () => {
  eventSource.close();
  setTimeout(() => connectSSE(), 5000);
};
```

### K 线图卡顿
```typescript
// 禁用动画，使用 Canvas
const option = {
  animation: false,
  renderer: 'canvas',
};
```

### 新闻列表滚动慢
```bash
pnpm add react-window
```
```tsx
import { FixedSizeList } from 'react-window';
```

---

## 📝 代码规范

### 组件命名
- PascalCase: `NewsCard.tsx`, `KLineChart.tsx`
- 使用函数组件 + TypeScript

### 样式规范
- 优先使用 Tailwind 类名
- 自定义样式使用 CSS 变量
- 响应式使用 `lg:`, `xl:` 等前缀

### 状态管理
- Zustand: 全局状态（新闻、信号）
- React Query: 服务端数据
- useState: 组件局部状态

---

## ✅ 开发检查清单

### 启动开发
```bash
cd frontend/web
pnpm install
pnpm dev
```

### 运行测试
```bash
pnpm test        # 单元测试
pnpm test:e2e    # E2E 测试
pnpm lint        # 代码检查
```

### 构建部署
```bash
pnpm build       # 生产构建
pnpm start       # 启动生产服务器
```

---

## 🎨 Tailwind 常用类名速查

### 布局
```
grid grid-cols-3 gap-6           # 三列网格
flex items-center justify-between # 水平布局
max-w-[1440px] mx-auto px-8      # 容器居中
```

### 颜色
```
bg-background-card               # 卡片背景
text-text-primary                # 主文字
text-market-positive             # 上涨绿色
border-border-primary            # 边框
```

### 交互
```
hover:bg-background-tertiary     # 悬停背景
transition-colors duration-200   # 颜色过渡
cursor-pointer                   # 指针样式
```

### 响应式
```
hidden lg:block                  # 大屏显示
grid-cols-1 xl:grid-cols-3      # 响应式列数
text-sm lg:text-base            # 响应式字号
```

---

## 🔍 调试技巧

### 查看 SSE 连接
```javascript
// 在浏览器控制台
performance.getEntriesByType('resource')
  .filter(r => r.name.includes('/stream'))
```

### 监控组件渲染
```tsx
import { Profiler } from 'react';

<Profiler
  id="NewsCard"
  onRender={(id, phase, actualDuration) => {
    console.log(`${id} ${phase} took ${actualDuration}ms`);
  }}
>
  <NewsCard />
</Profiler>
```

### 检查无障碍
```bash
pnpm add -D @axe-core/react
```

---

## 📚 快速链接

- 📖 [完整设计文档](./Bloomberg_Frontend_Redesign_v3.md)
- 🎨 [设计规范](../../docs/项目文档/前端规范/bloomberg-design-specification.md)
- 🔧 [业务需求](../../docs/项目文档/AI_real_time_news_plan1021.md)
- 📸 [参考截图](../../reference/bloomberg_wti/screenshots/)

---

## 🚀 立即开始

1. **阅读完整文档**: `Bloomberg_Frontend_Redesign_v3.md`
2. **查看设计规范**: `bloomberg-design-specification.md`
3. **安装依赖**: `pnpm install`
4. **启动开发**: `pnpm dev`
5. **开始编码**: 从 `page.tsx` 主页面开始

---

**提示**: 使用 Claude Code 时，可以说"按照 Bloomberg 设计规范实现 [组件名]"来获得符合规范的代码。

**最后更新**: 2025-10-26
