import { useEffect } from "react";
import { useNewsStreamStore, NewsStreamEvent } from "@/lib/state/newsStreamStore";
import { NEWS_STREAM_ENDPOINT, NEWS_LATEST_ENDPOINT } from "@/lib/config/env";

export type UseNewsStreamOptions = {
  endpoint?: string;
};

export function useNewsStream({ endpoint = NEWS_STREAM_ENDPOINT }: UseNewsStreamOptions = {}) {
  const setEvent = useNewsStreamStore((state) => state.setEvent);
  const setStreamStatus = useNewsStreamStore((state) => state.setStreamStatus);

  useEffect(() => {
    let eventSource: EventSource | undefined;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let retryAttempt = 0;
    let heartbeatHandler: ((event: MessageEvent) => void) | undefined;
    let cancelled = false;

    const connect = () => {
      if (cancelled) {
        return;
      }
      setStreamStatus({ state: "connecting" });
      try {
        eventSource = new EventSource(endpoint);
      } catch (error) {
        console.error("Failed to initialise news stream", error);
        setStreamStatus({
          state: "error",
          message: "Failed to initialise stream",
          lastEventAt: Date.now()
        });
        return;
      }

      eventSource.onopen = () => {
        retryAttempt = 0;
        setStreamStatus({ state: "open", lastEventAt: Date.now() });
      };

      heartbeatHandler = () => {
        setStreamStatus({ state: "open", lastEventAt: Date.now() });
      };

      eventSource.addEventListener("heartbeat", heartbeatHandler as EventListener);

      eventSource.onmessage = (evt) => {
        try {
          const payload: NewsStreamEvent = JSON.parse(evt.data);
          setStreamStatus({ state: "open", lastEventAt: Date.now() });
          setEvent(payload);
        } catch (error) {
          console.error("Failed to parse SSE payload", error);
        }
      };

      eventSource.onerror = () => {
        if (cancelled) {
          return;
        }
        if (eventSource && heartbeatHandler) {
          eventSource.removeEventListener("heartbeat", heartbeatHandler as EventListener);
        }
        eventSource?.close();
        retryAttempt += 1;
        const delay = Math.min(30_000, 1000 * 2 ** retryAttempt);
        setStreamStatus({
          state: "error",
          message: "Connection lost, retrying",
          lastEventAt: Date.now()
        });
        retryTimer = setTimeout(() => {
          connect();
        }, delay);
      };
    };

    const preloadLatest = async () => {
      try {
        const response = await fetch(NEWS_LATEST_ENDPOINT, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Failed to load latest news (${response.status})`);
        }
        const items = (await response.json()) as NewsStreamEvent[];
        if (!Array.isArray(items) || cancelled) {
          return;
        }
        for (const item of [...items].reverse()) {
          setEvent(item, { updateStatus: false });
        }
      } catch (error) {
        console.error("Failed to preload latest news", error);
      }
    };

    connect();
    preloadLatest();

    return () => {
      cancelled = true;
      if (eventSource && heartbeatHandler) {
        eventSource.removeEventListener("heartbeat", heartbeatHandler as EventListener);
      }
      eventSource?.close();
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
    };
  }, [endpoint, setEvent, setStreamStatus]);
}

