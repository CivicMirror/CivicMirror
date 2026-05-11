import { create } from 'zustand';

export type RaceFilterScope = 'national' | 'state' | 'zip' | 'address';

export interface RaceFiltersState {
  scope: RaceFilterScope;
  state: string | null;
  zip: string | null;
  address: string | null;
  electionId: number | null;
  detectedState: string | null;
  setScope: (scope: RaceFilterScope) => void;
  setState: (state: string | null) => void;
  setZip: (zip: string | null) => void;
  setAddress: (address: string | null) => void;
  setElectionId: (id: number | null) => void;
  setDetectedState: (state: string | null) => void;
  clearLocationPreference: () => void;
}

export const LOCATION_STORAGE_KEY = 'civicmirror_location';

interface PersistedLocationPreference {
  scope: RaceFilterScope;
  state: string | null;
  zip: string | null;
  address: string | null;
  electionId: number | null;
}

const defaultState: PersistedLocationPreference = {
  scope: 'national',
  state: null,
  zip: null,
  address: null,
  electionId: null,
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
    return { ...defaultState, ...(JSON.parse(stored) as Partial<PersistedLocationPreference>) };
  } catch {
    return defaultState;
  }
};

const persistLocation = (state: PersistedLocationPreference) => {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(state));
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
      };
      persistLocation(next);
      return { electionId: id };
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
