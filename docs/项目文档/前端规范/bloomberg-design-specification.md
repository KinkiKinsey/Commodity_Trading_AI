# Bloomberg 风格前端设计规范
## Frontend Design System Specification

---

## 1. 设计理念 (Design Philosophy)

### 1.1 核心原则
- **信息密度优先**: 在有限空间内展示最大量的有价值信息
- **专业性与可读性平衡**: 保持金融专业性的同时确保内容清晰易读
- **实时数据驱动**: 界面需支持实时数据更新而不中断用户工作流
- **渐进式演进**: 界面改进应循序渐进，避免剧烈变化影响用户习惯
- **模块化灵活性**: 采用模块化设计系统，支持内容权重的动态调整

### 1.2 用户体验原则
- 最小化用户学习成本
- 支持键盘快捷键操作
- 保持视觉一致性
- 优先展示关键信息
- 支持多屏幕工作流

---

## 2. 色彩系统 (Color System)

### 2.1 主色调 (Primary Colors)

```css
/* 品牌色 */
--bloomberg-black: #000000;
--bloomberg-orange: #FF6600;  /* 彭博橙 - 品牌主色 */
--bloomberg-amber: #FFA500;   /* 琥珀色 - 非语义信息 */

/* 背景色 */
--background-primary: #0D0D0D;    /* 深黑背景 */
--background-secondary: #1A1A1A;  /* 次级背景 */
--background-tertiary: #2A2A2A;   /* 三级背景 */
--background-card: #1C1C1C;       /* 卡片背景 */
```

### 2.2 语义色彩 (Semantic Colors)

```css
/* 市场数据 - 涨跌 */
--color-positive: #00C805;    /* 上涨 - 绿色 */
--color-negative: #FF3347;    /* 下跌 - 红色 */
--color-neutral: #8C8C8C;     /* 中性 - 灰色 */

/* 数据类别 */
--color-stock-blue: #3B82F6;     /* 股票 - 蓝色 */
--color-bond-purple: #A855F7;    /* 债券 - 紫色 */
--color-commodity-yellow: #EAB308; /* 商品 - 黄色 */
--color-forex-cyan: #06B6D4;     /* 外汇 - 青色 */

/* 状态色 */
--color-warning: #F59E0B;
--color-error: #EF4444;
--color-success: #10B981;
--color-info: #3B82F6;
```

### 2.3 文字色彩

```css
--text-primary: #FFFFFF;      /* 主要文字 */
--text-secondary: #A0A0A0;    /* 次要文字 */
--text-tertiary: #707070;     /* 三级文字 */
--text-link: #3B82F6;         /* 链接 */
--text-link-hover: #60A5FA;   /* 链接悬停 */
```

### 2.4 色彩无障碍 (Color Accessibility)

为色盲用户提供可选配色方案：

```css
/* Deuteranopia (红绿色盲) 配色方案 */
--cvd-positive: #3B82F6;  /* 用蓝色代替绿色表示上涨 */
--cvd-negative: #EF4444;  /* 用红色表示下跌 */
```

---

## 3. 排版系统 (Typography)

### 3.1 字体家族

```css
/* 主要字体 - 优先使用等宽字体保证数字对齐 */
--font-primary: 'Bloomberg Mono', 'SF Mono', 'Consolas', 'Courier New', monospace;

/* 标题字体 */
--font-heading: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* 数据展示字体 - 必须等宽 */
--font-data: 'IBM Plex Mono', 'Roboto Mono', monospace;

/* 正文字体 */
--font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
```

### 3.2 字体大小层级

```css
/* 标题 */
--text-4xl: 36px;    /* 页面主标题 */
--text-3xl: 28px;    /* 区块标题 */
--text-2xl: 24px;    /* 卡片标题 */
--text-xl: 20px;     /* 小标题 */

/* 正文 */
--text-lg: 16px;     /* 大号正文 */
--text-base: 14px;   /* 标准正文 */
--text-sm: 12px;     /* 小号文字 */
--text-xs: 11px;     /* 辅助信息 */

/* 数据展示 */
--text-data-lg: 24px;   /* 大号数据 */
--text-data-md: 18px;   /* 中号数据 */
--text-data-sm: 14px;   /* 小号数据 */
```

### 3.3 字重 (Font Weight)

