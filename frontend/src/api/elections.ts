import type {
  Candidate,
  MeasureOption,
  MockTallyEntry,
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

const normalizeRace = (race: RawRace): Race => ({
  ...race,
  candidates: race.candidates ?? race.candidate_set,
  measure_options: race.measure_options ?? race.measureoption_set,
  mock_tally: race.mock_tally ?? race.tally ?? race.mock_results,
});

const mapQueryParams = (params: RaceListParams = {}) => ({
  scope: params.scope,
  state: params.state ?? undefined,
  zip: params.zip ?? undefined,
  address: params.address ?? undefined,
  election_id: params.electionId ?? undefined,
  certification_status: params.certificationStatus ?? undefined,
  page: params.page ?? undefined,
});

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
