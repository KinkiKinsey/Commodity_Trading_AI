import { create } from "zustand";

export type Direction = "bullish" | "bearish" | "neutral";

export type ChainOfThoughtStep = {
  id: string;
  step: number;
  text: string;
  evidence?: string;
  url?: string;
};

export type ComplianceStatus = "clean" | "masked" | "blocked";

export type NewsSignal = {
  signalId: string;
  signalType: "buy" | "sell";
  price: number;
  indexValue?: number;
  reasonTag?: string;
  newsId?: string;
  createdAt: string;
};

export type NewsStreamEvent = {
  eventId: string;
  timestamp: string;
  headline: string;
  summary?: string;
  direction: Direction;
  confidence: number;
  language: string;
  chain_of_thought: ChainOfThoughtStep[];
  citations: string[];
  signalTags: string[];
  complianceStatus: ComplianceStatus;
  signal?: NewsSignal;
};

export type StreamStatus =
  | { state: "connecting" }
  | { state: "open"; lastEventAt: number }
  | { state: "error"; message: string; lastEventAt?: number };

type NewsStreamStore = {
  events: Map<string, NewsStreamEvent>;
  order: string[];
  streamStatus: StreamStatus;
  setEvent: (payload: NewsStreamEvent) => void;
  setStreamStatus: (status: StreamStatus) => void;
  clear: () => void;
};

export const useNewsStreamStore = create<NewsStreamStore>((set) => ({
  events: new Map(),
  order: [],
  streamStatus: { state: "connecting" },
  setEvent: (payload) =>
    set((state) => {
      const existing = new Map(state.events);
      existing.set(payload.eventId, payload);
      const nextOrder = state.order.includes(payload.eventId)
        ? state.order
        : [payload.eventId, ...state.order].slice(0, 200);
      return {
        events: existing,
        order: nextOrder,
        streamStatus: { state: "open", lastEventAt: Date.now() }
      };
    }),
  setStreamStatus: (status) => set(() => ({ streamStatus: status })),
  clear: () =>
    set(() => ({
      events: new Map(),
      order: [],
      streamStatus: { state: "connecting" }
    }))
}));
