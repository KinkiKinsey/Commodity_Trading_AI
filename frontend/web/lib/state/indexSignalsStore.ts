import { create } from "zustand";

export type IndexSignal = {
  signalId: string;
  signalType: "buy" | "sell";
  price: number;
  createdAt: string;
  indexValue?: number;
  reasonTag?: string;
  newsId?: string;
};

type IndexSignalsState = {
  signals: Record<string, IndexSignal[]>;
  isLoading: boolean;
  error?: string;
  setSignals: (symbol: string, payload: IndexSignal[]) => void;
  setLoading: (flag: boolean) => void;
  setError: (message?: string) => void;
};

export const useIndexSignalsStore = create<IndexSignalsState>((set) => ({
  signals: {},
  isLoading: false,
  error: undefined,
  setSignals: (symbol, payload) =>
    set((state) => ({
      signals: { ...state.signals, [symbol]: payload },
      isLoading: false,
      error: undefined
    })),
  setLoading: (flag) => set(() => ({ isLoading: flag })),
  setError: (message) => set(() => ({ error: message, isLoading: false }))
}));
