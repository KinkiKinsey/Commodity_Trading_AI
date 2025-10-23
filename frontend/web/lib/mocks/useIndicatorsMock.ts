import indicatorsMock from "../../mocks/pricing_indicators.json";

export type IndicatorMock = typeof indicatorsMock;

type UseIndicatorsMockReturn = {
  data: IndicatorMock;
  isLoading: boolean;
  error: null;
};

export function useIndicatorsMock(): UseIndicatorsMockReturn {
  return {
    data: indicatorsMock,
    isLoading: false,
    error: null,
  };
}

export function getIndicatorSeries<Name extends keyof IndicatorMock["indicators"]>(
  name: Name,
) {
  return indicatorsMock.indicators[name];
}
