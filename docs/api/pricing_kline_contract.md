# `/api/pricing/kline` response contract (draft v0.1)

> Purpose: align backend implementation and frontend integration for the Sector2 K-line experience in **Stage 7**.  
> Scope: applies to all instruments served through the pricing microservice (initially Yahoo Finance futures tickers).

---

## 1. Endpoint overview

- **Method**: `GET`
- **Path**: `/api/pricing/kline`
- **Query params**
  - `ticker` *(required)* – canonical Yahoo Finance ticker, e.g. `CLZ25.NYM`
  - `days` *(optional, default=180)* – number of calendar days of history to pull (max 720)
  - `include_indicators` *(optional, default=true)* – toggle auxiliary indicator payloads
  - `force_refresh` *(optional, default=false)* – bypass cache when `true`

Successful responses must conform to [`pricing-kline-response.json`](schemas/pricing_kline.schema.json). Schema validation should be enforced in backend unit/integration tests and in the frontend mock fixtures.

---

## 2. High level shape

| Field | Type | Notes |
|-------|------|-------|
| `ticker` | string | Canonical Yahoo Finance ticker (mirrors request). |
| `display_name` | string | User-facing contract name pulled from ticker mapping. |
| `range` | object | Start/end timestamps (ISO-8601 UTC) and total bar count. |
| `series` | array\<Bar\> | OHLCV bars ordered ascending by `timestamp`. Used for the base candlestick chart. |
| `ml_moving_average` | object | Result bundle returned by `ml_moving_average(df)` including `summary`, `time_intervals`, RBF line/bands, and reversal markers. |
| `signals` | array\<Signal\> | Buy/Sell markers derived from the latest ML trend reversal. Primary driver for modal trigger. |
| `indicators` | array\<Indicator\> | Optional extension indicators (Index 1 / Index 2 etc.). |
| `metadata` | object | Data latency, fetch timestamp, optional notes for UI status bar. |
| `errors` | array\<Error\> | Optional non-fatal issues (e.g. auxiliary indicator failure). Frontend logs + shows warning pill. |

Detailed property requirements are listed in the JSON schema.

---

## 3. Example payload

See [`../review_logs/step7_kline.json`](../review_logs/step7_kline.json) for a canonical 200-response assembled from mock Yahoo data plus `ml_moving_average` output. This fixture is intended for:

1. Backend contract tests (`pytest --maxfail=1 --disable-warnings -k test_pricing_kline_contract`).
2. Frontend storybook / play tests (seed the SSE mock with the JSON to render charts and modals).
3. Demo recording in Stage 7 (acts as deterministic data source).

---

## 4. Validation & QA checklist

- [ ] Pydantic response model matches the schema (`jsonschema.validate` during CI).
- [ ] Candlestick series contains at least 200 bars for default request.
- [ ] `ml_moving_average.time_intervals` + `signals[*].interval_ref` align on boundaries.
- [ ] Trend reversal in the example (2025-10-10) maps to linked news IDs and appears in modal demo.
- [ ] Latency banner logic uses `metadata.data_latency_seconds`.

> Any schema-breaking changes must update both this document and the JSON schema with a bumped version tag.
