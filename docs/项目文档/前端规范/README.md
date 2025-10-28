# Bloomberg 风格设计系统使用指南

本设计系统为您提供了完整的 Bloomberg 风格前端开发规范和配置文件，帮助您快速构建专业的金融数据平台。

## 📦 包含文件

1. **bloomberg-design-specification.md** - 完整的设计规范文档
2. **bloomberg-variables.css** - CSS 变量配置文件
3. **tailwind.config.js** - Tailwind CSS 配置文件
4. **README.md** - 本使用指南

---

## 🚀 快速开始

### 方案一：使用 CSS 变量（适合任何项目）

1. 在您的项目中导入 CSS 变量文件：

```html
<!-- 在 HTML 中引入 -->
<link rel="stylesheet" href="bloomberg-variables.css">
```

或在 CSS/SCSS 中：

```css
@import 'bloomberg-variables.css';
```

2. 直接使用变量：

```css
.my-component {
  background-color: var(--bg-card);
  color: var(--text-primary);
  padding: var(--space-4);
  border-radius: var(--radius-base);
}
```

### 方案二：使用 Tailwind CSS

1. 复制 `tailwind.config.js` 到项目根目录

2. 安装必要的依赖：

```bash
npm install -D tailwindcss postcss autoprefixer
```

3. 创建 `postcss.config.js`：

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

4. 在主 CSS 文件中引入 Tailwind：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

5. 使用 Tailwind 类名：

```jsx
<div className="bg-background-card text-text-primary p-4 rounded">
  <h2 className="text-xl font-semibold mb-3">Market Data</h2>
  <p className="text-text-secondary">...</p>
</div>
```

---

## 💡 实用示例

### 示例 1: 股票数据卡片

```jsx
import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

const StockCard = ({ symbol, name, price, change, changePercent }) => {
  const isPositive = change >= 0;
  
  return (
    <div className="data-card">
      <div className="data-card-header">
        <div>
          <span className="ticker-badge">{symbol}</span>
          <p className="text-sm text-text-secondary mt-1">{name}</p>
        </div>
        <div className="live-indicator">
          <span className="text-xs text-text-tertiary">实时</span>
        </div>
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <div className="text-data-lg font-semibold text-text-primary mb-1">
            ${price.toFixed(2)}
          </div>
          <div className={`flex items-center gap-1 text-sm ${
            isPositive ? 'text-market-positive' : 'text-market-negative'
          }`}>
            {isPositive ? 
              <TrendingUp size={16} /> : 
              <TrendingDown size={16} />
            }
            <span className="tabular-nums">{change.toFixed(2)}</span>
            <span className="tabular-nums">({changePercent.toFixed(2)}%)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockCard;
```

### 示例 2: 数据表格

