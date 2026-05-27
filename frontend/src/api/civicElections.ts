import { civicApiClient } from './civicApiClient';
import type {
  CivicElection,
  CivicLookupResult,
  CivicOfficialResult,
  CivicPaginatedResponse,
  CivicRaceBase,
  CivicRaceDetail,
} from '../types/civicApi';

export const civicElectionsApi = {
  async lookup(zip: string, electionId?: number): Promise<CivicLookupResult[]> {
    const params: Record<string, string> = { zip };
    if (electionId) params.election_id = String(electionId);
    return civicApiClient.fetch<CivicLookupResult[]>('/api/v1/lookup/', params);
  },

  async listElections(params: {
    state?: string;
    status?: string;
    jurisdiction_level?: 'national' | 'state' | 'local';
    election_date__gte?: string;
    election_date__lte?: string;
    page?: number;
  } = {}): Promise<CivicPaginatedResponse<CivicElection>> {
    const query: Record<string, string> = {};
    if (params.state) query.state = params.state;
    if (params.status) query.status = params.status;
    if (params.jurisdiction_level) query.jurisdiction_level = params.jurisdiction_level;
    if (params.election_date__gte) query.election_date__gte = params.election_date__gte;
    if (params.election_date__lte) query.election_date__lte = params.election_date__lte;
    if (params.page) query.page = String(params.page);
    return civicApiClient.fetch<CivicPaginatedResponse<CivicElection>>('/api/v1/elections/', query);
  },

  async getElection(id: number): Promise<CivicElection> {
    return civicApiClient.fetch<CivicElection>(`/api/v1/elections/${id}/`);
  },

  async listRaces(params: {
    state?: string;
    race_status?: string;
    race_type?: string;
    election?: number;
    geography_scope?: string;
    jurisdiction_level?: 'national' | 'state' | 'local';
    page?: number;
  } = {}): Promise<CivicPaginatedResponse<CivicRaceBase>> {
    const query: Record<string, string> = {};
    if (params.state) query.state = params.state;
    if (params.race_status) query.race_status = params.race_status;
    if (params.race_type) query.race_type = params.race_type;
    if (params.election) query.election = String(params.election);
    if (params.geography_scope) query.geography_scope = params.geography_scope;
    if (params.jurisdiction_level) query.jurisdiction_level = params.jurisdiction_level;
    if (params.page) query.page = String(params.page);
    return civicApiClient.fetch<CivicPaginatedResponse<CivicRaceBase>>('/api/v1/races/', query);
  },

  async getRaceDetail(id: number): Promise<CivicRaceDetail> {
    return civicApiClient.fetch<CivicRaceDetail>(`/api/v1/races/${id}/`);
  },

  async getRaceResults(id: number): Promise<CivicOfficialResult[]> {
    return civicApiClient.fetch<CivicOfficialResult[]>(`/api/v1/races/${id}/results/`);
  },
};
