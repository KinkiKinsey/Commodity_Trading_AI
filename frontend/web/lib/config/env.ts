const stripTrailingSlash = (value?: string | null) =>
  value ? value.replace(/\/+$/, "") : undefined;

const ensureLeadingSlash = (path: string) => (path.startsWith("/") ? path : `/${path}`);

const baseUrl = stripTrailingSlash(process.env.NEXT_PUBLIC_API_BASE_URL);

const buildEndpoint = (envValue: string | undefined, fallbackPath: string) => {
  if (envValue) {
    const trimmed = envValue.trim();
    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
      return trimmed;
    }
    if (trimmed.startsWith("/")) {
      return trimmed;
    }
    if (baseUrl) {
      return `${baseUrl}/${trimmed}`;
    }
    return ensureLeadingSlash(trimmed);
  }

  if (baseUrl) {
    return `${baseUrl}${ensureLeadingSlash(fallbackPath)}`;
  }

  return ensureLeadingSlash(fallbackPath);
};

export const NEWS_STREAM_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_NEWS_STREAM_ENDPOINT,
  "/api/news/stream"
);

export const PRICING_KLINE_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_PRICING_KLINE_ENDPOINT,
  "/api/pricing/kline"
);

export const MARKETS_OVERVIEW_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_MARKETS_OVERVIEW_ENDPOINT,
  "/api/markets/overview"
);

export const INDEX_SIGNALS_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_INDEX_SIGNALS_ENDPOINT,
  "/api/signals"
);

export const NEWS_LATEST_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_NEWS_LATEST_ENDPOINT,
  "/api/news/latest"
);

export const NEWS_TRANSLATION_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_NEWS_TRANSLATION_ENDPOINT,
  "/api/news/translate"
);

export const NEWS_ANALYZE_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_NEWS_ANALYZE_ENDPOINT,
  "/api/news/analyze"
);

export const OIL_FACTORS_ENDPOINT = buildEndpoint(
  process.env.NEXT_PUBLIC_OIL_FACTORS_ENDPOINT,
  "/api/oil/factors"
);

export const API_BASE_URL = baseUrl ?? "";
