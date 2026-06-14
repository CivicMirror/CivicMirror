import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

export interface SourceStatus {
  last_completed_at: string;
  status: string;
  records_created: number;
  records_updated: number;
  records_skipped: number;
}

export interface SyncStatusResponse {
  as_of: string;
  global: Record<string, SourceStatus>;
  by_state: Record<string, Record<string, SourceStatus>>;
}

export function useCoverageSyncStatus(): SyncStatusResponse | null {
  const [status, setStatus] = useState<SyncStatusResponse | null>(null);

  useEffect(() => {
    void apiClient
      .get<SyncStatusResponse>('/api/coverage/sync-status/')
      .then((res) => setStatus(res.data))
      .catch(() => undefined);
  }, []);

  return status;
}

/** Returns the most recently completed sync entry for a given state, across all sources. */
export function latestStateSync(
  byState: Record<string, Record<string, SourceStatus>>,
  stateCode: string,
): SourceStatus | null {
  const stateSources = byState[stateCode.toUpperCase()];
  if (!stateSources) return null;
  return Object.values(stateSources).reduce<SourceStatus | null>((best, current) => {
    if (!best) return current;
    return current.last_completed_at > best.last_completed_at ? current : best;
  }, null);
}
