import { useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useRaceFiltersStore } from '../store/raceFiltersStore';
import { formatStateName } from '../utils/format';
import { isStateCode } from '../utils/usStates';

const VALID_SCOPES = new Set(['national', 'state', 'zip', 'address']);

export const useRaceFilters = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useRaceFiltersStore();

  const isAutoDetected =
    filters.scope === 'national' &&
    !filters.state &&
    !filters.zip &&
    !filters.address &&
    Boolean(filters.detectedState);

  const resolvedScope = isAutoDetected ? 'state' : filters.scope;
  const effectiveState = resolvedScope === 'state' ? filters.state ?? filters.detectedState : null;

  useEffect(() => {
    if (!searchParams.toString()) {
      return;
    }

    const scopeParam = searchParams.get('scope');
    const stateParam = searchParams.get('state')?.toUpperCase() ?? null;
    const zipParam = searchParams.get('zip');
    const addressParam = searchParams.get('address');
    const electionIdParam = searchParams.get('electionId');

    if (scopeParam && VALID_SCOPES.has(scopeParam) && scopeParam !== filters.scope) {
      filters.setScope(scopeParam as typeof filters.scope);
    }

    if (stateParam && isStateCode(stateParam) && stateParam !== filters.state) {
      filters.setState(stateParam);
    }

    if (!stateParam && filters.state && scopeParam === 'national') {
      filters.setState(null);
    }

    if (zipParam && zipParam !== filters.zip) {
      filters.setZip(zipParam);
    }

    if (!zipParam && filters.zip && scopeParam === 'national') {
      filters.setZip(null);
    }

    if (addressParam && addressParam !== filters.address) {
      filters.setAddress(addressParam);
    }

    if (!addressParam && filters.address && scopeParam === 'national') {
      filters.setAddress(null);
    }

    const parsedElectionId = electionIdParam ? Number(electionIdParam) : null;
    if (parsedElectionId !== filters.electionId) {
      filters.setElectionId(Number.isFinite(parsedElectionId) ? parsedElectionId : null);
    }
  }, [filters, searchParams]);

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

    if (filters.electionId) {
      next.set('electionId', String(filters.electionId));
    }

    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [filters.address, filters.electionId, filters.scope, filters.state, filters.zip, searchParams, setSearchParams]);

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
