export interface User {
  id: number;
  email: string;
  username: string;
}

export interface UserProfile {
  id: number;
  username: string;
  age_range?: string;
  country?: string;
  us_state?: string;
  gender?: string;
  saved_zipcode?: string;
  created_at: string;
}

export interface Election {
  id: number;
  name: string;
  election_date: string;
  jurisdiction_level: 'national' | 'state' | 'local';
  state?: string;
  status: string;
}

export interface Candidate {
  id: number;
  name: string;
  party: string;
  incumbent: boolean;
  candidate_status: string;
}

export interface MeasureOption {
  id: number;
  option_label: string;
}

export interface MockTallyEntry {
  id: number | string;
  label: string;
  party?: string;
  votes: number;
  percentage?: number;
  is_leading?: boolean;
}

export interface Race {
  id: number;
  election: Election;
  race_type: 'candidate' | 'measure';
  office_title: string;
  jurisdiction: string;
  geography_scope: string;
  certification_status: string;
  race_status: string;
  source: 'civic_api' | 'community';
  candidates?: Candidate[];
  measure_options?: MeasureOption[];
  mock_tally?: MockTallyEntry[];
  mock_vote_count: number;
  voting_opens?: string;
  voting_closes?: string;
  viewer_has_voted?: boolean;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username?: string;
  password: string;
  age_range?: string;
  country?: string;
  us_state?: string;
  gender?: string;
  terms_version: string;
  terms_accepted: true;
}

export interface AuthResponse {
  token: string;
  user: User;
  profile: UserProfile;
}

export interface RaceListParams {
  scope?: 'national' | 'state' | 'zip' | 'address';
  state?: string | null;
  zip?: string | null;
  address?: string | null;
  electionId?: number | null;
  certificationStatus?: string | null;
  page?: number;
}

export interface ProfileUpdatePayload {
  age_range?: string;
  country?: string;
  us_state?: string;
  gender?: string;
}

export interface VotePayload {
  candidate_id?: number;
  measure_option_id?: number;
}
