export type CoverageTier = 'full' | 'state' | 'results' | 'elections';

export interface CoverageTierMeta {
  label: string;
  description: string;
  color: 'success' | 'warning' | 'default';
}

export type CoverageTierMap = Partial<Record<string, CoverageTier>>;

export const COVERAGE_TIER_META: Record<CoverageTier, CoverageTierMeta> = {
  full: {
    label: 'Full Coverage',
    description:
      'Dedicated state integration — elections, races, candidates, and official results are ingested directly from the state source.',
    color: 'success',
  },
  state: {
    label: 'State Integration',
    description:
      'Dedicated state source ingests elections, races, and candidates. Results ingestion is not available yet.',
    color: 'warning',
  },
  results: {
    label: 'Results Adapter',
    description:
      'Live election-night results available when configured per election. Elections and races come from the national Civic data feed.',
    color: 'warning',
  },
  elections: {
    label: 'Elections Only',
    description:
      'Races and candidates are available via the national Civic data feed. No dedicated results adapter yet.',
    color: 'default',
  },
};

/**
 * Returns the coverage tier for a state.
 * coverageTiers comes from /api/coverage/sync-status/ and is the source of
 * truth. adapterStates is kept only as a compatibility fallback for older API
 * responses that predate coverage_tiers.
 */
export function getTier(
  stateCode: string,
  coverageTiers?: CoverageTierMap,
  adapterStates?: string[],
): CoverageTier {
  const code = stateCode.toUpperCase();
  const tier = coverageTiers?.[code];
  if (tier) return tier;
  if (adapterStates?.includes(code)) return 'results';
  return 'elections';
}
