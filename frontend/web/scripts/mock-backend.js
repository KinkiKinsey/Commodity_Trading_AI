const http = require("http");

const clients = new Set();

function buildSampleEvent() {
  const now = new Date();
  return {
    eventId: `demo-supply-${now.getTime()}`,
    timestamp: now.toISOString(),
    headline: "Supply tensions in Venezuela keep crude bid",
    summary:
      "Talks between Caracas and foreign majors stalled again, raising the odds of export disruptions that would tighten Atlantic Basin balances into winter.",
    direction: "bullish",
    confidence: 0.86,
    language: "en-US",
    chain_of_thought: [
      {
        id: "step-0",
        step: 0,
        text: "Negotiations over production-sharing contracts broke down, risking October output volumes.",
      },
      {
        id: "step-1",
        step: 1,
        text: "U.S. secondary sanctions waivers are unlikely to be renewed, increasing shipping friction.",
      },
      {
        id: "step-2",
        step: 2,
        text: "Refiners in the Gulf are already running low on medium sour barrels, so any Venezuelan shortfall forces higher bids for WTI and Brent.",
      },
    ],
    citations: [
      "https://www.reuters.com/markets/energy/venezuela-talks-2025-10-22/",
      "https://www.argusmedia.com/en/news/venezuelan-crude-trade-2025",
    ],
    signalTags: ["OPEC+", "Geopolitics"],
    complianceStatus: "clean",
    signal: {
      signalId: `sig-${now.getTime()}`,
      signalType: "buy",
      price: 87.92,
      indexValue: 5123.7,
      reasonTag: "Supply risk",
      newsId: `demo-supply-${now.getTime()}`,
      createdAt: now.toISOString(),
    },
  };
}

function buildKlineResponse() {
  const now = Date.now();
  const hours = Array.from({ length: 48 }, (_, idx) => now - (47 - idx) * 60 * 60 * 1000);
  const series = hours.map((timestamp, idx) => {
    const base = 86.5 + Math.sin(idx / 6) * 1.2;
    const close = parseFloat((base + Math.random() * 0.4).toFixed(2));
    const open = parseFloat((close + (Math.random() - 0.5) * 0.6).toFixed(2));
    const high = Math.max(open, close) + parseFloat((Math.random() * 0.5).toFixed(2));
    const low = Math.min(open, close) - parseFloat((Math.random() * 0.5).toFixed(2));
    return {
      timestamp: new Date(timestamp).toISOString(),
      open,
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close,
      volume: Math.floor(120000 + Math.random() * 25000),
    };
  });

  const trendPoints = series.filter((_, idx) => idx % 12 === 0).map((bar, idx) => ({
    timestamp: bar.timestamp,
    price: bar.close,
    trend: idx % 2 === 0 ? "BULLISH" : "BEARISH",
  }));

  return {
    ticker: "CLZ25.NYM",
    display_name: "WTI Crude (Dec 2025)",
    timezone: "America/New_York",
    range: {
      start: series[0].timestamp,
      end: series[series.length - 1].timestamp,
      count: series.length,
    },
    series,
    ml_moving_average: {
      summary:
        "WTI keeps a constructive bias above 86 USD with alternating consolidation bands; momentum flips bullish in the latest New York session.",
      time_intervals: [
        {
          start_date: series[0].timestamp,
          end_date: series[20].timestamp,
          trend: "BEARISH",
        },
        {
          start_date: series[20].timestamp,
          end_date: series[47].timestamp,
          trend: "BULLISH",
        },
      ],
      trend_points: trendPoints,
      parameters: {
        window: 9,
        sigma: 1.8,
        mult: 2.4,
      },
      line: series.map((bar) => ({
        timestamp: bar.timestamp,
        value: parseFloat((bar.close * 0.995).toFixed(2)),
      })),
    },
    signals: [
      {
        signal_id: "sig-demo-1",
        signal_type: "buy",
        timestamp: series[44].timestamp,
        price: series[44].close,
        trend: "BULLISH",
        source: "ml_moving_average",
        linked_news_ids: ["demo-supply-latest"],
      },
    ],
    indicators: [],
    source: {
      exchange: "NYMEX",
      instrument_type: "Futures",
      currency: "USD",
      data_vendor: "Mock",
    },
    metadata: {
      fetched_at: new Date().toISOString(),
      data_latency_seconds: 12,
      notes: "Mocked payload served by scripts/mock-backend.js",
    },
  };
}

function handleSse(req, res) {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
    "Access-Control-Allow-Origin": "*",
  });

  res.write("event: heartbeat\ndata: {}\n\n");
  const heartbeat = setInterval(() => {
    res.write("event: heartbeat\ndata: {}\n\n");
  }, 15000);

  const client = { res };
  clients.add(client);

  const sendEvent = () => {
    const event = buildSampleEvent();
    res.write(`data: ${JSON.stringify(event)}\n\n`);
  };

  sendEvent();
  const eventInterval = setInterval(sendEvent, 40000);

  req.on("close", () => {
    clearInterval(heartbeat);
    clearInterval(eventInterval);
    clients.delete(client);
  });
}

function handleKline(res) {
  const payload = buildKlineResponse();
  res.writeHead(200, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(JSON.stringify(payload));
}

const server = http.createServer((req, res) => {
  if (req.url.startsWith("/api/news/stream")) {
    handleSse(req, res);
    return;
  }

  if (req.url.startsWith("/api/pricing/kline")) {
    handleKline(res);
    return;
  }

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    });
    res.end();
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Not found" }));
});

const PORT = process.env.MOCK_BACKEND_PORT ? Number(process.env.MOCK_BACKEND_PORT) : 8000;

server.listen(PORT, () => {
  console.log(`[mock-backend] listening on http://localhost:${PORT}`);
});

