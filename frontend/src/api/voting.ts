import type { MyVote, TallyResponse, VotePayload, VoteResponse } from '../types';
import { apiClient } from './client';export const votingApi = {
  async postVote(raceId: number, payload: VotePayload) {
    const response = await apiClient.post<VoteResponse>(`/api/races/${raceId}/vote/`, payload);
    return response.data;
  },
  async getRaceTally(raceId: number): Promise<TallyResponse | null> {
    try {
      const response = await apiClient.get<TallyResponse>(`/api/races/${raceId}/tally/`);
      return response.data;
    } catch {
      return null;
    }
  },
  async getMyVotes() {
    const response = await apiClient.get<MyVote[]>('/api/users/votes/');
    return response.data;
  },
};
