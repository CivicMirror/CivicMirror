import type { MyVote, Race, TallyOption, TallyResponse, VotePayload, VoteResponse } from '../types';
import { buildRaceTallyEntries } from '../utils/format';
import { raceApi } from './elections';
import { apiClient } from './client';

const toTallyOption = (
  entry: { id: number | string; label: string; votes: number; percentage?: number },
  index: number,
  type: TallyOption['type'],
): TallyOption => ({
  id: typeof entry.id === 'number' ? entry.id : Number(entry.id) || index + 1,
  label: entry.label,
  type,
  count: entry.votes,
  percent: entry.percentage ?? 0,
});

const buildFallbackTally = (race: Race): TallyResponse => {
  const entries = buildRaceTallyEntries(race);
  const totalVotes = race.mock_vote_count || entries.reduce((sum, entry) => sum + entry.votes, 0);

  return {
    race_id: race.id,
    total_votes: totalVotes,
    options: entries.map((entry, index) =>
      toTallyOption(entry, index, race.race_type === 'candidate' ? 'candidate' : 'measure_option'),
    ),
    breakdowns: {},
  };
};

export const votingApi = {
  async postVote(raceId: number, payload: VotePayload) {
    const response = await apiClient.post<VoteResponse>(`/api/races/${raceId}/vote/`, payload);
    return response.data;
  },
  async getRaceTally(raceId: number) {
    try {
      const response = await apiClient.get<TallyResponse>(`/api/races/${raceId}/tally/`);
      return response.data;
    } catch {
      const race = await raceApi.detail(raceId);
      return buildFallbackTally(race);
    }
  },
  async getMyVotes() {
    const response = await apiClient.get<MyVote[]>('/api/users/me/votes/');
    return response.data;
  },
};
