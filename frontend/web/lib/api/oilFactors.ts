import { API_BASE_URL, OIL_FACTORS_ENDPOINT } from "@/lib/config/env";

export type OilFactorRecord = {
  factor: string;
  scope: string;
  trend_count?: number;
  weighted_mean?: number;
  weighted_variance?: number;
  risk_reward_ratio?: number;
  average_duration?: number;
  total_duration?: number;
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  time_interval?: string;
  driver_type?: string;
  AI_Reason?: string;
};

export type OilFactorResponse = {
  ticker: string;
  language: string;
  count: number;
  factors: OilFactorRecord[];
};

const DEFAULT_ORIGIN = "http://localhost:3000";

function resolveEndpoint(endpoint: string): URL {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return new URL(endpoint);
  }

  const origin =
    API_BASE_URL && API_BASE_URL.length > 0
      ? API_BASE_URL
      : typeof window !== "undefined" && window.location
      ? window.location.origin
      : DEFAULT_ORIGIN;

  return new URL(endpoint, origin);
}

export async function fetchOilFactors(params: {
  ticker?: string;
  language?: string;
  forceRefresh?: boolean;
}): Promise<OilFactorResponse> {
  const url = resolveEndpoint(OIL_FACTORS_ENDPOINT);

  if (params.ticker) url.searchParams.set("ticker", params.ticker);
  if (params.language) url.searchParams.set("language", params.language);
  if (params.forceRefresh) url.searchParams.set("force_refresh", "true");

  const response = await fetch(url.toString(), {
    method: "GET",
    headers: { "Accept": "application/json" }
  });

  if (!response.ok) {
    throw new Error(`Failed to load oil factors (${response.status})`);
  }

  return (await response.json()) as OilFactorResponse;
}