```jsx
const MarketTable = ({ data }) => {
  return (
    <div className="overflow-x-auto">
      <table className="data-table">
        <thead>
          <tr>
            <th>代码</th>
            <th>名称</th>
            <th className="numeric">最新价</th>
            <th className="numeric">涨跌</th>
            <th className="numeric">涨跌幅</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.symbol}>
              <td>
                <span className="ticker-badge">{row.symbol}</span>
              </td>
              <td>{row.name}</td>
              <td className="numeric tabular-nums font-data">
                ${row.price.toFixed(2)}
              </td>
              <td className={`numeric tabular-nums font-data ${
                row.change >= 0 ? 'text-market-positive' : 'text-market-negative'
              }`}>
                {row.change >= 0 ? '+' : ''}{row.change.toFixed(2)}
              </td>
              <td className={`numeric tabular-nums font-data ${
                row.changePercent >= 0 ? 'text-market-positive' : 'text-market-negative'
              }`}>
                {row.changePercent >= 0 ? '+' : ''}{row.changePercent.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### 示例 3: 导航栏

```jsx
const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 h-[60px] bg-bloomberg-black border-b border-border-primary flex items-center px-6 z-fixed">
      <div className="flex items-center gap-8">
        <h1 className="text-xl font-bold text-bloomberg-orange">
          Bloomberg Terminal
        </h1>
        
        <div className="flex gap-4">
          <a href="#markets" className="text-text-secondary hover:text-text-primary transition-colors">
            Markets
          </a>
          <a href="#news" className="text-text-secondary hover:text-text-primary transition-colors">
            News
          </a>
          <a href="#analysis" className="text-text-secondary hover:text-text-primary transition-colors">
            Analysis
          </a>
        </div>
      </div>
      
      <div className="ml-auto flex items-center gap-4">
        <div className="live-indicator">
          <span className="text-sm">Market Open</span>
        </div>
        <button className="btn btn-primary">
          Subscribe
        </button>
      </div>
    </nav>
  );
};
```

### 示例 4: 带图表的仪表盘布局

```jsx
const Dashboard = () => {
  return (
    <div className="min-h-screen bg-background-primary">
      {/* 导航栏 */}
      <Navbar />
      
      {/* 主内容区 */}
      <div className="pt-[60px] flex">
        {/* 侧边栏 */}
        <aside className="w-60 bg-background-secondary border-r border-border-primary p-4">
          <div className="space-y-2">
            <button className="w-full text-left px-3 py-2 rounded text-text-secondary hover:bg-background-tertiary hover:text-text-primary transition-colors">
              Overview
            </button>
            <button className="w-full text-left px-3 py-2 rounded text-text-primary bg-background-tertiary">
              Watchlist
            </button>
            <button className="w-full text-left px-3 py-2 rounded text-text-secondary hover:bg-background-tertiary hover:text-text-primary transition-colors">
              Portfolio
            </button>
          </div>
        </aside>
        
        {/* 主内容 */}
        <main className="flex-1 p-6">
          {/* 市场概览卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StockCard 
              symbol="SPX"
              name="S&P 500"
              price={4195.44}
              change={15.22}
              changePercent={0.36}
            />
            {/* 更多卡片... */}
          </div>
          
          {/* 数据表格 */}
          <div className="data-card">
            <h2 className="text-xl font-semibold mb-4">Top Movers</h2>
            <MarketTable data={marketData} />
          </div>
        </main>
      </div>
    </div>
  );
};
```

---

## 🎨 核心设计原则

### 1. 色彩使用

- **深色背景**: 使用 `#0D0D0D` 作为主背景，减少眼睛疲劳
- **高对比度**: 确保文字与背景有足够的对比度
- **语义色彩**: 
  - 绿色 (`#00C805`) 表示上涨
  - 红色 (`#FF3347`) 表示下跌
  - 彭博橙 (`#FF6600`) 用于强调和品牌元素

### 2. 排版

- **等宽字体**: 数字和代码使用等宽字体确保对齐
- **数字样式**: 使用 `tabular-nums` 确保数字列对齐
- **字体层级**: 清晰的字体大小层级（36px → 28px → 24px → ...）

### 3. 信息密度

- 在有限空间内展示最多信息
- 使用紧凑的间距（4px, 8px, 12px, 16px）
- 避免过多的留白，但保持可读性

### 4. 实时数据处理

```jsx
// 使用动画高亮数据变化
const [highlightedRows, setHighlightedRows] = useState(new Set());

useEffect(() => {
  if (dataUpdated) {
    setHighlightedRows(new Set([rowIndex]));
    setTimeout(() => {
      setHighlightedRows(new Set());
    }, 500);
  }
}, [data]);

// 在渲染中应用高亮类
<tr className={highlightedRows.has(index) ? 'animate-data-update' : ''}>
```

---

## 📱 响应式设计

### 断点使用

```javascript
// Tailwind 断点
sm: '640px'   // 手机横屏
md: '768px'   // 平板竖屏
lg: '1024px'  // 平板横屏/小笔记本
xl: '1280px'  // 桌面
2xl: '1536px' // 大屏桌面
```

### 移动端适配示例

```jsx
// 响应式网格
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {/* 卡片内容 */}
</div>

// 响应式侧边栏
<aside className="hidden lg:block w-60">
  {/* 侧边栏内容 */}
</aside>

// 移动端菜单
<button className="lg:hidden">
  <MenuIcon />
</button>
```