```css
--font-light: 300;
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 3.4 行高 (Line Height)

```css
--line-height-tight: 1.2;    /* 紧凑 - 用于数据 */
--line-height-normal: 1.5;   /* 标准 - 用于正文 */
--line-height-relaxed: 1.75; /* 宽松 - 用于长文章 */
```

---

## 4. 布局系统 (Layout System)

### 4.1 容器尺寸

```css
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
--container-2xl: 1536px;
--container-full: 100%;
```

### 4.2 间距系统 (Spacing Scale)

```css
--space-0: 0px;
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
```

### 4.3 网格系统

- **基础网格**: 12列网格系统
- **间距**: 24px (Desktop), 16px (Tablet), 12px (Mobile)
- **边距**: 32px (Desktop), 24px (Tablet), 16px (Mobile)

### 4.4 页面布局结构

```
┌─────────────────────────────────────────┐
│           Header (固定60px)              │
├──────────┬──────────────────────────────┤
│          │                              │
│  Sidebar │      Main Content Area       │
│ (240px)  │                              │
│  固定    │         响应式宽度            │
│          │                              │
│  导航    │      数据展示区域             │
│  菜单    │                              │
│          │                              │
└──────────┴──────────────────────────────┘
```

### 4.5 卡片布局规范

```css
.data-card {
  background: var(--background-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: var(--space-4);
  margin-bottom: var(--space-4);
}

.data-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
```

---

## 5. 组件设计规范 (Component Design)

### 5.1 导航栏 (Navigation Bar)

```css
.navbar {
  height: 60px;
  background: var(--bloomberg-black);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  padding: 0 var(--space-6);
  position: fixed;
  top: 0;
  width: 100%;
  z-index: 1000;
}

.navbar-brand {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--bloomberg-orange);
}

.navbar-link {
  color: var(--text-secondary);
  padding: var(--space-2) var(--space-4);
  transition: color 0.2s ease;
}

.navbar-link:hover {
  color: var(--text-primary);
}
```

### 5.2 数据表格 (Data Table)

```css
.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-family: var(--font-data);
  font-size: var(--text-sm);
}

.data-table thead {
  background: var(--background-secondary);
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table th {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.data-table td {
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.data-table tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

/* 数字右对齐 */
.data-table .numeric {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* 涨跌颜色 */
.positive {
  color: var(--color-positive);
}

.negative {
  color: var(--color-negative);
}
```

### 5.3 股票代码标签 (Ticker Badge)

```css
.ticker-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 4px;
  font-family: var(--font-data);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-stock-blue);
  letter-spacing: 0.5px;
}
```

### 5.4 实时数据指示器

```css
.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.live-indicator::before {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--color-positive);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
```

### 5.5 迷你图表 (Sparkline)

```css
.sparkline-container {
  height: 40px;
  width: 100px;
  display: inline-block;
}

.sparkline {
  stroke-width: 2;
  fill: none;
}

.sparkline.positive {
  stroke: var(--color-positive);
}

.sparkline.negative {
  stroke: var(--color-negative);
}
```

### 5.6 按钮组件

```css
.btn {
  padding: var(--space-2) var(--space-4);
  border-radius: 4px;
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background: var(--bloomberg-orange);
  color: white;
}

.btn-primary:hover {
  background: #FF7722;
}

.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.3);
}
```

### 5.7 输入框

```css
.input {
  padding: var(--space-3) var(--space-4);
  background: var(--background-secondary);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: var(--text-primary);
  font-size: var(--text-base);
  transition: all 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: var(--bloomberg-orange);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

.input::placeholder {
  color: var(--text-tertiary);
}
```

---

## 6. 数据可视化 (Data Visualization)

### 6.1 图表配色方案

```javascript
const chartColors = {
  primary: '#FF6600',
  series: [
    '#3B82F6',  // 蓝色
    '#10B981',  // 绿色
    '#F59E0B',  // 橙色
    '#8B5CF6',  // 紫色
    '#06B6D4',  // 青色
    '#EC4899',  // 粉色
  ],
  grid: 'rgba(255, 255, 255, 0.1)',
  text: '#A0A0A0',
};
```

### 6.2 图表样式规范

```javascript
const chartDefaults = {
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'Inter, sans-serif',
    fontSize: 12,
    color: '#A0A0A0',
  },
  grid: {
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
  },
  tooltip: {
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 1,
    textStyle: {
      color: '#FFFFFF',
    },
  },
};
```

### 6.3 K线图配置

```javascript
const candlestickConfig = {
  itemStyle: {
    color: '#00C805',      // 上涨
    color0: '#FF3347',     // 下跌
    borderColor: '#00C805',
    borderColor0: '#FF3347',
  },
};
```

---

## 7. 动画与过渡 (Animation & Transitions)

### 7.1 过渡时间

```css
--transition-fast: 150ms;
--transition-base: 200ms;
--transition-slow: 300ms;
--transition-slower: 500ms;
```

### 7.2 缓动函数

```css
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### 7.3 数据更新动画

