export type PlaceholderPoint = {
  timestamp: string;
  close: number;
  volume?: number;
};

export function generatePlaceholderSeries(length = 60): PlaceholderPoint[] {
  const now = Date.now();
  let value = 80 + Math.random() * 10;
  const points: PlaceholderPoint[] = [];

  for (let i = length - 1; i >= 0; i -= 1) {
    value += (Math.random() - 0.5) * 1.2;
    points.push({
      timestamp: new Date(now - i * 60_000).toISOString(),
      close: Number(value.toFixed(2)),
      volume: Math.round(1_000 + Math.random() * 500)
    });
  }

  return points;
}
