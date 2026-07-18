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
      'Has dedicated backend support for the full core workflow: election discovery, race and candidate creation, and official results ingestion for federal, statewide, and state legislative races. Missing items, if any, are enhanced data such as local races, precinct detail, ballot-measure depth, biographies, GIS boundaries, or historical backfills.',
    color: 'success',
  },
  state: {
    label: 'State Integration',
    description:
      'Has a dedicated backend state source for pre-election data: elections, races, and candidates can be created from official state data. Missing official results ingestion, so result comparison depends on a future adapter or other configured result source.',
    color: 'warning',
  },
  results: {
    label: 'Results Adapter',
    description:
      'Has a backend results adapter that can ingest official vote totals when an election is configured for that source. Missing a dedicated state election/race/candidate pipeline, so race setup still depends on the national Civic feed, existing records, or manual configuration.',
    color: 'warning',
  },
  elections: {
    label: 'Elections Only',
    description:
      'Has baseline election and race availability through the national Civic data feed. Missing dedicated state ingestion and missing a dedicated results adapter, so candidate/race completeness and official results are limited compared with state-specific integrations.',
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