```css
@keyframes data-update {
  0% {
    background-color: rgba(255, 102, 0, 0.3);
  }
  100% {
    background-color: transparent;
  }
}

.data-cell.updated {
  animation: data-update 0.5s ease-out;
}
```

### 7.4 闪烁效果 (用于重要数据变化)

```css
@keyframes flash {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.flash {
  animation: flash 0.5s ease-in-out;
}
```

---

## 8. 响应式设计 (Responsive Design)

### 8.1 断点定义

```css
/* Mobile First 方法 */
--breakpoint-sm: 640px;   /* 手机横屏 */
--breakpoint-md: 768px;   /* 平板竖屏 */
--breakpoint-lg: 1024px;  /* 平板横屏/小笔记本 */
--breakpoint-xl: 1280px;  /* 桌面 */
--breakpoint-2xl: 1536px; /* 大屏桌面 */
```

### 8.2 响应式布局策略

```css
/* 移动端 */
@media (max-width: 767px) {
  .sidebar {
    display: none; /* 隐藏侧边栏 */
  }
  
  .data-table {
    font-size: var(--text-xs);
  }
  
  .container {
    padding: var(--space-4);
  }
}

/* 平板 */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar {
    width: 180px;
  }
  
  .data-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 桌面 */
@media (min-width: 1024px) {
  .sidebar {
    width: 240px;
  }
  
  .data-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## 9. 性能优化指南 (Performance Optimization)

### 9.1 实时数据更新优化

```javascript
// 使用节流函数限制更新频率
const throttledUpdate = throttle((data) => {
  updateUI(data);
}, 200); // 每200ms最多更新一次

// WebSocket数据接收
socket.on('market-data', throttledUpdate);
```

### 9.2 虚拟滚动

对于大量数据列表，使用虚拟滚动技术：

```javascript
// 推荐使用 react-window 或 react-virtualized
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={10000}
  itemSize={40}
  width="100%"
>
  {Row}
</FixedSizeList>
```

### 9.3 图表性能优化

```javascript
// 使用Canvas代替SVG渲染大数据量图表
const chartOptions = {
  renderer: 'canvas', // 而非 'svg'
  animation: false,   // 对实时数据禁用动画
};

// 数据采样
const downsampledData = downsample(rawData, 1000);
```

---

## 10. 可访问性 (Accessibility)

### 10.1 ARIA标签

```html
<!-- 实时更新区域 -->
<div role="region" aria-live="polite" aria-atomic="true">
  <span class="price">$150.25</span>
</div>

<!-- 数据表格 -->
<table role="table" aria-label="股票报价">
  <thead role="rowgroup">
    <tr role="row">
      <th role="columnheader">代码</th>
      <th role="columnheader">价格</th>
    </tr>
  </thead>
</table>
```

### 10.2 键盘导航

```css
/* 聚焦状态 */
*:focus-visible {
  outline: 2px solid var(--bloomberg-orange);
  outline-offset: 2px;
}

/* 跳过导航链接 */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--bloomberg-orange);
  color: white;
  padding: var(--space-2);
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

### 10.3 对比度要求

- 大文本 (18px+): 最小对比度 3:1
- 正常文本: 最小对比度 4.5:1
- 关键操作按钮: 最小对比度 7:1

---

## 11. 交互模式 (Interaction Patterns)

### 11.1 悬停效果

```css
.interactive-row {
  transition: background-color var(--transition-base);
}

.interactive-row:hover {
  background-color: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}
```

### 11.2 选中状态

```css
.selectable.selected {
  background-color: rgba(255, 102, 0, 0.15);
  border-left: 3px solid var(--bloomberg-orange);
}
```

### 11.3 加载状态

```css
.loading-skeleton {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.05) 25%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0.05) 75%
  );
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
```

### 11.4 错误状态

