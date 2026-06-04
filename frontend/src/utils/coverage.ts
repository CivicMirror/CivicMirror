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

export function getTier(stateCode: string): CoverageTier {
  return COVERAGE[stateCode.toUpperCase()] ?? 'elections';
}
