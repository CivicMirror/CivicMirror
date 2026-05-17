import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { raceApi } from '../api/elections';
import { getApiErrorMessage } from '../api/client';
import ErrorMessage from '../components/common/ErrorMessage';
import LocationBar from '../components/races/LocationBar';
import RaceList from '../components/races/RaceList';
import { useIPGeolocation } from '../hooks/useIPGeolocation';
import { useRaceFilters } from '../hooks/useRaceFilters';
import { useRaceFiltersStore } from '../store/raceFiltersStore';
import type { Election, PaginatedResponse, Race } from '../types';
import { formatStateName } from '../utils/format';

function HomePage() {
  useIPGeolocation();

  const {
    activeLocationLabel,
    address,
    effectiveState,
    electionId,
    isAutoDetected,
    resolvedScope,
    zip,
  } = useRaceFilters();

  const setElectionId = useRaceFiltersStore((state) => state.setElectionId);
  const contestType = useRaceFiltersStore((state) => state.contestType);

  const [page, setPage] = useState(1);
  const [requestKey, setRequestKey] = useState(0);
  const [data, setData] = useState<PaginatedResponse<Race> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPage(1);
  }, [address, contestType, effectiveState, electionId, resolvedScope, zip]);

  const hasIncompleteLocation =
    (resolvedScope === 'state' && !effectiveState) ||
    (resolvedScope === 'zip' && !zip) ||
    (resolvedScope === 'address' && !address);

  useEffect(() => {
    if (hasIncompleteLocation) {
      setLoading(false);
      setData(null);
      return;
    }

    let isActive = true;
    setLoading(true);
    setError(null);

    void raceApi
      .list({
        scope: resolvedScope,
        state: resolvedScope === 'state' ? effectiveState : null,
        zip: resolvedScope === 'zip' ? zip : null,
        address: resolvedScope === 'address' ? address : null,
        electionId,
        contestType,
        page,
      })
      .then((response) => {
        if (isActive) {
          setData(response);
        }
      })
      .catch((requestError) => {
        if (isActive) {
          setError(getApiErrorMessage(requestError, 'We could not load races right now.'));
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [address, contestType, effectiveState, electionId, hasIncompleteLocation, page, requestKey, resolvedScope, zip]);

  const elections = useMemo(() => {
    const byId = new Map<number, Election>();
    data?.results.forEach((race) => {
      byId.set(race.election.id, race.election);
    });
    return [...byId.values()].sort((left, right) =>
      left.election_date.localeCompare(right.election_date),
    );
  }, [data]);

  const heading = useMemo(() => {
    if (resolvedScope === 'state' && effectiveState) {
      return `Races in ${formatStateName(effectiveState)}`;
    }

    if (resolvedScope === 'zip' && zip) {
      return `Races near ZIP ${zip}`;
    }

    if (resolvedScope === 'address' && address) {
      return 'Races for your address';
    }

    return 'National active races';
  }, [address, effectiveState, resolvedScope, zip]);

  const subheading = useMemo(() => {
    if (isAutoDetected && activeLocationLabel) {
      return `Auto-detected from your IP address. You can change or clear ${activeLocationLabel} anytime.`;
    }

    if (resolvedScope === 'zip') {
      return 'ZIP lookups combine statewide and approximate local coverage.';
    }

    if (resolvedScope === 'address') {
      return 'Address searches can reveal the most precise local ballot for this election.';
    }

    return 'Browse mock participation without logging in, then narrow the feed with an optional location.';
  }, [activeLocationLabel, isAutoDetected, resolvedScope]);

  return (
    <Stack spacing={4}>
      <Card>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={2.5}>

            <Box>
              <Typography gutterBottom variant="h1" sx={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.25rem)' }}>
                See how your community would vote.
              </Typography>
              <Typography color="text.secondary" maxWidth={760} variant="h6">
                CivicMirror lets anyone browse real election contests, follow mock participation, and
                progressively narrow the feed from national races down to the ballot near them.
              </Typography>
            </Box>
            <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5}>
              <Button component="a" href="#civicmirror-location-bar" variant="contained">
                Enter ZIP or address
              </Button>
              <Button color="primary" component={RouterLink} to="/register" variant="outlined">
                Register to save your profile
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <LocationBar
        activeLocationLabel={activeLocationLabel}
        address={address}
        effectiveState={effectiveState}
        isAutoDetected={isAutoDetected}
        resolvedScope={resolvedScope}
        zip={zip}
      />

      <Stack direction={{ xs: 'column', lg: 'row' }} gap={2} justifyContent="space-between">
        <Box>
          <Typography gutterBottom variant="h4">
            {heading}
          </Typography>
          <Typography color="text.secondary">{subheading}</Typography>
        </Box>

        {elections.length > 1 ? (
          <FormControl sx={{ minWidth: 260 }}>
            <InputLabel id="election-select-label">Election</InputLabel>
            <Select
              label="Election"
              labelId="election-select-label"
              onChange={(event) => {
                const nextValue = event.target.value;
                setElectionId(nextValue ? Number(nextValue) : null);
              }}
              value={electionId ? String(electionId) : ''}
            >
              <MenuItem value="">All current elections</MenuItem>
              {elections.map((election) => (
                <MenuItem key={election.id} value={String(election.id)}>
                  {election.name} · {election.election_date}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        ) : null}
      </Stack>

      {resolvedScope === 'address' ? (
        <Alert severity="info">
          Address lookups are only used to load the ballot in this view. CivicMirror should never
          store raw addresses permanently server-side.
        </Alert>
      ) : null}

      {hasIncompleteLocation ? (
        <Alert severity="info">Choose a location above to load this feed.</Alert>
      ) : error ? (
        <ErrorMessage
          message={error}
          onRetry={() => {
            setError(null);
            setData(null);
            setRequestKey((current) => current + 1);
          }}
        />
      ) : (
        <RaceList data={data} loading={loading} onPageChange={setPage} page={page} />
      )}
    </Stack>
  );
}

export default HomePage;
