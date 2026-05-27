import { create } from 'zustand';
import type { TimeFilter } from '../utils/timeFilter';

export type { TimeFilter };
export type RaceFilterScope = 'national' | 'state' | 'zip' | 'address';

export interface RaceFiltersState {
  scope: RaceFilterScope;
  state: string | null;
  zip: string | null;
  address: string | null;
  electionId: number | null;
  detectedState: string | null;
  contestType: string | null;
  timeFilter: TimeFilter;
  setScope: (scope: RaceFilterScope) => void;
  setState: (state: string | null) => void;
  setZip: (zip: string | null) => void;
  setAddress: (address: string | null) => void;
  setElectionId: (id: number | null) => void;
  setDetectedState: (state: string | null) => void;
  setContestType: (type: string | null) => void;
  setTimeFilter: (filter: TimeFilter) => void;
  clearLocationPreference: () => void;
}

export const LOCATION_STORAGE_KEY = 'civicmirror_location';

interface PersistedLocationPreference {
  scope: RaceFilterScope;
  state: string | null;
  zip: string | null;
  address: string | null;
  electionId: number | null;
  contestType: string | null;
  timeFilter: TimeFilter;
}

const defaultState: PersistedLocationPreference = {
  scope: 'national',
  state: null,
  zip: null,
  address: null,
  electionId: null,
  contestType: null,
  timeFilter: 'month',
};

const readPersistedLocation = (): PersistedLocationPreference => {
  if (typeof window === 'undefined') {
    return defaultState;
  }

  const stored = window.localStorage.getItem(LOCATION_STORAGE_KEY);
  if (!stored) {
    return defaultState;
  }

  try {
    const parsed = JSON.parse(stored) as Partial<PersistedLocationPreference>;
    // Always drop any previously-stored address — it is PII and we no longer
    // write it, but old localStorage entries may still contain it.
    return { ...defaultState, ...parsed, address: null };
  } catch {
    return defaultState;
  }
};

const persistLocation = (state: PersistedLocationPreference) => {
  if (typeof window === 'undefined') {
    return;
  }

  // Never persist the street address — it is PII. Persist the scope so the
  // Address tab remains selected on reload, but the user re-enters the value.
  window.localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify({ ...state, address: null }));
};

const persisted = readPersistedLocation();

export const useRaceFiltersStore = create<RaceFiltersState>((set) => ({
  ...persisted,
  detectedState: null,
  setScope(scope) {
    set((current) => {
      const next = { ...current, scope };
      persistLocation({
        scope: next.scope,
        state: next.state,
        zip: next.zip,
        address: next.address,
        electionId: next.electionId,
        contestType: next.contestType,
        timeFilter: next.timeFilter,
      });
      return { scope };
    });
  },
  setState(state) {
    set((current) => {
      const next: PersistedLocationPreference = {
        scope: state ? 'state' : 'national',
        state,
        zip: null,
        address: null,
        electionId: current.electionId,
        contestType: current.contestType,
        timeFilter: current.timeFilter,
      };
      persistLocation(next);
      return { ...next };
    });
  },
  setZip(zip) {
    set((current) => {
      const next: PersistedLocationPreference = {
        scope: zip ? 'zip' : 'national',
        state: null,
        zip,
        address: null,
        electionId: current.electionId,
        contestType: current.contestType,
        timeFilter: current.timeFilter,
      };
      persistLocation(next);
      return { ...next };
    });
  },
  setAddress(address) {
    set((current) => {
      const next: PersistedLocationPreference = {
        scope: address ? 'address' : 'national',
        state: null,
        zip: null,
        address,
        electionId: current.electionId,
        contestType: current.contestType,
        timeFilter: current.timeFilter,
      };
      persistLocation(next);
      return { ...next };
    });
  },
  setElectionId(id) {
    set((current) => {
      const next: PersistedLocationPreference = {
        scope: current.scope,
        state: current.state,
        zip: current.zip,
        address: current.address,
        electionId: id,
        contestType: current.contestType,
        timeFilter: current.timeFilter,
      };
      persistLocation(next);
      return { electionId: id };
    });
  },
  setContestType(contestType) {
    set((current) => {
      const next: PersistedLocationPreference = {
        scope: current.scope,
        state: current.state,
        zip: current.zip,
        address: current.address,
        electionId: current.electionId,
        contestType,
        timeFilter: current.timeFilter,
      };
      persistLocation(next);
      return { contestType };
    });
  },
  setTimeFilter(timeFilter) {
    set((current) => {
      const next: PersistedLocationPreference = {
        scope: current.scope,
        state: current.state,
        zip: current.zip,
        address: current.address,
        // Clear any selected election — it may not belong to the new time window.
        electionId: null,
        contestType: current.contestType,
        timeFilter,
      };
      persistLocation(next);
      return { timeFilter, electionId: null };
    });
  },
  setDetectedState(state) {
    set({ detectedState: state });
  },
  clearLocationPreference() {
    set((current) => {
      const next: PersistedLocationPreference = {
        ...defaultState,
        electionId: current.electionId,
      };
      persistLocation(next);
      return {
        scope: 'national',
        state: null,
        zip: null,
        address: null,
        detectedState: null,
      };
    });
  },
}));
