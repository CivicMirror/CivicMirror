const BASE_URL = (import.meta.env.VITE_CIVIC_API_URL as string) || 'http://localhost:8001';
const API_KEY = (import.meta.env.VITE_CIVIC_API_KEY as string) || '';

async function civicFetch<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(path, BASE_URL);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.set(k, v);
      }
    });
  }

  const res = await fetch(url.toString(), {
    headers: { 'X-Api-Key': API_KEY },
  });

  if (!res.ok) {
    throw new Error(`CivicAPI ${res.status}: ${res.statusText} (${path})`);
  }

  return res.json() as Promise<T>;
}

export const civicApiClient = { fetch: civicFetch };

export async function checkCivicApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(new URL('/health/', BASE_URL).toString());
    return res.ok;
  } catch {
    return false;
  }
}