```css
.error-state {
  border-color: var(--color-error);
  background-color: rgba(239, 68, 68, 0.1);
}

.error-message {
  color: var(--color-error);
  font-size: var(--text-sm);
  margin-top: var(--space-2);
}
```

---

## 12. 图标系统 (Icon System)

### 12.1 图标规范

- **尺寸**: 16px, 20px, 24px, 32px
- **线条粗细**: 1.5px (默认), 2px (加重)
- **风格**: 线性图标，统一圆角
- **推荐图标库**: Lucide Icons, Heroicons

### 12.2 图标使用示例

```jsx
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

// 涨跌图标
<TrendingUp size={16} className="text-positive" />
<TrendingDown size={16} className="text-negative" />
<Activity size={20} className="text-primary" />
```

---

## 13. 特殊组件 (Specialized Components)

### 13.1 市场时钟

```css
.market-clock {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--background-secondary);
  border-radius: 4px;
  font-family: var(--font-data);
}

.market-status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--color-positive);
}
```

### 13.2 新闻提要卡片

```css
.news-card {
  background: var(--background-card);
  border-left: 3px solid transparent;
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  transition: all var(--transition-base);
}

.news-card:hover {
  border-left-color: var(--bloomberg-orange);
  background: var(--background-secondary);
}

.news-card-meta {
  display: flex;
  gap: var(--space-3);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--space-2);
}

.news-card-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
  line-height: var(--line-height-normal);
}
```

### 13.3 警报通知

```css
.alert {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: 4px;
  margin-bottom: var(--space-4);
}

.alert-warning {
  background: rgba(245, 158, 11, 0.1);
  border-left: 4px solid var(--color-warning);
}

.alert-error {
  background: rgba(239, 68, 68, 0.1);
  border-left: 4px solid var(--color-error);
}

.alert-info {
  background: rgba(59, 130, 246, 0.1);
  border-left: 4px solid var(--color-info);
}
```

---

## 14. 代码示例 (Code Examples)

### 14.1 完整的数据卡片组件

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
          <p className="text-sm text-secondary mt-1">{name}</p>
        </div>
        <div className="live-indicator">
          <span className="text-xs text-tertiary">实时</span>
        </div>
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <div className="text-data-lg font-semibold text-primary mb-1">
            ${price.toFixed(2)}
          </div>
          <div className={`flex items-center gap-1 text-sm ${
            isPositive ? 'text-positive' : 'text-negative'
          }`}>
            {isPositive ? 
              <TrendingUp size={16} /> : 
              <TrendingDown size={16} />
            }
            <span>{change.toFixed(2)}</span>
            <span>({changePercent.toFixed(2)}%)</span>
          </div>
        </div>
        
        <div className="sparkline-container">
          {/* 迷你图表组件 */}
        </div>
      </div>
    </div>
  );
};

export default StockCard;
```

### 14.2 实时数据表格组件

```jsx
import React, { useState, useEffect } from 'react';

