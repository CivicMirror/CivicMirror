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

export interface VoteChoice {
  type: 'candidate' | 'measure_option' | string;
  id: number;
  label: string;
}

export interface Candidate {
  id: number;
  name: string;
  party: string;
  incumbent: boolean;
  candidate_status: 'running' | 'withdrawn' | 'disqualified' | 'write_in' | string;
  description?: string;
  image_url?: string;
  website_url?: string;
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

export interface TallyOption {
  id: number;
  label: string;
  type: 'candidate' | 'measure_option';
  count: number;
  percent: number;
}

export interface TallyResponse {
  race_id: number;
  total_votes: number;
  options: TallyOption[];
  breakdowns: Record<string, Record<string, number>>;
}

export interface OfficialResultRow {
  id: number;
  candidate_name: string | null;
  option_label: string | null;
  vote_count: number;
  vote_pct: number | null;
  is_winner: boolean | null;
  result_type: 'official' | 'unofficial';
  certified_at: string | null;
  source_url: string;
  round_number: number | null;
  is_write_in_aggregate: boolean;
  jurisdiction_fragment: string;
}

export interface OfficialResultsResponse {
  race_id: number;
  certification_status: 'upcoming' | 'results_pending' | 'results_certified' | 'partial_results';
  source_url: string;
  results: OfficialResultRow[];
}

export interface Race {
  id: number;
  election: Election;
  race_type: 'candidate' | 'measure';
  ballot_type: string;
  office_title: string;
  jurisdiction: string;
  geography_scope: string;
  certification_status: 'upcoming' | 'results_pending' | 'results_certified' | 'partial_results';
  race_status: 'draft' | 'pending_review' | 'active' | 'cancelled' | 'archived';
  source: 'civic_api' | 'community';
  vote_method?: 'single_choice' | 'multi_seat' | 'ranked_choice' | 'yes_no' | string;
  max_selections?: number;
  candidates?: Candidate[];
  measure_options?: MeasureOption[];
  mock_tally?: MockTallyEntry[];
  mock_vote_count: number;
  voting_opens?: string;
  voting_closes?: string;
  viewer_has_voted?: boolean;
  viewer_choice?: VoteChoice;
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
  contestType?: string | null;
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

export interface VoteResponse {
  id: number;
  race_id: number;
  cast_at: string;
  choice: VoteChoice;
}

export interface MyVote {
  id: number;
  race_id: number;
  election_name: string;
  office_title: string;
  jurisdiction: string;
  cast_at: string;
  choice: VoteChoice;
  race_status: string;
}

export type VoteErrorCode =
  | 'not_authenticated'
  | 'race_inactive'
  | 'voting_closed'
  | 'invalid_option'
  | 'already_voted';

export interface VoteErrorResponse {
  code: VoteErrorCode;
  detail: string;
}

export interface CommunityRaceCandidateInput {
  name: string;
  party?: string;
  description?: string;
  image_url?: string;
  website_url?: string;
  candidate_type: 'running' | 'write_in';
}

export interface CommunityCandidateRacePayload {
  race_type: 'candidate';
  office_title: string;
  jurisdiction: 'city' | 'town' | 'county' | 'district';
  election_date: string;
  location_name: string;
  candidates: CommunityRaceCandidateInput[];
}

export interface CommunityMeasureRacePayload {
  race_type: 'measure';
  ballot_type: 'Citizen-Initiated' | 'Town-Initiated';
  question_title: string;
  election_date: string;
  location_name: string;
  yes_vote_details: string;
  no_vote_details: string;
  source_links: string[];
}

export type CommunityRacePayload = CommunityCandidateRacePayload | CommunityMeasureRacePayload;

export interface ConflictRace {
  id: number;
  office_title: string;
  jurisdiction: string;
  election_date?: string;
  election_name?: string;
  location_name?: string;
}

export interface ConflictResponse {
  conflict: true;
  detail?: string;
  conflicts: ConflictRace[];
}
