// Types for the CivicMirror-API (civicmirror-worker service).
// All shapes match the API-Reference and Data-Models in /Shared.

export interface CivicElectionCycle {
  id: number;
  cycle_year: number;
  description: string;
  cycle_start: string;
  cycle_end: string;
}

export interface CivicElection {
  id: number;
  source_id: string;
  name: string;
  election_date: string;
  jurisdiction_level: 'national' | 'state' | 'local';
  state: string | null;
  status: 'upcoming' | 'active' | 'results_pending' | 'results_certified' | 'archived';
  last_synced_at: string | null;
  election_cycle: CivicElectionCycle | null;
  race_count: number;
}

export interface CivicCandidate {
  id: number;
  race: number;
  name: string;
  party: string;
  incumbent: boolean;
  candidate_status: 'running' | 'withdrawn' | 'disqualified' | 'write_in';
  description: string;
  image_url: string;
  website_url: string;
  fec_candidate_id: string;
  bioguide_id: string;
  openstates_person_id: string;
  contact_phone: string;
  contact_office: string;
}

export interface CivicMeasureOption {
  id: number;
  option_label: string;
  race: number;
}

export type CivicRaceType = 'candidate' | 'measure';
export type CivicVoteMethod = 'single_choice' | 'multi_seat' | 'ranked_choice' | 'yes_no';
export type CivicCertificationStatus =
  | 'upcoming'
  | 'results_pending'
  | 'partial_results'
  | 'results_certified';
export type CivicRaceStatus = 'draft' | 'pending_review' | 'active' | 'cancelled' | 'archived';
export type CivicMatchConfidence = 'verified' | 'high' | 'medium' | 'low' | 'flagged';

export interface CivicRaceBase {
  id: number;
  election: number;
  race_type: CivicRaceType;
  office_title: string;
  jurisdiction: string;
  geography_scope: string;
  certification_status: CivicCertificationStatus;
  race_status: CivicRaceStatus;
  vote_method: CivicVoteMethod;
  ocd_division_id: string;
  last_synced_at: string | null;
}

export interface CivicRaceDetail extends CivicRaceBase {
  max_selections: number;
  ballot_type: string;
  normalized_office_title: string;
  yes_vote_details: string;
  no_vote_details: string;
  match_confidence: CivicMatchConfidence;
  candidates: CivicCandidate[];
  measure_options: CivicMeasureOption[];
}

export interface CivicOfficialResult {
  id: number;
  race: number;
  candidate: number | null;
  measure_option: number | null;
  vote_count: number;
  vote_pct: string | null;
  result_type: 'unofficial' | 'official';
  is_winner: boolean | null;
  round_number: number | null;
  jurisdiction_fragment: string;
  is_write_in_aggregate: boolean;
  certified_at: string | null;
  source_url: string;
}

export interface CivicDistrictRecord {
  id: number;
  state: string;
  district_type: string;
  district_number: string;
  ocd_division_id: string;
  name: string;
  fips_code: string;
  election_year_valid: number | null;
  approximate: boolean;
  last_updated: string;
}

export interface CivicPaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CivicLookupResult {
  election: CivicElection;
  races: CivicRaceDetail[];
}
