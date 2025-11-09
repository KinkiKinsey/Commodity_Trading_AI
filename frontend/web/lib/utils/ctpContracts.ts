
export const DEFAULT_CTP_CONTRACT_COUNT = 6;
export const CTP_CONTRACT_BUFFER = 8;

export function generateCtpContractIds(count: number, referenceDate: Date = new Date()): string[] {
  const ids: string[] = [];
  const now = new Date(referenceDate);
  let year = now.getUTCFullYear();
  let month = now.getUTCMonth() + 2; // skip current month, start from next
  if (month > 12) {
    month = 1;
    year += 1;
  }

  while (ids.length < count) {
    const yy = (year % 100).toString().padStart(2, "0");
    const mm = month.toString().padStart(2, "0");
    ids.push(`CL${yy}${mm}-NYM`);
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }

  return ids;
}

export function normalizeContractId(id: string): string | null {
  const trimmed = id.trim();
  if (!trimmed) {
    return null;
  }
  const match = trimmed.match(/^CL\d{4}-NYM$/i);
  return match ? match[0].toUpperCase() : null;
}
