export function resolveApiUrl(endpoint: string): URL {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return new URL(endpoint);
  }

  const origin =
    typeof window !== "undefined" && window.location ? window.location.origin : "http://localhost:3000";

  return new URL(endpoint, origin);
}
