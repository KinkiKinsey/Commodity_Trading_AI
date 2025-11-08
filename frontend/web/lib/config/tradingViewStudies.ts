/**
 * TradingView indicator configuration derived from INDEX1.xlsx exports.
 * The workbook lists the Pine scripts we designed on TV and captures the
 * parameter values we care about (e.g. BB length/multiplier, RSI levels).
 *
 * For now we manually encode the bits TradingView's `studies_overrides`
 * API understands. When needed we can extend this module to parse the
 * workbook dynamically or source values from an API.
 */

export const DEFAULT_TV_STUDIES = ["STD;Bollinger_Bands", "STD;MACD", "STD;RSI"];

export const DEFAULT_TV_STUDY_OVERRIDES: Record<string, string | number | boolean> = {
  // Bollinger Bands (BBAND sheet → length 20, multiplier 2.0)
  "bollinger bands.length": 20,
  "bollinger bands.stddev": 2,
  "bollinger bands.median.color": "#2157F3",
  "bollinger bands.median.linewidth": 1,
  "bollinger bands.upper.color": "rgba(8,153,129,0.55)",
  "bollinger bands.upper.linewidth": 2,
  "bollinger bands.lower.color": "rgba(242,54,69,0.55)",
  "bollinger bands.lower.linewidth": 2,

  // MACD defaults (Excel sheet MLMA/standard TV settings)
  "macd.fast length": 12,
  "macd.slow length": 26,
  "macd.signal smoothing": 9,
  "macd.macd.color": "#2157F3",
  "macd.signal.color": "#F23645",
  "macd.histogram.color": "#089981",

  // RSI (LONGTERM sheet → length 14, levels 70/30)
  "relative strength index.length": 14,
  "relative strength index.level.0": 70,
  "relative strength index.level.1": 30,
  "relative strength index.level.0.color": "#F23645",
  "relative strength index.level.1.color": "#089981",
  "relative strength index.levels.style": 0,
};