const MarketTable = ({ data }) => {
  const [highlightedRows, setHighlightedRows] = useState(new Set());

  useEffect(() => {
    // 当数据更新时高亮显示
    const newHighlights = new Set();
    data.forEach((item, index) => {
      if (item.updated) {
        newHighlights.add(index);
        setTimeout(() => {
          setHighlightedRows(prev => {
            const next = new Set(prev);
            next.delete(index);
            return next;
          });
        }, 500);
      }
    });
    setHighlightedRows(newHighlights);
  }, [data]);

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>代码</th>
          <th>名称</th>
          <th className="numeric">最新价</th>
          <th className="numeric">涨跌</th>
          <th className="numeric">涨跌幅</th>
          <th className="numeric">成交量</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row, index) => (
          <tr 
            key={row.symbol}
            className={highlightedRows.has(index) ? 'updated' : ''}
          >
            <td>
              <span className="ticker-badge">{row.symbol}</span>
            </td>
            <td>{row.name}</td>
            <td className="numeric font-data">${row.price.toFixed(2)}</td>
            <td className={`numeric font-data ${
              row.change >= 0 ? 'positive' : 'negative'
            }`}>
              {row.change >= 0 ? '+' : ''}{row.change.toFixed(2)}
            </td>
            <td className={`numeric font-data ${
              row.changePercent >= 0 ? 'positive' : 'negative'
            }`}>
              {row.changePercent >= 0 ? '+' : ''}{row.changePercent.toFixed(2)}%
            </td>
            <td className="numeric font-data">
              {(row.volume / 1000000).toFixed(2)}M
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default MarketTable;
```

---

## 15. 技术栈建议 (Recommended Tech Stack)

### 15.1 核心框架
- **React 18+** 或 **Next.js 14+**: 现代化的组件开发
- **TypeScript**: 类型安全
- **Tailwind CSS**: 快速样式开发（配合自定义主题）

### 15.2 状态管理
- **Zustand** 或 **Redux Toolkit**: 全局状态管理
- **React Query / TanStack Query**: 服务端状态管理

### 15.3 数据可视化
- **ECharts**: 强大的图表库
- **D3.js**: 自定义可视化
- **Recharts**: React图表组件

### 15.4 实时数据
- **Socket.io-client**: WebSocket连接
- **SWR**: 数据获取和缓存

### 15.5 UI组件库
- **Radix UI** 或 **Headless UI**: 无样式组件库
- **Lucide React**: 图标库

---

## 16. 开发工作流 (Development Workflow)

### 16.1 命名规范

```javascript
// 组件文件命名: PascalCase
StockCard.tsx
MarketTable.tsx

// 工具函数文件: camelCase
formatCurrency.ts
calculateChange.ts

// CSS模块: kebab-case
stock-card.module.css

// 常量文件: UPPER_SNAKE_CASE
API_ENDPOINTS.ts
```

### 16.2 代码组织结构

```
src/
├── components/
│   ├── common/          # 通用组件
│   ├── market/          # 市场数据组件
│   ├── charts/          # 图表组件
│   └── layout/          # 布局组件
├── hooks/               # 自定义Hooks
├── utils/               # 工具函数
├── services/            # API服务
├── constants/           # 常量
├── types/               # TypeScript类型
├── styles/              # 全局样式
└── pages/               # 页面组件
```

### 16.3 Git提交规范

```
feat: 新功能
fix: 修复bug
style: 样式更新
refactor: 代码重构
perf: 性能优化
test: 测试相关
docs: 文档更新
chore: 构建/工具链更新
```

---

## 17. 测试规范 (Testing Standards)

### 17.1 组件测试

```javascript
import { render, screen } from '@testing-library/react';
import StockCard from './StockCard';

describe('StockCard', () => {
  it('should display positive change in green', () => {
    const props = {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: 150.25,
      change: 2.50,
      changePercent: 1.69,
    };
    
    render(<StockCard {...props} />);
    
    const changeElement = screen.getByText(/\+2.50/);
    expect(changeElement).toHaveClass('text-positive');
  });
});
```

---

## 18. 浏览器兼容性 (Browser Compatibility)

### 支持的浏览器版本
- Chrome: 最新版本及前两个主要版本
- Firefox: 最新版本及前两个主要版本
- Safari: 最新版本及前两个主要版本
- Edge: 最新版本及前两个主要版本

### 必须支持的特性
- CSS Grid
- CSS Flexbox
- WebSocket
- ES6+ 语法
- CSS自定义属性

---

## 19. 安全性考虑 (Security Considerations)

### 19.1 XSS防护
```javascript
// 使用DOMPurify清理用户输入
import DOMPurify from 'dompurify';

const cleanHTML = DOMPurify.sanitize(userInput);
```

### 19.2 CSP策略
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline';">
```

---

## 20. 性能指标 (Performance Metrics)

### 目标性能指标
- **首次内容绘制 (FCP)**: < 1.5秒
- **最大内容绘制 (LCP)**: < 2.5秒
- **首次输入延迟 (FID)**: < 100毫秒
- **累积布局偏移 (CLS)**: < 0.1
- **交互时间 (TTI)**: < 3.8秒

---

## 总结

本设计规范基于Bloomberg Terminal和Bloomberg.com的设计哲学，强调：

1. **信息密度**: 在有限空间内最大化信息展示
2. **专业性**: 使用等宽字体、精确的数据对齐和专业配色
3. **实时性**: 支持高频率数据更新而不影响性能
4. **一致性**: 保持视觉和交互的一致性
5. **可访问性**: 考虑色盲用户和键盘导航需求

遵循本规范将帮助您构建一个专业、高效、用户友好的金融数据平台。

---

**版本**: 1.0.0  
**最后更新**: 2025年10月  
**维护者**: 前端开发团队