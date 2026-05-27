import type { Candidate, Election, MeasureOption, OfficialResultRow, OfficialResultsResponse, PaginatedResponse, Race } from '../types/api';
import type { CivicElection, CivicLookupResult, CivicOfficialResult, CivicRaceBase, CivicRaceDetail } from '../types/civicApi';

const PAGE_SIZE = 25;

export function civicElectionToLegacy(civicElection: CivicElection): Election {
  return {
    id: civicElection.id,
    name: civicElection.name,
    election_date: civicElection.election_date,
    jurisdiction_level: civicElection.jurisdiction_level,
    state: civicElection.state ?? undefined,
    status: civicElection.status,
  };
}

function civicRaceDetailToLegacy(race: CivicRaceDetail, election: CivicElection): Race {
  const candidates: Candidate[] = race.candidates.map((c) => ({
    id: c.id,
    name: c.name,
    party: c.party,
    incumbent: c.incumbent,
    candidate_status: c.candidate_status,
    description: c.description || undefined,
    image_url: c.image_url || undefined,
    website_url: c.website_url || undefined,
  }));

  const measureOptions: MeasureOption[] = race.measure_options.map((m) => ({
    id: m.id,
    option_label: m.option_label,
  }));

  return {
    id: race.id,
    election: civicElectionToLegacy(election),
    race_type: race.race_type,
    ballot_type: race.ballot_type,
    office_title: race.office_title,
    jurisdiction: race.jurisdiction,
    geography_scope: race.geography_scope,
    certification_status: race.certification_status,
    race_status: race.race_status,
    source: 'civic_api',
    vote_method: race.vote_method,
    max_selections: race.max_selections,
    candidates,
    measure_options: measureOptions,
    mock_vote_count: 0,
    // voting_opens/closes and viewer_* intentionally absent — supplied by voting API when available
  };
}

export { civicRaceDetailToLegacy };

/**
 * Converts a CivicRaceBase (list-view, no nested candidates) to the legacy Race shape.
 * Used for state/national scope where the /api/v1/races/ list endpoint is used directly.
 * Candidates and measure_options are empty — the detail page fetches them via getRaceDetail.
 */
export function civicRaceBaseToLegacy(race: CivicRaceBase, election: Election): Race {
  return {
    id: race.id,
    election,
    race_type: race.race_type,
    ballot_type: '',
    office_title: race.office_title,
    jurisdiction: race.jurisdiction,
    geography_scope: race.geography_scope,
    certification_status: race.certification_status,
    race_status: race.race_status,
    source: 'civic_api',
    vote_method: race.vote_method,
    candidates: [],
    measure_options: [],
    mock_vote_count: 0,
  };
}

function matchesContestType(race: Race, contestType: string | null | undefined): boolean {
  if (!contestType) return true;
  const RACE_TYPE_VALUES = new Set(['candidate', 'measure']);
  if (RACE_TYPE_VALUES.has(contestType)) return race.race_type === contestType;
  return race.ballot_type === contestType;
}

/**
 * Converts a `/api/v1/lookup/` response into the PaginatedResponse<Race> shape
 * that the existing RaceList/RaceCard components expect.
 *
 * Filtering by contestType and timeBounds (client-side date range) and
 * pagination are applied here because the lookup endpoint returns all active
 * races at once with no server-side filtering.
 */
export function lookupResultsToLegacyPaged(
  results: CivicLookupResult[],
  page: number,
  contestType?: string | null,
  timeBounds?: { election_date__gte?: string; election_date__lte?: string },
): PaginatedResponse<Race> {
  const allRaces: Race[] = results.flatMap(({ election, races }) => {
    if (timeBounds) {
      const d = election.election_date;
      if (timeBounds.election_date__gte && d < timeBounds.election_date__gte) return [];
      if (timeBounds.election_date__lte && d > timeBounds.election_date__lte) return [];
    }
    return races.map((race) => civicRaceDetailToLegacy(race, election));
  });

  const filtered = allRaces.filter((race) => matchesContestType(race, contestType));

  const start = (page - 1) * PAGE_SIZE;
  const pageRaces = filtered.slice(start, start + PAGE_SIZE);

  return {
    count: filtered.length,
    next: start + PAGE_SIZE < filtered.length ? 'next' : null,
    previous: page > 1 ? 'prev' : null,
    results: pageRaces,
  };
}

/**
 * Extracts the unique elections from a lookup response, sorted by date.
 * Used to populate the election selector dropdown on the homepage.
 */
export function electionsFromLookup(results: CivicLookupResult[]): Election[] {
  const seen = new Map<number, Election>();
  for (const { election } of results) {
    if (!seen.has(election.id)) {
      seen.set(election.id, civicElectionToLegacy(election));
    }
  }
  return [...seen.values()].sort((a, b) => a.election_date.localeCompare(b.election_date));
}

/**
 * Converts a CivicMirror-API results response into the OfficialResultsResponse
 * shape expected by OfficialResultsPanel. Candidate/measure-option PKs are
 * resolved to display names using the race detail object.
 */
export function civicResultsToLegacyResponse(
  results: CivicOfficialResult[],
  detail: CivicRaceDetail,
): OfficialResultsResponse {
  const candidateById = new Map(detail.candidates.map((c) => [c.id, c.name]));
  const measureOptionById = new Map(detail.measure_options.map((m) => [m.id, m.option_label]));

  const rows: OfficialResultRow[] = results.map((row) => ({
    id: row.id,
    candidate_name: row.candidate !== null ? (candidateById.get(row.candidate) ?? null) : null,
    option_label:
      row.measure_option !== null ? (measureOptionById.get(row.measure_option) ?? null) : null,
    vote_count: row.vote_count,
    vote_pct: row.vote_pct !== null ? parseFloat(row.vote_pct) : null,
    is_winner: row.is_winner,
    result_type: row.result_type,
    certified_at: row.certified_at,
    source_url: row.source_url,
    round_number: row.round_number,
    is_write_in_aggregate: row.is_write_in_aggregate,
    jurisdiction_fragment: row.jurisdiction_fragment,
  }));

  return {
    race_id: detail.id,
    certification_status: detail.certification_status,
    source_url: results[0]?.source_url ?? '',
    results: rows,
  };
}
