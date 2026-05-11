import type { MockTallyEntry, Race, TallyOption, TallyResponse } from '../types';
import { STATE_NAME_BY_CODE } from './usStates';

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});

const dateTimeFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
});

const compactNumberFormatter = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
});

export type DisplayStatusKey =
  | 'upcoming'
  | 'active'
  | 'results_pending'
  | 'results_certified'
  | 'partial_results'
  | 'pending_review'
  | 'cancelled'
  | 'archived';

const normalizePercentage = (value?: number): number | undefined => {
  if (value === undefined || Number.isNaN(value)) {
    return undefined;
  }

  return value <= 1 ? value * 100 : value;
};

export const formatDate = (value?: string | null) => {
  if (!value) {
    return 'TBD';
  }

  return dateFormatter.format(new Date(value));
};

export const formatDateTime = (value?: string | null) => {
  if (!value) {
    return 'TBD';
  }

  return dateTimeFormatter.format(new Date(value));
};

export const formatCompactNumber = (value: number) => compactNumberFormatter.format(value);

export const formatPercent = (value: number) => {
  const rounded = Math.round(value * 10) / 10;
  return Number.isInteger(rounded) ? `${rounded.toFixed(0)}%` : `${rounded.toFixed(1)}%`;
};

export const formatStateName = (code?: string | null) => {
  if (!code) {
    return '';
  }

  return STATE_NAME_BY_CODE[code.toUpperCase()] ?? code;
};

export const formatRaceSource = (source: Race['source']) =>
  source === 'civic_api' ? 'Civic API' : 'Community';

export const getRaceDisplayStatus = (
  race: Pick<Race, 'certification_status' | 'race_status' | 'voting_opens' | 'voting_closes'>,
): DisplayStatusKey => {
  if (race.race_status === 'cancelled') {
    return 'cancelled';
  }

  if (race.race_status === 'pending_review' || race.race_status === 'draft') {
    return 'pending_review';
  }

  if (race.certification_status === 'results_certified') {
    return 'results_certified';
  }

  if (race.certification_status === 'partial_results') {
    return 'partial_results';
  }

  if (race.race_status === 'archived') {
    return 'archived';
  }

  const now = Date.now();
  const opensAt = race.voting_opens ? new Date(race.voting_opens).getTime() : undefined;
  const closesAt = race.voting_closes ? new Date(race.voting_closes).getTime() : undefined;

  if (opensAt && now < opensAt) {
    return 'upcoming';
  }

  if (closesAt && now > closesAt) {
    return 'results_pending';
  }

  if (race.race_status === 'active' || race.certification_status === 'upcoming') {
    return 'active';
  }

  return race.certification_status === 'results_pending' ? 'results_pending' : 'upcoming';
};

export const buildRaceTallyEntries = (race: Race, limit?: number): MockTallyEntry[] => {
  const sourceEntries =
    race.mock_tally && race.mock_tally.length > 0
      ? race.mock_tally
      : race.race_type === 'candidate'
        ? (race.candidates ?? []).map((candidate) => ({
            id: candidate.id,
            label: candidate.name,
            party: candidate.party,
            votes: 0,
            percentage: 0,
          }))
        : (race.measure_options ?? []).map((option) => ({
            id: option.id,
            label: option.option_label,
            votes: 0,
            percentage: 0,
          }));

  const totalVotes = sourceEntries.reduce((sum, entry) => sum + (entry.votes ?? 0), 0);

  const normalized = sourceEntries
    .map((entry) => ({
      ...entry,
      percentage:
        normalizePercentage(entry.percentage) ??
        (totalVotes > 0 ? ((entry.votes ?? 0) / totalVotes) * 100 : 0),
    }))
    .sort((left, right) => (right.percentage ?? 0) - (left.percentage ?? 0));

  const withLeaders = normalized.map((entry, index) => ({
    ...entry,
    is_leading: entry.is_leading ?? index === 0,
  }));

  return limit ? withLeaders.slice(0, limit) : withLeaders;
};

export const buildTallyOptions = (
  entries: MockTallyEntry[],
  type: TallyOption['type'],
  limit?: number,
): TallyOption[] => {
  const limitedEntries = limit ? entries.slice(0, limit) : entries;

  return limitedEntries.map((entry, index) => ({
    id: typeof entry.id === 'number' ? entry.id : Number(entry.id) || index + 1,
    label: entry.label,
    type,
    count: entry.votes,
    percent: normalizePercentage(entry.percentage) ?? 0,
  }));
};

export const buildRaceTallyResponse = (race: Race, limit?: number): TallyResponse => {
  const entries = buildRaceTallyEntries(race, limit);
  const totalVotes = race.mock_vote_count || entries.reduce((sum, entry) => sum + entry.votes, 0);

  return {
    race_id: race.id,
    total_votes: totalVotes,
    options: buildTallyOptions(entries, race.race_type === 'candidate' ? 'candidate' : 'measure_option'),
    breakdowns: {},
  };
};
