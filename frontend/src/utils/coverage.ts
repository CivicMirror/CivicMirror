export type CoverageTier = 'full' | 'results' | 'elections';

export interface CoverageTierMeta {
  label: string;
  description: string;
  color: 'success' | 'warning' | 'default';
}

export const COVERAGE_TIER_META: Record<CoverageTier, CoverageTierMeta> = {
  full: {
    label: 'Full Coverage',
    description:
      'Dedicated state SOS integration — elections, races, candidates, and live results are ingested directly from the state source.',
    color: 'success',
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
 * Explicit coverage tier per state code.
 * States not listed here default to 'elections'.
 */
export const COVERAGE: Partial<Record<string, CoverageTier>> = {
  // Full SOS integration + live results
  WV: 'full',
  CO: 'full',
  SC: 'full',
  MA: 'full',
  VA: 'full',
  AZ: 'full',
  NC: 'full',

  // Results adapter (election-night results when results_url is configured)
  AR: 'results',
  CT: 'results',
  IA: 'results',
  AK: 'results',
  DE: 'results',
  HI: 'results',
  ID: 'results',
  IN: 'results',
  KS: 'results',
  LA: 'results',
  ME: 'results',
  MS: 'results',
  MT: 'results',
  ND: 'results',
  NE: 'results',
  NH: 'results',
  NV: 'results',
  OK: 'results',
  RI: 'results',
  SD: 'results',
  VT: 'results',
  WI: 'results',
  WY: 'results',
};

/**
 * Returns the coverage tier for a state.
 * adapterStates (from /api/coverage/sync-status/) promotes unlisted states to
 * 'results' automatically when a new results adapter is registered on the backend.
 */
export function getTier(stateCode: string, adapterStates?: string[]): CoverageTier {
  const code = stateCode.toUpperCase();
  const hardcoded = COVERAGE[code];
  if (hardcoded) return hardcoded;
  if (adapterStates?.includes(code)) return 'results';
  return 'elections';
}
