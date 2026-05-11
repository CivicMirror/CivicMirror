import type { PaginatedResponse, VotePayload } from '../types';
import { apiClient } from './client';

export interface UserVote {
  id: number;
  race_id: number;
  candidate_id?: number;
  measure_option_id?: number;
  cast_at: string;
}

export const voteApi = {
  async castVote(raceId: number, payload: VotePayload) {
    const response = await apiClient.post(`/api/races/${raceId}/votes/`, payload);
    return response.data;
  },
  async getMyVotes() {
    const response = await apiClient.get<PaginatedResponse<UserVote>>('/api/votes/me/');
    return response.data;
  },
};
