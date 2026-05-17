import { useEffect, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useRaceFiltersStore } from '../store/raceFiltersStore';
import { formatStateName } from '../utils/format';
import { isStateCode } from '../utils/usStates';

const VALID_SCOPES = new Set(['national', 'state', 'zip', 'address']);

export const useRaceFilters = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useRaceFiltersStore();

  // Refs let us read the latest values inside effects without listing them as
  // reactive deps — this breaks the URL↔store feedback loop.
  const filtersRef = useRef(filters);
  filtersRef.current = filters;
  const searchParamsRef = useRef(searchParams);
  searchParamsRef.current = searchParams;
  const setSearchParamsRef = useRef(setSearchParams);
  setSearchParamsRef.current = setSearchParams;

  const isAutoDetected =
    filters.scope === 'national' &&
    !filters.state &&
    !filters.zip &&
    !filters.address &&
    Boolean(filters.detectedState);

  const resolvedScope = isAutoDetected ? 'state' : filters.scope;
  const effectiveState = resolvedScope === 'state' ? filters.state ?? filters.detectedState : null;

  // URL → Store: only re-runs when the URL changes, reads store via ref.
  // This prevents the store setter from immediately re-triggering this effect
  // and reverting a user action that hasn't been reflected in the URL yet.
  useEffect(() => {
    if (!searchParams.toString()) {
      return;
    }

    const f = filtersRef.current;
    const scopeParam = searchParams.get('scope');
    const stateParam = searchParams.get('state')?.toUpperCase() ?? null;
    const zipParam = searchParams.get('zip');
    const addressParam = searchParams.get('address');
    const contestTypeParam = searchParams.get('contestType');

    if (scopeParam && VALID_SCOPES.has(scopeParam) && scopeParam !== f.scope) {
      f.setScope(scopeParam as typeof f.scope);
    }

    if (stateParam && isStateCode(stateParam) && stateParam !== f.state) {
      f.setState(stateParam);
    }

    // Clear a location field when the URL no longer carries it for that scope.
    // Using scope !== 'state' (not === 'national') catches all scope switches,
    // e.g. state→zip still clears the stale state value from the store.
    if (!stateParam && f.state && scopeParam !== 'state') {
      f.setState(null);
    }

    if (zipParam && zipParam !== f.zip) {
      f.setZip(zipParam);
    }

    if (!zipParam && f.zip && scopeParam !== 'zip') {
      f.setZip(null);
    }

    if (addressParam && addressParam !== f.address) {
      f.setAddress(addressParam);
    }

    if (!addressParam && f.address && scopeParam !== 'address') {
      f.setAddress(null);
    }

    const rawElectionId = searchParams.get('electionId');
    // Guard against empty string ("") which Number() coerces to 0 — an invalid
    // Django AutoField PK — and against non-numeric strings which produce NaN.
    const parsed =
      rawElectionId !== null && rawElectionId !== '' ? Number(rawElectionId) : null;
    const nextElectionId = parsed !== null && Number.isFinite(parsed) && parsed > 0 ? parsed : null;
    if (nextElectionId !== f.electionId) {
      f.setElectionId(nextElectionId);
    }

    if (contestTypeParam !== f.contestType) {
      f.setContestType(contestTypeParam);
    }
  }, [searchParams]); // only URL changes drive URL→Store sync

  // Store → URL: only re-runs when store fields change, reads URL via ref.
  // Removing searchParams and setSearchParams from deps prevents URL changes
  // (including the ones this effect causes) from re-triggering it.
  useEffect(() => {
    const next = new URLSearchParams();

    if (filters.scope !== 'national') {
      next.set('scope', filters.scope);
    }

    if (filters.scope === 'state' && filters.state) {
      next.set('state', filters.state);
    }

    if (filters.scope === 'zip' && filters.zip) {
      next.set('zip', filters.zip);
    }

    if (filters.scope === 'address' && filters.address) {
      next.set('address', filters.address);
    }

    if (filters.electionId != null) {
      next.set('electionId', String(filters.electionId));
    }

    if (filters.contestType != null) {
      next.set('contestType', filters.contestType);
    }

    if (next.toString() !== searchParamsRef.current.toString()) {
      setSearchParamsRef.current(next, { replace: true });
    }
  }, [filters.address, filters.contestType, filters.electionId, filters.scope, filters.state, filters.zip]); // only store changes drive Store→URL sync

  const activeLocationLabel = useMemo(() => {
    if (resolvedScope === 'state' && effectiveState) {
      return formatStateName(effectiveState);
    }

    if (resolvedScope === 'zip') {
      return filters.zip;
    }

    if (resolvedScope === 'address') {
      return filters.address;
    }

    return null;
  }, [effectiveState, filters.address, filters.zip, resolvedScope]);

  return {
    ...filters,
    resolvedScope,
    effectiveState,
    isAutoDetected,
    activeLocationLabel,
  };
};
