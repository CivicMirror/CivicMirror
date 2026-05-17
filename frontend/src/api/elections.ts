import type {
  Candidate,
  MeasureOption,
  MockTallyEntry,
  OfficialResultRow,
  OfficialResultsResponse,
  PaginatedResponse,
  Race,
  RaceListParams,
} from '../types';
import { apiClient } from './client';

interface RawRace extends Omit<Race, 'candidates' | 'measure_options' | 'mock_tally'> {
  candidates?: Candidate[];
  candidate_set?: Candidate[];
  measure_options?: MeasureOption[];
  measureoption_set?: MeasureOption[];
  mock_tally?: MockTallyEntry[];
  tally?: MockTallyEntry[];
  mock_results?: MockTallyEntry[];
}

interface RawOfficialResultRow extends Omit<OfficialResultRow, 'option_label' | 'round_number' | 'is_write_in_aggregate' | 'jurisdiction_fragment'> {
  option_label?: string | null;
  measure_option_label?: string | null;
  round_number?: number | null;
  is_write_in_aggregate?: boolean;
  jurisdiction_fragment?: string;
}

interface RawOfficialResultsResponse extends Omit<OfficialResultsResponse, 'results' | 'source_url'> {
  source_url?: string;
  results: RawOfficialResultRow[];
}

const normalizeRace = (race: RawRace): Race => ({
  ...race,
  candidates: race.candidates ?? race.candidate_set,
  measure_options: race.measure_options ?? race.measureoption_set,
  mock_tally: race.mock_tally ?? race.tally ?? race.mock_results,
});

const mapQueryParams = (params: RaceListParams = {}) => {
  const { contestType } = params;

  // "candidate" / "measure" map to the race_type filter.
  // Known election sub-types (General, Primary, Run-off, Retention) map to ballot_type.
  const RACE_TYPE_VALUES = new Set(['candidate', 'measure']);
  const raceType = contestType && RACE_TYPE_VALUES.has(contestType) ? contestType : undefined;
  const ballotType =
    contestType && !RACE_TYPE_VALUES.has(contestType) ? contestType : undefined;

  return {
    scope: params.scope,
    state: params.state ?? undefined,
    zip: params.zip ?? undefined,
    address: params.address ?? undefined,
    election_id: params.electionId ?? undefined,
    certification_status: params.certificationStatus ?? undefined,
    race_type: raceType,
    ballot_type: ballotType,
    page: params.page ?? undefined,
  };
};

export const raceApi = {
  async list(params: RaceListParams = {}) {
    const response = await apiClient.get<PaginatedResponse<RawRace>>('/api/races/', {
      params: mapQueryParams(params),
    });

    return {
      ...response.data,
      results: response.data.results.map(normalizeRace),
    };
  },
  async detail(id: number) {
    const response = await apiClient.get<RawRace>(`/api/races/${id}/`);
    return normalizeRace(response.data);
  },
  resolveByZip(zip: string, electionId?: number | null) {
    return this.list({ scope: 'zip', zip, electionId: electionId ?? null });
  },
  resolveByAddress(address: string, electionId?: number | null) {
    return this.list({ scope: 'address', address, electionId: electionId ?? null });
  },
};

export async function getRaceOfficialResults(raceId: number): Promise<OfficialResultsResponse> {
  const { data } = await apiClient.get<RawOfficialResultsResponse>(`/api/races/${raceId}/official-results/`);

  return {
    ...data,
    source_url: data.source_url ?? data.results[0]?.source_url ?? '',
    results: data.results.map((row) => ({
      ...row,
      option_label: row.option_label ?? row.measure_option_label ?? null,
      round_number: row.round_number ?? null,
      is_write_in_aggregate: row.is_write_in_aggregate ?? false,
      jurisdiction_fragment: row.jurisdiction_fragment ?? '',
    })),
  };
}
