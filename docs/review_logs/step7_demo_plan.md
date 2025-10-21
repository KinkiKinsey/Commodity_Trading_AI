# Stage 7 demo & mock data checklist

This note captures the assets and steps required to deliver the Stage 7 verification demo (K-line + ML trend overlay) and to support future automated tests.

---

## 1. Mock data assets

| Asset | Location | Purpose |
|-------|----------|---------|
| K-line contract sample | `docs/review_logs/step7_kline.json` | Canonical 200-response for `/api/pricing/kline`. Powers chart + modal demo. |
| News payload (existing) | `backend/tests/fixtures/news_stream_sample.json` *(TODO)* | Used to link `linked_news_ids` from the signal to modal content. |
| Indicator mapping | `docs/datasets/ticker_mapping.csv` | Ensures ticker ↔ display name ↔ alias is consistent when seeding stores. |

### Suggested frontend mock hook

```ts
// frontend/web/lib/mocks/useKlineMock.ts
import payload from "@/mocks/step7_kline.json";

export function useKlineMock() {
  return {
    data: payload,
    isLoading: false,
    error: null,
  };
}
```

The JSON file can be imported directly (Next.js supports JSON modules). For Storybook, drop the same file under `.storybook/mocks/`.

---

## 2. Demo flow script

1. **Landing:** Open `http://localhost:3000/news/real-time?symbol=CLZ25.NYM` with dark theme enabled. Ensure only raw K-line is visible.
2. **Analyse action:** Click the “分析” button. Confirm red/blue ML trend line fades in and legend updates with `ml_moving_average.summary`.
3. **Reversal marker:** Hover the 2025-10-15 buy signal, then click to open `NewsPreviewModal`. Verify the modal shows linked news, inference chain, and `metadata.data_latency_seconds`.
4. **Toggle indicators:** Enable “Index 1” and “Index 2” toggles. Check that overlays render without shifting the ML trend context.
5. **Latency banner:** Simulate `data_latency_seconds > 120` by editing the mock in browser DevTools. Confirm yellow banner + manual refresh button.
6. **i18n switch:** Toggle locale to English; reused strings should map via `next-intl`.

Record the walkthrough (1080p, 60fps) and archive under `docs/review_logs/step7_demo.mp4` after review.

---

## 3. Automation hooks

- **Frontend Playwright**: load `step7_kline.json` and assert:
  - Candlestick renders 18 bars.
  - Reversal markers count equals `signals.length`.
  - Modal chain-of-thought length matches `linked_news_ids`.
- **Backend Pytest**:
  - Validate response with jsonschema using `pricing_kline.schema.json`.
  - Assert ticker mapping table resolves `display_name`.

---

## 4. Open items

- [ ] Capture actual news fixtures and align IDs with `linked_news_ids`.
- [ ] Decide whether auxiliary indicators are served via `/api/pricing/kline` or separate endpoints.
- [ ] Document SSE fallback for when pricing feed is stale > 5 minutes.
