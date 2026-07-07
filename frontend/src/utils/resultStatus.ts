import type { ChipProps } from '@mui/material';
import type { Race } from '../types';

/**
 * 'unofficial' is not a certification_status value the backend emits — it's a
 * panel-only key for when reported result rows exist ahead of certification_status
 * catching up (e.g. election-night unofficial tallies while status is still
 * 'results_pending'). See resolveResultStatusKey.
 */
export type ResultStatusKey = Race['certification_status'] | 'unofficial';

export interface ResultStatusConfig {
  /** Short chip text, shared by CertificationBadge and OfficialResultsPanel. */
  label: string;
  color: ChipProps['color'];
  variant: ChipProps['variant'];
  /** Section heading used by OfficialResultsPanel. */
  title: string;
  /** Explanatory sentence used by OfficialResultsPanel. */
  description: string;
  /** Prefix for the results table's vote/percent columns. */
  voteColumnPrefix: string;
}

export const RESULT_STATUS_MAP: Record<ResultStatusKey, ResultStatusConfig> = {
  upcoming: {
    label: 'Upcoming',
    color: 'default',
    variant: 'outlined',
    title: 'Upcoming',
    description: 'This race has not yet occurred.',
    voteColumnPrefix: 'Result',
  },
  results_pending: {
    label: 'Results Pending',
    color: 'warning',
    variant: 'outlined',
    title: 'Results Pending',
    description: 'Election results are not available yet.',
    voteColumnPrefix: 'Result',
  },
  unofficial: {
    label: 'Unofficial',
    color: 'warning',
    variant: 'filled',
    title: 'Unofficial Results',
    description: 'Reported election results are available, but they have not been certified and may change.',
    voteColumnPrefix: 'Unofficial',
  },
  partial_results: {
    label: 'Partial Results',
    color: 'warning',
    variant: 'filled',
    title: 'Partial Results',
    description: 'Some election results are available, but the comparison may be incomplete.',
    voteColumnPrefix: 'Result',
  },
  results_certified: {
    label: 'Certified Results',
    color: 'success',
    variant: 'filled',
    title: 'Certified Results',
    description: 'Final certified election results are available for this race.',
    voteColumnPrefix: 'Certified',
  },
};

/**
 * certification_status is authoritative when it reports partial or certified —
 * a race-level determination shouldn't be overridden by a single stray row.
 * Otherwise (pending/unrecognized), fall back to row-level result_type so real
 * reported results aren't hidden behind a stale "results_pending" status.
 */
export function resolveResultStatusKey(
  certificationStatus: string,
  hasUnofficialRows: boolean,
  hasOfficialRows: boolean,
): ResultStatusKey {
  if (certificationStatus === 'partial_results') {
    return 'partial_results';
  }

  if (certificationStatus === 'results_certified') {
    return 'results_certified';
  }

  if (hasUnofficialRows) {
    return 'unofficial';
  }

  if (hasOfficialRows) {
    return 'results_certified';
  }

  if (certificationStatus === 'upcoming') {
    return 'upcoming';
  }

  return 'results_pending';
}
