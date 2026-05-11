import axios from 'axios';
import type { CommunityRacePayload, ConflictRace, ConflictResponse } from '../types';
import { apiClient } from './client';

const normalizeConflictRace = (race: Record<string, unknown>): ConflictRace => ({
  id: Number(race.id ?? 0),
  office_title:
    typeof race.office_title === 'string'
      ? race.office_title
      : typeof race.question_title === 'string'
        ? race.question_title
        : 'Existing race',
  jurisdiction: typeof race.jurisdiction === 'string' ? race.jurisdiction : 'Unknown jurisdiction',
  election_date: typeof race.election_date === 'string' ? race.election_date : undefined,
  election_name: typeof race.election_name === 'string' ? race.election_name : undefined,
  location_name: typeof race.location_name === 'string' ? race.location_name : undefined,
});

const normalizeConflictResponse = (data: Record<string, unknown>): ConflictResponse => ({
  conflict: true,
  detail:
    typeof data.detail === 'string'
      ? data.detail
      : 'Similar races were found. Please review before submitting.',
  conflicts: (Array.isArray(data.conflicts)
    ? data.conflicts
    : Array.isArray(data.similar_races)
      ? data.similar_races
      : Array.isArray(data.matches)
        ? data.matches
        : []
  )
    .filter((entry): entry is Record<string, unknown> => typeof entry === 'object' && entry !== null)
    .map(normalizeConflictRace),
});

const isConflictPayload = (data: unknown): data is Record<string, unknown> => {
  if (!data || typeof data !== 'object') {
    return false;
  }

  return 'conflict' in data || 'conflicts' in data || 'similar_races' in data || 'matches' in data;
};

export const communityRaceApi = {
  async submitCommunityRace(payload: CommunityRacePayload & { force_submit?: boolean }) {
    try {
      const response = await apiClient.post<{ id: number } | ConflictResponse>('/api/races/local/', payload);
      return isConflictPayload(response.data) ? normalizeConflictResponse(response.data) : response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && isConflictPayload(error.response?.data)) {
        return normalizeConflictResponse(error.response.data);
      }

      throw error;
    }
  },
};
