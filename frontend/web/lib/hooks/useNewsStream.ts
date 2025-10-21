import { useEffect } from "react";
import { useNewsStreamStore, NewsStreamEvent } from "@/lib/state/newsStreamStore";

export type UseNewsStreamOptions = {
  endpoint?: string;
};

const DEFAULT_ENDPOINT =
  process.env.NEXT_PUBLIC_NEWS_STREAM_ENDPOINT ?? "http://localhost:8000/api/news/stream";

export function useNewsStream({ endpoint = DEFAULT_ENDPOINT }: UseNewsStreamOptions = {}) {
  const setEvent = useNewsStreamStore((state) => state.setEvent);
  const setStreamStatus = useNewsStreamStore((state) => state.setStreamStatus);

  useEffect(() => {
    let eventSource: EventSource | undefined;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let retryAttempt = 0;

    const connect = () => {
      setStreamStatus({ state: "connecting" });
      eventSource = new EventSource(endpoint);

      eventSource.onopen = () => {
        retryAttempt = 0;
        setStreamStatus({ state: "open", lastEventAt: Date.now() });
      };

      eventSource.onmessage = (evt) => {
        // Heartbeat keeps the connection alive
        if (evt.event === "heartbeat") {
          setStreamStatus({ state: "open", lastEventAt: Date.now() });
          return;
        }

        try {
          const payload: NewsStreamEvent = JSON.parse(evt.data);
          setEvent(payload);
        } catch (error) {
          console.error("Failed to parse SSE payload", error);
        }
      };

      eventSource.onerror = () => {
        eventSource?.close();
        retryAttempt += 1;
        const delay = Math.min(30_000, 1000 * 2 ** retryAttempt);
        setStreamStatus({
          state: "error",
          message: "连接已断开，正在重试…",
          lastEventAt: Date.now()
        });
        retryTimer = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      eventSource?.close();
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
    };
  }, [endpoint, setEvent, setStreamStatus]);
}
