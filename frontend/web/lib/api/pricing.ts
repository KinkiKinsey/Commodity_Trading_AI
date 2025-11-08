export type PricingSignal = {
  signal_id: string;
  signal_type: "buy" | "sell";
  timestamp: string;
  price: number;
  trend: "BULLISH" | "BEARISH";
  source: string;
  interval_ref?: {
    start_date?: string;
    end_date?: string;
  };
  linked_news_ids?: string[];
};

export type PricingIndicatorSeriesPoint = {
  timestamp: string;
  value: number;
};

export type PricingIndicator = {
  name: string;
  description?: string;
  type?: string;
  summary?: string;
  series: PricingIndicatorSeriesPoint[];
};

export type PricingBar = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
};

export type PricingKlineResponse = {
  ticker: string;
  display_name: string;
  timezone: string;
  range: {
    start: string;
    end: string;
    count: number;
  };
  series: PricingBar[];
  ml_moving_average: {
    summary: string;
    time_intervals: Array<{
      start_date: string;
      end_date: string;
      trend: "BULLISH" | "BEARISH";
    }>;
    trend_points: Array<{
      timestamp: string;
      price: number;
      trend: "BULLISH" | "BEARISH";
      interval_ref?: {
        start_date: string;
        end_date: string;
      };
    }>;
    parameters: {
      window: number;
      sigma: number;
      mult: number;
    };
    line: PricingIndicatorSeriesPoint[];
    upper_band?: PricingIndicatorSeriesPoint[];
    lower_band?: PricingIndicatorSeriesPoint[];
  };
  signals: PricingSignal[];
  indicators: PricingIndicator[];
  source: {
    exchange: string;
    instrument_type: string;
    currency?: string;
    data_vendor?: string;
  };
  metadata: {
    fetched_at: string;
    data_latency_seconds: number;
    source_latency_seconds?: number;
    notes?: string;
  };
  request_id?: string;
  sector?: string;
  errors?: Array<{
    code: string;
    message: string;
  }>;
};

export type QuoteLevel = {
  price: number;
  volume: number;
};

export type PricingTickResponse = {
  instrument_id: string;
  last_price: number;
  volume: number;
  trading_day: string;
  updated_at: string;
  bid: QuoteLevel;
  ask: QuoteLevel;
  raw: Record<string, unknown>;
};
