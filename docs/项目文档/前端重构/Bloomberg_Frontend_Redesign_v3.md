# Bloomberg 风格前端重构设计文档（Ringshell 实时资讯页）
## 开发实施指南 v3.0

---

## 📋 文档导航

- [0. 快速开始](#0-快速开始)
- [1. 技术栈与依赖](#1-技术栈与依赖)
- [2. 项目结构](#2-项目结构)
- [3. 数据契约](#3-数据契约)
- [4. 组件规范](#4-组件规范)
- [5. 状态管理](#5-状态管理)
- [6. 样式系统](#6-样式系统)
- [7. 开发检查清单](#7-开发检查清单)

---

## 0. 快速开始

### 0.1 文档目的
本文档为 `frontend/web/app/news/real-time/page.tsx` 的重构提供**可执行的技术蓝图**，确保：
- AI 辅助开发工具（Claude Code）能快速理解需求并生成代码
- 前端工程师能直接参照实现，无需额外解释
- 设计师和产品经理能验证交付物与预期一致

### 0.2 参考依赖文档
| 文档 | 路径 | 用途 |
|------|------|------|
| 业务需求 | `docs/项目文档/AI_real_time_news_plan1021.md` | 功能清单、验收标准 |
| 视觉规范 | `docs/项目文档/前端规范/bloomberg-design-specification.md` | 设计系统、组件库 |
| CSS 变量 | `docs/项目文档/前端规范/bloomberg-variables.css` | 主题配置 |
| Tailwind 配置 | `docs/项目文档/前端规范/tailwind.config.js` | 样式工具类 |
| 截图参考 | `reference/bloomberg_wti/screenshots/` | 布局与交互示例 |

### 0.3 核心目标
1. 采用 Bloomberg Terminal 式深色主题，信息密度优先
2. 支持实时数据推送（SSE）且性能稳定（< 16ms 交互响应）
3. 集成 AI 推理链、情绪分析、K 线图、新闻引用等功能
4. 完全响应式，支持桌面、平板、移动端
5. 符合 WCAG 2.1 AA 标准，支持键盘导航和色盲模式

---

## 1. 技术栈与依赖

### 1.1 核心框架
```json
{
  "framework": "Next.js 14 (App Router)",
  "react": "^18.2.0",
  "typescript": "^5.2.0",
  "styling": "Tailwind CSS ^3.4.0",
  "stateManagement": [
    "Zustand ^4.4.0",
    "@tanstack/react-query ^5.0.0"
  ],
  "charts": "ECharts ^5.4.0",
  "icons": "lucide-react ^0.263.1"
}
```

### 1.2 安装命令
```bash
cd frontend/web
pnpm add zustand @tanstack/react-query echarts echarts-for-react lucide-react
pnpm add -D @types/node
```

### 1.3 环境变量配置
```bash
# frontend/web/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SSE_ENDPOINT=/api/news/stream
NEXT_PUBLIC_WS_ENDPOINT=ws://localhost:8000/ws
```

---

## 2. 项目结构

### 2.1 文件组织
```
frontend/web/
├── app/
│   └── news/
│       └── real-time/
│           ├── page.tsx                 # 主页面
│           ├── layout.tsx               # 布局容器
│           └── components/              # 页面级组件
│               ├── MarketColumn.tsx     # 左列：市场概览
│               ├── NewsColumn.tsx       # 中列：新闻流
│               └── InsightsColumn.tsx   # 右列：洞察侧栏
├── components/
│   ├── common/                          # 通用组件
│   │   ├── DataCard.tsx
│   │   ├── TickerBadge.tsx
│   │   └── LiveIndicator.tsx
│   ├── layout/                          # 布局组件
│   │   ├── GlobalNavbar.tsx
│   │   ├── BottomTicker.tsx
│   │   └── AppShell.tsx
│   ├── charts/                          # 图表组件
│   │   ├── IndexSignalChart.tsx
│   │   ├── KLineChart.tsx
│   │   └── SentimentDial.tsx
│   ├── news/                            # 新闻相关
│   │   ├── NewsCard.tsx
│   │   ├── NewsPreviewModal.tsx
│   │   └── ChainOfThoughtDrawer.tsx
│   └── signals/                         # 信号组件
│       ├── SignalList.tsx
│       └── SignalBadge.tsx
├── lib/
│   ├── api/                             # API 客户端
│   │   ├── newsClient.ts
│   │   ├── pricingClient.ts
│   │   └── sseClient.ts
│   ├── hooks/                           # 自定义 Hooks
│   │   ├── useNewsStream.ts
│   │   ├── useIndexSignals.ts
│   │   └── useKLineData.ts
│   ├── stores/                          # Zustand 状态
│   │   ├── newsStreamStore.ts
│   │   ├── indexSignalsStore.ts
│   │   └── uiStateStore.ts
│   ├── types/                           # TypeScript 类型
│   │   ├── news.ts
│   │   ├── pricing.ts
│   │   └── api.ts
│   └── utils/                           # 工具函数
│       ├── formatters.ts
│       ├── dateUtils.ts
│       └── chartHelpers.ts
├── styles/
│   ├── globals.css                      # 全局样式
│   └── bloomberg-theme.css              # Bloomberg 主题
└── mocks/                               # Mock 数据
    ├── newsStreamMock.json
    └── pricingMock.json
```

### 2.2 命名规范
- **组件文件**: PascalCase（`NewsCard.tsx`）
- **工具函数**: camelCase（`formatCurrency.ts`）
- **类型定义**: PascalCase + Interface/Type 后缀（`NewsItem`, `PricingData`）
- **Hook**: `use` 前缀（`useNewsStream.ts`）
- **Store**: `Store` 后缀（`newsStreamStore.ts`）

---

## 3. 数据契约

### 3.1 核心数据类型

```typescript
// lib/types/news.ts

/**
 * 新闻方向
 */
export type Direction = 'BULLISH' | 'BEARISH' | 'NEUTRAL';

/**
 * 市场状态
 */
export type MarketStatus = 'open' | 'closed' | 'pre-market' | 'after-hours';

/**
 * 连接状态
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * 推理步骤
 */
export interface ChainOfThoughtStep {
  id: string;
  step: number;
  title: string;
  content: string;
  timestamp: string;
  sources: string[];
}

/**
 * 新闻引用
 */
export interface Citation {
  id: string;
  title: string;
  url: string;
  source: string;
  favicon?: string;
  publishedAt: string;
  isDomestic: boolean;
}

/**
 * AI 信号
 */
export interface AISignal {
  id: string;
  type: 'buy' | 'sell' | 'hold';
  price: number;
  timestamp: string;
  confidence: number; // 0-1
  newsId?: string;
  reasonTag?: string;
}

/**
 * 新闻项
 */
export interface NewsItem {
  id: string;
  headline: string;
  summary: string;
  direction: Direction;
  confidence: number; // 0-100
  sentiment: number; // -1 to 1
  timestamp: string;
  tags: string[];
  chainOfThought: ChainOfThoughtStep[];
  citations: Citation[];
  complianceStatus: 'approved' | 'pending' | 'flagged';
  relatedSignals: AISignal[];
}

/**
 * SSE 推送事件
 */
export interface SSEEvent {
  type: 'news' | 'signal' | 'heartbeat' | 'error';
  version: string;
  data: NewsItem | AISignal | { message: string };
  timestamp: string;
}
```

```typescript
// lib/types/pricing.ts

/**
 * K 线数据点
 */
export interface CandlestickData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/**
 * ML 移动平均趋势区间
 */
export interface TrendInterval {
  startDate: string;
  endDate: string;
  trend: 'BULLISH' | 'BEARISH';
}

/**
 * ML 移动平均结果
 */
export interface MLMovingAverageResult {
  summary: string;
  timeIntervals: TrendInterval[];
  upperLine: number[];
  lowerLine: number[];
}

/**
 * 技术指标
 */
export interface TechnicalIndicator {
  name: string;
  values: number[];
  description: string;
}

/**
 * K 线图数据响应
 */
export interface KLineResponse {
  ticker: string;
  series: CandlestickData[];
  mlMovingAverage: MLMovingAverageResult;
  indicators: TechnicalIndicator[];
  signals: AISignal[];
  lastUpdate: string;
}

/**
 * 市场概览
 */
export interface MarketOverview {
  ticker: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  status: MarketStatus;
}
```

### 3.2 API 端点契约

#### 3.2.1 实时新闻流（SSE）
```typescript
// GET /api/news/stream
// Content-Type: text/event-stream

// 事件格式：
event: news
data: {
  "type": "news",
  "version": "1.0",
  "timestamp": "2025-10-26T10:30:00Z",
  "data": {
    "id": "news_001",
    "headline": "美国总统军事施压委内瑞拉石油出口",
    "summary": "美国政府宣布对委内瑞拉实施新一轮制裁...",
    "direction": "BEARISH",
    "confidence": 85,
    "sentiment": -0.6,
    "timestamp": "2025-10-26T10:30:00Z",
    "tags": ["OPEC", "地缘政治", "供应"],
    "chainOfThought": [...],
    "citations": [...],
    "complianceStatus": "approved",
    "relatedSignals": [...]
  }
}

// 心跳事件（每 30 秒）
event: heartbeat
data: {"type":"heartbeat","timestamp":"2025-10-26T10:30:30Z"}
```

#### 3.2.2 K 线数据
```typescript
// GET /api/pricing/kline?ticker=CLZ25.NYM&days=90

interface KLineRequest {
  ticker: string;
  days?: number; // 默认 90
  includeML?: boolean; // 默认 true
  includeIndicators?: boolean; // 默认 false
}

interface KLineAPIResponse {
  success: boolean;
  data: KLineResponse;
  error?: string;
}
```

#### 3.2.3 市场概览
```typescript
// GET /api/markets/overview

interface MarketOverviewResponse {
  success: boolean;
  data: MarketOverview[];
  lastUpdate: string;
}
```

### 3.3 Mock 数据示例

```json
// mocks/newsStreamMock.json
{
  "id": "news_demo_001",
  "headline": "美国总统军事施压委内瑞拉石油出口",
  "summary": "美国政府宣布对委内瑞拉实施新一轮制裁，可能影响全球原油供应链...",
  "direction": "BEARISH",
  "confidence": 85,
  "sentiment": -0.6,
  "timestamp": "2025-10-26T10:30:00Z",
  "tags": ["OPEC", "地缘政治", "供应"],
  "chainOfThought": [
    {
      "id": "step_1",
      "step": 1,
      "title": "制裁背景分析",
      "content": "美国政府针对委内瑞拉石油行业的制裁升级...",
      "timestamp": "2025-10-26T10:30:05Z",
      "sources": ["reuters.com", "bloomberg.com"]
    },
    {
      "id": "step_2",
      "step": 2,
      "title": "供应影响评估",
      "content": "委内瑞拉日产量约 70 万桶，占全球供应的 0.7%...",
      "timestamp": "2025-10-26T10:30:10Z",
      "sources": ["eia.gov"]
    }
  ],
  "citations": [
    {
      "id": "cite_1",
      "title": "US imposes new sanctions on Venezuela oil sector",
      "url": "https://reuters.com/article/...",
      "source": "Reuters",
      "favicon": "https://reuters.com/favicon.ico",
      "publishedAt": "2025-10-26T09:45:00Z",
      "isDomestic": false
    }
  ],
  "complianceStatus": "approved",
  "relatedSignals": [
    {
      "id": "signal_001",
      "type": "sell",
      "price": 75.30,
      "timestamp": "2025-10-26T10:25:00Z",
      "confidence": 0.82,
      "reasonTag": "地缘风险升级"
    }
  ]
}
```

---

## 4. 组件规范

### 4.1 页面主组件

```tsx
// app/news/real-time/page.tsx

'use client';

import { Suspense } from 'react';
import { GlobalNavbar } from '@/components/layout/GlobalNavbar';
import { BottomTicker } from '@/components/layout/BottomTicker';
import { MarketColumn } from './components/MarketColumn';
import { NewsColumn } from './components/NewsColumn';
import { InsightsColumn } from './components/InsightsColumn';
import { useNewsStream } from '@/lib/hooks/useNewsStream';
import { useIndexSignals } from '@/lib/hooks/useIndexSignals';

export default function RealTimeNewsPage() {
  // 订阅实时数据流
  const { news, status: newsStatus, error: newsError } = useNewsStream();
  const { signals, status: signalsStatus } = useIndexSignals();

  return (
    <div className="min-h-screen bg-background-primary">
      {/* 顶部导航 */}
      <GlobalNavbar />

      {/* 主内容区 - 三列布局 */}
      <main className="max-w-[1440px] mx-auto px-8 py-12">
        <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr_320px] gap-6">
          {/* 左列：市场概览 */}
          <aside className="hidden xl:block">
            <MarketColumn signals={signals} />
          </aside>

          {/* 中列：新闻流 */}
          <section>
            <NewsColumn 
              news={news} 
              status={newsStatus}
              error={newsError}
            />
          </section>

          {/* 右列：洞察 */}
          <aside className="hidden xl:block">
            <InsightsColumn 
              news={news}
              connectionStatus={newsStatus}
            />
          </aside>
        </div>
      </main>

      {/* 底部行情带 */}
      <BottomTicker />
    </div>
  );
}
```

### 4.2 核心组件接口

#### 4.2.1 全局导航栏
```tsx
// components/layout/GlobalNavbar.tsx

import { FC } from 'react';
import { Search, Bell, User } from 'lucide-react';

export const GlobalNavbar: FC = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 h-16 bg-bloomberg-black border-b border-border-primary z-fixed">
      <div className="max-w-[1440px] mx-auto px-8 h-full flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-8">
          <h1 className="text-xl font-bold text-bloomberg-orange">
            Ringshell
          </h1>
          
          {/* 主导航 */}
          <div className="hidden md:flex items-center gap-6">
            <NavLink href="/markets">Markets</NavLink>
            <NavLink href="/economics">Economics</NavLink>
            <NavLink href="/news">News</NavLink>
            <NavLink href="/analysis">Analysis</NavLink>
          </div>
        </div>

        {/* 右侧工具 */}
        <div className="flex items-center gap-4">
          <button 
            className="p-2 rounded hover:bg-background-tertiary transition-colors"
            aria-label="Search"
          >
            <Search size={20} className="text-text-secondary" />
          </button>
          
          <button 
            className="p-2 rounded hover:bg-background-tertiary transition-colors"
            aria-label="Notifications"
          >
            <Bell size={20} className="text-text-secondary" />
          </button>

          <button className="btn btn-primary">
            Subscribe
          </button>

          <button 
            className="p-2 rounded hover:bg-background-tertiary transition-colors"
            aria-label="User menu"
          >
            <User size={20} className="text-text-secondary" />
          </button>
        </div>
      </div>
    </nav>
  );
};

const NavLink: FC<{ href: string; children: React.ReactNode }> = ({ 
  href, 
  children 
}) => (
  <a
    href={href}
    className="text-text-secondary hover:text-text-primary transition-colors text-sm font-medium"
  >
    {children}
  </a>
);
```

#### 4.2.2 新闻卡片
```tsx
// components/news/NewsCard.tsx

import { FC, useState } from 'react';
import { TrendingUp, TrendingDown, Clock } from 'lucide-react';
import type { NewsItem } from '@/lib/types/news';
import { NewsPreviewModal } from './NewsPreviewModal';

interface NewsCardProps {
  news: NewsItem;
  onClick?: (news: NewsItem) => void;
}

export const NewsCard: FC<NewsCardProps> = ({ news, onClick }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const isPositive = news.direction === 'BULLISH';

  return (
    <>
      <article
        className="news-card cursor-pointer"
        onClick={() => {
          onClick?.(news);
          setIsModalOpen(true);
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsModalOpen(true);
          }
        }}
      >
        {/* 标签和时间 */}
        <div className="flex items-center gap-3 mb-2">
          <div className="flex items-center gap-2">
            {news.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="text-xs px-2 py-1 rounded bg-background-tertiary text-text-secondary uppercase font-medium"
              >
                {tag}
              </span>
            ))}
          </div>
          
          <div className="flex items-center gap-1 text-xs text-text-tertiary ml-auto">
            <Clock size={12} />
            <time dateTime={news.timestamp}>
              {formatRelativeTime(news.timestamp)}
            </time>
          </div>
        </div>

        {/* 标题 */}
        <h3 className="text-base font-semibold text-text-primary mb-2 line-clamp-2">
          {news.headline}
        </h3>

        {/* 摘要 */}
        <p className="text-sm text-text-secondary line-clamp-2 mb-3">
          {news.summary}
        </p>

        {/* 方向和置信度 */}
        <div className="flex items-center justify-between">
          <div className={`flex items-center gap-2 text-sm font-medium ${
            isPositive ? 'text-market-positive' : 'text-market-negative'
          }`}>
            {isPositive ? (
              <TrendingUp size={16} />
            ) : (
              <TrendingDown size={16} />
            )}
            <span>{news.direction}</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-text-tertiary">Confidence</span>
            <span className="text-sm font-semibold text-text-primary tabular-nums">
              {news.confidence}%
            </span>
          </div>
        </div>

        {/* 信号指示 */}
        {news.relatedSignals.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border-secondary">
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-tertiary">Signal:</span>
              {news.relatedSignals.map((signal) => (
                <span
                  key={signal.id}
                  className={`text-xs px-2 py-1 rounded font-medium ${
                    signal.type === 'buy'
                      ? 'bg-market-positive/20 text-market-positive'
                      : 'bg-market-negative/20 text-market-negative'
                  }`}
                >
                  {signal.type.toUpperCase()} @ ${signal.price.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
        )}
      </article>

      {/* 新闻预览模态框 */}
      <NewsPreviewModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        news={news}
      />
    </>
  );
};

// 辅助函数
function formatRelativeTime(timestamp: string): string {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins} 分钟前`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} 小时前`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} 天前`;
}
```

#### 4.2.3 推理链抽屉
```tsx
// components/news/ChainOfThoughtDrawer.tsx

import { FC, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, ChevronRight, ExternalLink } from 'lucide-react';
import type { ChainOfThoughtStep } from '@/lib/types/news';

interface ChainOfThoughtDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  steps: ChainOfThoughtStep[];
  title: string;
}

export const ChainOfThoughtDrawer: FC<ChainOfThoughtDrawerProps> = ({
  isOpen,
  onClose,
  steps,
  title,
}) => {
  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-modal">
        {/* 背景遮罩 */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/70" aria-hidden="true" />
        </Transition.Child>

        {/* 抽屉面板 */}
        <Transition.Child
          as={Fragment}
          enter="transform transition ease-in-out duration-300"
          enterFrom="translate-x-full"
          enterTo="translate-x-0"
          leave="transform transition ease-in-out duration-300"
          leaveFrom="translate-x-0"
          leaveTo="translate-x-full"
        >
          <Dialog.Panel className="fixed right-0 top-0 h-full w-full max-w-2xl bg-background-secondary border-l border-border-primary overflow-y-auto">
            {/* 头部 */}
            <div className="sticky top-0 bg-background-secondary border-b border-border-primary p-6 flex items-center justify-between">
              <Dialog.Title className="text-xl font-semibold text-text-primary">
                {title}
              </Dialog.Title>
              <button
                onClick={onClose}
                className="p-2 rounded hover:bg-background-tertiary transition-colors"
                aria-label="Close"
              >
                <X size={20} className="text-text-secondary" />
              </button>
            </div>

            {/* 推理步骤 */}
            <div className="p-6 space-y-6">
              {steps.map((step, index) => (
                <div key={step.id} className="relative">
                  {/* 连接线 */}
                  {index < steps.length - 1 && (
                    <div
                      className="absolute left-4 top-12 bottom-0 w-px bg-border-primary"
                      aria-hidden="true"
                    />
                  )}

                  {/* 步骤卡片 */}
                  <div className="relative data-card">
                    {/* 步骤编号 */}
                    <div className="absolute -left-4 -top-4 w-8 h-8 rounded-full bg-bloomberg-orange flex items-center justify-center text-sm font-bold text-white">
                      {step.step}
                    </div>

                    {/* 标题和时间 */}
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="text-base font-semibold text-text-primary">
                        {step.title}
                      </h4>
                      <time
                        className="text-xs text-text-tertiary tabular-nums"
                        dateTime={step.timestamp}
                      >
                        {new Date(step.timestamp).toLocaleTimeString('zh-CN')}
                      </time>
                    </div>

                    {/* 内容 */}
                    <p className="text-sm text-text-secondary leading-relaxed mb-4">
                      {step.content}
                    </p>

                    {/* 来源 */}
                    {step.sources.length > 0 && (
                      <div className="pt-3 border-t border-border-secondary">
                        <p className="text-xs text-text-tertiary mb-2">来源:</p>
                        <div className="flex flex-wrap gap-2">
                          {step.sources.map((source, idx) => (
                            <a
                              key={idx}
                              href={`https://${source}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded bg-background-tertiary text-asset-stock hover:bg-background-card transition-colors"
                            >
                              <span>{source}</span>
                              <ExternalLink size={10} />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Dialog.Panel>
        </Transition.Child>
      </Dialog>
    </Transition>
  );
};
```

#### 4.2.4 K 线图
```tsx
// components/charts/KLineChart.tsx

import { FC, useRef, useEffect } from 'react';
import * as echarts from 'echarts/core';
import { CandlestickChart, LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkPointComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { KLineResponse, AISignal } from '@/lib/types/pricing';

// 注册必需组件
echarts.use([
  CandlestickChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkPointComponent,
  CanvasRenderer,
]);

interface KLineChartProps {
  data: KLineResponse;
  height?: number;
  showMLTrend?: boolean;
  onSignalClick?: (signal: AISignal) => void;
}

export const KLineChart: FC<KLineChartProps> = ({
  data,
  height = 500,
  showMLTrend = false,
  onSignalClick,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化图表
    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current, 'dark');
    }

    const chart = instanceRef.current;

    // 准备 K 线数据
    const dates = data.series.map((item) => item.timestamp);
    const ohlc = data.series.map((item) => [
      item.open,
      item.close,
      item.low,
      item.high,
    ]);
    const volumes = data.series.map((item) => item.volume);

    // 准备 ML 趋势线数据
    const mlUpperLine = showMLTrend ? data.mlMovingAverage.upperLine : [];
    const mlLowerLine = showMLTrend ? data.mlMovingAverage.lowerLine : [];

    // 准备信号标记
    const signalMarkers = data.signals.map((signal) => ({
      name: signal.type === 'buy' ? 'BUY' : 'SELL',
      coord: [signal.timestamp, signal.price],
      value: signal.price.toFixed(2),
      itemStyle: {
        color: signal.type === 'buy' ? '#00C805' : '#FF3347',
      },
      label: {
        formatter: `{b}\n${signal.price.toFixed(2)}`,
        color: '#FFFFFF',
      },
    }));

    // 配置图表选项
    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      animation: false,
      grid: [
        {
          left: '10%',
          right: '8%',
          top: '10%',
          height: '60%',
        },
        {
          left: '10%',
          right: '8%',
          top: '75%',
          height: '15%',
        },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#8392A5' } },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
        {
          type: 'category',
          gridIndex: 1,
          data: dates,
          scale: true,
          boundaryGap: false,
          axisLine: { lineStyle: { color: '#8392A5' } },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax',
        },
      ],
      yAxis: [
        {
          scale: true,
          splitArea: { show: false },
          axisLine: { lineStyle: { color: '#8392A5' } },
          splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLine: { lineStyle: { color: '#8392A5' } },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 70,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: '2%',
          start: 70,
          end: 100,
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          fillerColor: 'rgba(255, 102, 0, 0.2)',
          handleStyle: {
            color: '#FF6600',
          },
        },
      ],
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        textStyle: {
          color: '#FFFFFF',
        },
      },
      series: [
        {
          name: 'K Line',
          type: 'candlestick',
          data: ohlc,
          itemStyle: {
            color: '#00C805',
            color0: '#FF3347',
            borderColor: '#00C805',
            borderColor0: '#FF3347',
          },
          markPoint: {
            data: signalMarkers,
            symbol: 'pin',
            symbolSize: 50,
          },
        },
        ...(showMLTrend
          ? [
              {
                name: 'ML Upper',
                type: 'line',
                data: mlUpperLine,
                smooth: true,
                lineStyle: {
                  color: '#3B82F6',
                  width: 2,
                },
                showSymbol: false,
              },
              {
                name: 'ML Lower',
                type: 'line',
                data: mlLowerLine,
                smooth: true,
                lineStyle: {
                  color: '#EF4444',
                  width: 2,
                },
                showSymbol: false,
              },
            ]
          : []),
        {
          name: 'Volume',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumes,
          itemStyle: {
            color: 'rgba(59, 130, 246, 0.3)',
          },
        },
      ],
    };

    chart.setOption(option);

    // 监听信号点击
    chart.on('click', 'series.markPoint', (params: any) => {
      const signalIndex = params.dataIndex;
      if (onSignalClick && data.signals[signalIndex]) {
        onSignalClick(data.signals[signalIndex]);
      }
    });

    // 响应式调整
    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.off('click');
    };
  }, [data, showMLTrend, onSignalClick]);

  return (
    <div
      ref={chartRef}
      style={{ height: `${height}px`, width: '100%' }}
      aria-label="K线图表"
    />
  );
};
```

---

## 5. 状态管理

### 5.1 Zustand Store 实现

```typescript
// lib/stores/newsStreamStore.ts

import { create } from 'zustand';
import type { NewsItem, ConnectionStatus } from '@/lib/types/news';

interface NewsStreamState {
  news: NewsItem[];
  status: ConnectionStatus;
  error: string | null;
  lastUpdate: string | null;
  
  // Actions
  addNews: (news: NewsItem) => void;
  updateNews: (id: string, updates: Partial<NewsItem>) => void;
  setStatus: (status: ConnectionStatus) => void;
  setError: (error: string | null) => void;
  clearNews: () => void;
}

export const useNewsStreamStore = create<NewsStreamState>((set) => ({
  news: [],
  status: 'disconnected',
  error: null,
  lastUpdate: null,

  addNews: (news) =>
    set((state) => ({
      news: [news, ...state.news].slice(0, 100), // 保留最近 100 条
      lastUpdate: new Date().toISOString(),
    })),

  updateNews: (id, updates) =>
    set((state) => ({
      news: state.news.map((item) =>
        item.id === id ? { ...item, ...updates } : item
      ),
    })),

  setStatus: (status) => set({ status }),

  setError: (error) => set({ error }),

  clearNews: () => set({ news: [], error: null }),
}));
```

```typescript
// lib/stores/uiStateStore.ts

import { create } from 'zustand';

interface UIState {
  // 过滤器
  directionFilter: 'ALL' | 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  timeRangeFilter: '1H' | '4H' | '1D' | '1W' | 'ALL';
  searchQuery: string;
  
  // 模态框状态
  isNewsPreviewOpen: boolean;
  isChainOfThoughtOpen: boolean;
  selectedNewsId: string | null;
  
  // K 线图状态
  showMLTrend: boolean;
  showIndicators: boolean;
  
  // Actions
  setDirectionFilter: (direction: UIState['directionFilter']) => void;
  setTimeRangeFilter: (range: UIState['timeRangeFilter']) => void;
  setSearchQuery: (query: string) => void;
  openNewsPreview: (newsId: string) => void;
  closeNewsPreview: () => void;
  openChainOfThought: (newsId: string) => void;
  closeChainOfThought: () => void;
  toggleMLTrend: () => void;
  toggleIndicators: () => void;
}

export const useUIStateStore = create<UIState>((set) => ({
  directionFilter: 'ALL',
  timeRangeFilter: 'ALL',
  searchQuery: '',
  isNewsPreviewOpen: false,
  isChainOfThoughtOpen: false,
  selectedNewsId: null,
  showMLTrend: false,
  showIndicators: false,

  setDirectionFilter: (direction) => set({ directionFilter: direction }),
  setTimeRangeFilter: (range) => set({ timeRangeFilter: range }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  
  openNewsPreview: (newsId) =>
    set({ isNewsPreviewOpen: true, selectedNewsId: newsId }),
  closeNewsPreview: () =>
    set({ isNewsPreviewOpen: false, selectedNewsId: null }),
  
  openChainOfThought: (newsId) =>
    set({ isChainOfThoughtOpen: true, selectedNewsId: newsId }),
  closeChainOfThought: () =>
    set({ isChainOfThoughtOpen: false }),
  
  toggleMLTrend: () => set((state) => ({ showMLTrend: !state.showMLTrend })),
  toggleIndicators: () =>
    set((state) => ({ showIndicators: !state.showIndicators })),
}));
```

### 5.2 自定义 Hooks

```typescript
// lib/hooks/useNewsStream.ts

import { useEffect, useRef } from 'react';
import { useNewsStreamStore } from '@/lib/stores/newsStreamStore';
import type { SSEEvent } from '@/lib/types/news';

export function useNewsStream() {
  const { news, status, error, addNews, setStatus, setError } =
    useNewsStreamStore();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // 建立 SSE 连接
    const connectSSE = () => {
      try {
        setStatus('connecting');
        
        const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}${process.env.NEXT_PUBLIC_SSE_ENDPOINT}`;
        const eventSource = new EventSource(url);

        eventSource.addEventListener('news', (event) => {
          try {
            const data: SSEEvent = JSON.parse(event.data);
            if (data.type === 'news' && 'headline' in data.data) {
              addNews(data.data);
            }
          } catch (err) {
            console.error('Failed to parse SSE event:', err);
          }
        });

        eventSource.addEventListener('heartbeat', () => {
          console.log('SSE heartbeat received');
        });

        eventSource.onopen = () => {
          setStatus('connected');
          setError(null);
          console.log('SSE connection opened');
        };

        eventSource.onerror = (err) => {
          console.error('SSE error:', err);
          setStatus('error');
          setError('连接失败，正在重试...');
          
          // 自动重连
          setTimeout(() => {
            eventSource.close();
            connectSSE();
          }, 5000);
        };

        eventSourceRef.current = eventSource;
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : '未知错误');
      }
    };

    connectSSE();

    // 清理函数
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [addNews, setStatus, setError]);

  return {
    news,
    status,
    error,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    hasError: status === 'error',
  };
}
```

```typescript
// lib/hooks/useKLineData.ts

import { useQuery } from '@tanstack/react-query';
import type { KLineResponse } from '@/lib/types/pricing';

interface UseKLineDataOptions {
  ticker: string;
  days?: number;
  includeML?: boolean;
  includeIndicators?: boolean;
  enabled?: boolean;
}

export function useKLineData({
  ticker,
  days = 90,
  includeML = true,
  includeIndicators = false,
  enabled = true,
}: UseKLineDataOptions) {
  return useQuery<KLineResponse>({
    queryKey: ['kline', ticker, days, includeML, includeIndicators],
    queryFn: async () => {
      const params = new URLSearchParams({
        ticker,
        days: days.toString(),
        includeML: includeML.toString(),
        includeIndicators: includeIndicators.toString(),
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/pricing/kline?${params}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch K-line data');
      }

      const result = await response.json();
      return result.data;
    },
    enabled,
    staleTime: 60 * 1000, // 1 分钟
    refetchInterval: 5 * 60 * 1000, // 每 5 分钟刷新
  });
}
```

---

## 6. 样式系统

### 6.1 全局样式配置

```css
/* styles/globals.css */

@import 'bloomberg-theme.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

/* 全局基础样式 */
@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background-primary text-text-primary font-body;
    font-feature-settings: 'rlig' 1, 'calt' 1;
  }

  /* 滚动条样式 */
  ::-webkit-scrollbar {
    @apply w-2 h-2;
  }

  ::-webkit-scrollbar-track {
    @apply bg-background-secondary;
  }

  ::-webkit-scrollbar-thumb {
    @apply bg-background-tertiary rounded;
  }

  ::-webkit-scrollbar-thumb:hover {
    @apply bg-text-tertiary;
  }

  /* 选中文本样式 */
  ::selection {
    @apply bg-bloomberg-orange/30 text-text-primary;
  }

  /* 聚焦样式 */
  :focus-visible {
    @apply outline-2 outline-offset-2 outline-bloomberg-orange;
  }
}

/* 自定义组件样式 */
@layer components {
  /* 数据卡片 */
  .data-card {
    @apply bg-background-card border border-border-primary rounded-md p-4 mb-4;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  }

  .data-card:hover {
    @apply bg-background-secondary;
  }

  /* 新闻卡片 */
  .news-card {
    @apply data-card border-l-4 border-l-transparent transition-all duration-200;
  }

  .news-card:hover {
    @apply border-l-bloomberg-orange -translate-y-1;
  }

  /* 按钮 */
  .btn {
    @apply px-4 py-2 rounded font-medium text-sm transition-all duration-200;
    @apply disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-primary {
    @apply bg-bloomberg-orange text-white;
    @apply hover:bg-[#FF7722] active:scale-95;
  }

  .btn-secondary {
    @apply bg-transparent text-text-primary border border-border-primary;
    @apply hover:bg-background-tertiary hover:border-text-tertiary;
  }

  /* 输入框 */
  .input {
    @apply px-4 py-3 bg-background-secondary border border-border-primary rounded;
    @apply text-text-primary placeholder:text-text-tertiary;
    @apply focus:border-bloomberg-orange focus:ring-2 focus:ring-bloomberg-orange/20;
    @apply transition-all duration-200;
  }

  /* Ticker 徽章 */
  .ticker-badge {
    @apply inline-flex items-center px-3 py-1;
    @apply bg-asset-stock/15 border border-asset-stock/30 rounded;
    @apply font-data text-sm font-semibold text-asset-stock;
    @apply tracking-wider;
  }

  /* 实时指示器 */
  .live-indicator {
    @apply inline-flex items-center gap-2;
  }

  .live-indicator::before {
    content: '';
    @apply w-2 h-2 bg-market-positive rounded-full;
    animation: pulse 2s ease-in-out infinite;
  }

  /* 数据表格 */
  .data-table {
    @apply w-full border-collapse font-data text-sm;
  }

  .data-table thead {
    @apply bg-background-secondary sticky top-0 z-10;
  }

  .data-table th {
    @apply px-4 py-3 text-left font-semibold text-text-secondary;
    @apply border-b-2 border-border-primary;
  }

  .data-table td {
    @apply px-4 py-2 border-b border-border-secondary;
  }

  .data-table tr:hover {
    @apply bg-background-hover;
  }

  .data-table .numeric {
    @apply text-right tabular-nums;
  }
}

/* 工具类 */
@layer utilities {
  .tabular-nums {
    font-variant-numeric: tabular-nums;
  }

  .text-truncate {
    @apply overflow-hidden text-ellipsis whitespace-nowrap;
  }

  .animate-data-update {
    animation: dataUpdate 0.5s ease-out;
  }
}

/* 动画定义 */
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

@keyframes dataUpdate {
  0% {
    background-color: rgba(255, 102, 0, 0.3);
  }
  100% {
    background-color: transparent;
  }
}
```

### 6.2 响应式断点策略

```typescript
// lib/utils/responsive.ts

export const BREAKPOINTS = {
  xs: 480,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
  '3xl': 1920,
} as const;

export const LAYOUT_CONFIG = {
  // 桌面：三列布局
  desktop: {
    minWidth: BREAKPOINTS.xl,
    columns: 'grid-cols-[320px_1fr_320px]',
    gap: 'gap-6',
  },
  // 平板：两列布局（左列折叠）
  tablet: {
    minWidth: BREAKPOINTS.lg,
    maxWidth: BREAKPOINTS.xl - 1,
    columns: 'grid-cols-1',
    gap: 'gap-4',
  },
  // 移动：单列布局
  mobile: {
    maxWidth: BREAKPOINTS.lg - 1,
    columns: 'grid-cols-1',
    gap: 'gap-4',
  },
};
```

---

## 7. 开发检查清单

### 7.1 Phase 1: 环境搭建 ✅
- [ ] 安装所有依赖包
- [ ] 配置环境变量（`.env.local`）
- [ ] 引入 Bloomberg 主题 CSS
- [ ] 配置 Tailwind（复制 `tailwind.config.js`）
- [ ] 测试 `pnpm dev` 启动成功

### 7.2 Phase 2: 布局骨架 ✅
- [ ] 实现 `GlobalNavbar` 组件
- [ ] 实现 `BottomTicker` 组件
- [ ] 创建三列主布局（`MarketColumn`, `NewsColumn`, `InsightsColumn`）
- [ ] 配置响应式断点
- [ ] 测试在不同屏幕尺寸下的布局

### 7.3 Phase 3: 状态管理 ⏳
- [ ] 创建 `newsStreamStore.ts`
- [ ] 创建 `uiStateStore.ts`
- [ ] 实现 `useNewsStream` Hook（SSE 连接）
- [ ] 实现 `useKLineData` Hook（数据获取）
- [ ] 测试 Mock 数据流

### 7.4 Phase 4: 核心组件 ⏳
- [ ] 实现 `NewsCard` 组件
- [ ] 实现 `NewsPreviewModal` 组件
- [ ] 实现 `ChainOfThoughtDrawer` 组件
- [ ] 实现 `KLineChart` 组件
- [ ] 实现 `SentimentDial` 组件
- [ ] 实现 `CitationsList` 组件
- [ ] 测试所有组件在 Storybook 中

### 7.5 Phase 5: 交互逻辑 ⏳
- [ ] 新闻卡片点击 → 打开预览模态框
- [ ] 模态框内点击"查看推理" → 打开推理抽屉
- [ ] K 线图信号点击 → 打开相关新闻
- [ ] 过滤器和搜索功能
- [ ] 键盘导航支持
- [ ] 测试所有交互流程

### 7.6 Phase 6: 数据集成 ⏳
- [ ] 连接后端 SSE 接口
- [ ] 连接 K 线数据 API
- [ ] 连接市场概览 API
- [ ] 实现错误处理和重连逻辑
- [ ] 实现数据缓存策略
- [ ] 测试实时数据推送

### 7.7 Phase 7: 性能优化 ⏳
- [ ] 实现虚拟滚动（新闻列表）
- [ ] 优化 K 线图渲染（Canvas）
- [ ] 实现数据更新节流
- [ ] 代码分割和懒加载
- [ ] 图片优化（Next.js Image）
- [ ] 运行 Lighthouse 性能测试（目标：FCP < 1.5s, LCP < 2.5s, CLS < 0.1）

### 7.8 Phase 8: 可访问性 ⏳
- [ ] 所有交互元素支持键盘操作
- [ ] 添加 ARIA 标签
- [ ] 实现色盲友好模式切换
- [ ] 测试屏幕阅读器兼容性
- [ ] 确保色彩对比度 ≥ 4.5:1
- [ ] 运行 axe 可访问性检查

### 7.9 Phase 9: 测试 ⏳
- [ ] 编写单元测试（Jest + React Testing Library）
- [ ] 编写集成测试（Playwright）
- [ ] 端到端测试（关键用户流程）
- [ ] 错误边界测试
- [ ] 移动端触控测试
- [ ] 所有测试通过率 100%

### 7.10 Phase 10: 文档和部署 ⏳
- [ ] 更新组件文档（Storybook）
- [ ] 编写 README
- [ ] 生成 API 文档
- [ ] 配置 CI/CD
- [ ] 生产环境部署
- [ ] 性能监控配置

---

## 8. 常见问题和解决方案

### Q1: SSE 连接频繁断开？
**解决方案**:
```typescript
// 增加心跳检测和自动重连
let reconnectTimeout: NodeJS.Timeout;
eventSource.onerror = () => {
  eventSource.close();
  reconnectTimeout = setTimeout(() => connectSSE(), 5000);
};
```

### Q2: K 线图渲染卡顿？
**解决方案**:
```typescript
// 使用 Canvas 渲染器并禁用动画
const option = {
  animation: false,
  renderer: 'canvas',
};
```

### Q3: 新闻列表滚动性能差？
**解决方案**:
```bash
# 安装虚拟滚动库
pnpm add react-window

# 使用 FixedSizeList 渲染
<FixedSizeList height={600} itemCount={news.length} itemSize={120}>
  {Row}
</FixedSizeList>
```

### Q4: 移动端布局错乱？
**解决方案**:
```tsx
// 使用 Tailwind 响应式类
<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
```

### Q5: TypeScript 类型错误？
**解决方案**:
```typescript
// 确保所有 API 响应都有明确的类型定义
interface APIResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}
```

---

## 9. 下一步行动

### 立即开始
1. 克隆项目并切换到正确分支
2. 安装依赖：`cd frontend/web && pnpm install`
3. 复制环境变量：`cp .env.example .env.local`
4. 启动开发服务器：`pnpm dev`

### 开发顺序建议
1. **第 1 天**: 环境搭建 + 布局骨架
2. **第 2 天**: 状态管理 + 基础组件
3. **第 3 天**: 核心功能组件（新闻卡、K 线图）
4. **第 4 天**: 交互逻辑 + 数据集成
5. **第 5 天**: 性能优化 + 可访问性
6. **第 6 天**: 测试 + 文档

### 验收标准
- ✅ 所有组件通过 Storybook 展示
- ✅ 端到端测试覆盖率 > 80%
- ✅ Lighthouse 性能评分 > 90
- ✅ 无严重可访问性错误
- ✅ 支持桌面、平板、移动三种布局
- ✅ 实时数据推送延迟 < 2s

---

## 10. 参考资源

### 内部文档
- 设计规范: `docs/项目文档/前端规范/bloomberg-design-specification.md`
- API 文档: `docs/项目文档/API接口文档.md`
- 业务需求: `docs/项目文档/AI_real_time_news_plan1021.md`

### 外部资源
- [Next.js 文档](https://nextjs.org/docs)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [ECharts 文档](https://echarts.apache.org/handbook/en/get-started)
- [Zustand 文档](https://docs.pmnd.rs/zustand)
- [React Query 文档](https://tanstack.com/query/latest)

### 设计参考
- Bloomberg Terminal UI
- TradingView Charts
- nof1.ai (灵感来源)

---

**版本**: 3.0.0  
**最后更新**: 2025-10-26  
**维护者**: 前端开发团队  
**状态**: ✅ 可用于 AI 辅助开发

---

## 附录 A: 完整的 TypeScript 配置

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## 附录 B: ESLint 配置

```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "warn",
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

## 附录 C: Git 提交规范

```
feat: 新功能
fix: Bug 修复
style: 样式更新
refactor: 代码重构
perf: 性能优化
test: 测试相关
docs: 文档更新
chore: 构建/工具链更新

示例:
git commit -m "feat: 实现 NewsCard 组件"
git commit -m "fix: 修复 SSE 连接断开问题"
git commit -m "perf: 优化 K 线图渲染性能"
```