---

## ⚡ 性能优化建议

### 1. 虚拟滚动

对于大量数据列表，使用虚拟滚动：

```bash
npm install react-window
```

```jsx
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={data.length}
  itemSize={40}
  width="100%"
>
  {Row}
</FixedSizeList>
```

### 2. 数据更新节流

```javascript
import { throttle } from 'lodash';

const throttledUpdate = throttle((data) => {
  setMarketData(data);
}, 200); // 每200ms最多更新一次
```

### 3. 图表性能优化

```javascript
// 使用 ECharts
const chartOptions = {
  renderer: 'canvas', // Canvas比SVG性能更好
  animation: false,   // 实时数据禁用动画
};

// 数据采样（当数据点过多时）
const downsampledData = data.filter((_, index) => index % 5 === 0);
```

---

## 🔧 常用工具库推荐

### UI 组件

```bash
npm install lucide-react        # 图标
npm install recharts            # React图表
npm install @radix-ui/react-*   # 无样式组件库
```

### 数据处理

```bash
npm install lodash             # 工具函数
npm install date-fns           # 日期处理
npm install numeral            # 数字格式化
```

### 状态管理

```bash
npm install zustand            # 轻量状态管理
npm install @tanstack/react-query  # 服务端状态
```

### 实时数据

```bash
npm install socket.io-client   # WebSocket客户端
npm install swr                # 数据获取
```

---

## 🎯 最佳实践

### 1. 组件组织

```
components/
├── common/           # 通用组件（Button, Input, Card）
├── market/           # 市场相关（StockCard, PriceTable）
├── charts/           # 图表组件
└── layout/           # 布局组件（Navbar, Sidebar）
```

### 2. 类型定义（TypeScript）

```typescript
// types/market.ts
export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
}

export interface MarketData {
  stocks: Stock[];
  lastUpdate: Date;
  marketStatus: 'open' | 'closed' | 'pre-market' | 'after-hours';
}
```

### 3. 自定义 Hooks

```typescript
// hooks/useMarketData.ts
import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

export function useMarketData() {
  const [data, setData] = useState<Stock[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket = io('ws://your-api.com');

    socket.on('connect', () => setIsConnected(true));
    socket.on('market-data', (newData) => setData(newData));
    socket.on('disconnect', () => setIsConnected(false));

    return () => {
      socket.disconnect();
    };
  }, []);

  return { data, isConnected };
}
```

---

## 🐛 常见问题

### Q: 如何切换到色盲友好模式？

```jsx
// 在根元素上添加属性
<div data-color-scheme="cvd">
  {/* 您的应用 */}
</div>
```

### Q: 如何自定义主题色？

在 `tailwind.config.js` 或 CSS 变量中修改：

```css
:root {
  --bloomberg-orange: #YOUR_COLOR;
}
```

### Q: 数据表格如何实现排序？

```jsx
const [sortConfig, setSortConfig] = useState({ key: 'price', direction: 'desc' });

const sortedData = [...data].sort((a, b) => {
  if (a[sortConfig.key] < b[sortConfig.key]) {
    return sortConfig.direction === 'asc' ? -1 : 1;
  }
  if (a[sortConfig.key] > b[sortConfig.key]) {
    return sortConfig.direction === 'asc' ? 1 : -1;
  }
  return 0;
});
```

---

## 📚 更多资源

- **设计规范**: 查看 `bloomberg-design-specification.md` 了解详细的设计规范
- **ECharts 文档**: https://echarts.apache.org/
- **Tailwind CSS 文档**: https://tailwindcss.com/
- **Radix UI 文档**: https://www.radix-ui.com/
- **React Window 文档**: https://react-window.vercel.app/

---

## 🤝 贡献与反馈

如有任何问题或建议，欢迎反馈！

---

## 📄 许可证

本设计系统基于 Bloomberg Terminal 的设计理念创建，仅供学习和参考使用。

---

**版本**: 1.0.0  
**最后更新**: 2025年10月26日
