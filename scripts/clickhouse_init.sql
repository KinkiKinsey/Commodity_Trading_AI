-- Create database
CREATE DATABASE IF NOT EXISTS ctp;

-- Raw tick table
CREATE TABLE IF NOT EXISTS ctp.ctp_ticks (
    symbol String,
    local_ts DateTime64(3, 'UTC'),
    exchange_ts DateTime64(3, 'UTC'),
    update_time String,
    update_millisec UInt32,
    last_price Float64,
    bid_price1 Float64,
    bid_volume1 Float64,
    ask_price1 Float64,
    ask_volume1 Float64,
    volume Float64
) ENGINE = MergeTree
PARTITION BY toDate(local_ts)
ORDER BY (symbol, local_ts);

-- Aggregated bars
CREATE TABLE IF NOT EXISTS ctp.ctp_bars_1m (
    symbol String,
    ts DateTime64(3, 'UTC'),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64
) ENGINE = MergeTree
PARTITION BY toDate(ts)
ORDER BY (symbol, ts);

CREATE MATERIALIZED VIEW IF NOT EXISTS ctp.mv_ticks_to_1m
TO ctp.ctp_bars_1m
AS
SELECT
    symbol,
    toStartOfInterval(local_ts, INTERVAL 1 MINUTE) AS ts,
    anyHeavy(last_price) as open,
    max(last_price) as high,
    min(last_price) as low,
    anyLast(last_price) as close,
    sum(volume) as volume
FROM ctp.ctp_ticks
GROUP BY symbol, ts;
