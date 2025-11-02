import { NEWS_ANALYZE_ENDPOINT } from "@/lib/config/env";
import type { NewsStreamEvent } from "@/lib/state/newsStreamStore";

export type AnalyzeNewsRequest = {
  text: string;
  headline?: string;
  summary?: string;
};

export async function analyzeNews(payload: AnalyzeNewsRequest): Promise<NewsStreamEvent> {
  const response = await fetch(NEWS_ANALYZE_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`News analysis failed (${response.status}): ${detail}`);
  }

  const data = (await response.json()) as NewsStreamEvent;
  return data;
}
