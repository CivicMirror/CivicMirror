import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  FormControl,
  InputLabel,
  Link,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { civicElectionsApi } from '../api/civicElections';
import ErrorMessage from '../components/common/ErrorMessage';
import LocationBar from '../components/races/LocationBar';
import RaceList from '../components/races/RaceList';
import { useRaceFilters } from '../hooks/useRaceFilters';
import { useRaceFiltersStore } from '../store/raceFiltersStore';
import type { Election, PaginatedResponse, Race } from '../types';
import { formatStateName } from '../utils/format';
import { civicElectionToLegacy, civicRaceBaseToLegacy, electionsFromLookup, lookupResultsToLegacyPaged } from '../utils/civicRaceAdapter';
import { getTimeBounds } from '../utils/timeFilter';
import { COVERAGE } from '../utils/coverage';

function HomePage() {
  const {
    activeLocationLabel,
    address,
    effectiveState,
    electionId,
    isAutoDetected,
    resolvedScope,
    timeFilter,
    zip,
  } = useRaceFilters();

  const setElectionId = useRaceFiltersStore((state) => state.setElectionId);
  const contestType = useRaceFiltersStore((state) => state.contestType);
  const timeBounds = getTimeBounds(timeFilter);

  const [page, setPage] = useState(1);
  const [requestKey, setRequestKey] = useState(0);
  const [data, setData] = useState<PaginatedResponse<Race> | null>(null);
  // elections derived from lookup response (ZIP scope) or from race data (other scopes)
  const [lookupElections, setLookupElections] = useState<Election[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeRaceCount, setActiveRaceCount] = useState<number | null>(null);

  useEffect(() => {
    void civicElectionsApi.listRaces({ race_status: 'active' })
      .then((res) => setActiveRaceCount(res.count))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    setPage(1);
  }, [address, contestType, effectiveState, electionId, resolvedScope, timeFilter, zip]);

  const hasIncompleteLocation =
    (resolvedScope === 'state' && !effectiveState) ||
    (resolvedScope === 'zip' && !zip) ||
    (resolvedScope === 'address' && !address);

  useEffect(() => {
    if (hasIncompleteLocation) {
      setLoading(false);
      setData(null);
      setLookupElections(null);
      return;
    }

    let isActive = true;
    setLoading(true);
    setError(null);

    if (resolvedScope === 'zip' && zip) {
      // ZIP + Historical: the lookup endpoint only returns active elections, so
      // historical data is not available via this path.
      if (timeFilter === 'historical') {
        setLoading(false);
        setData(null);
        setLookupElections(null);
        return;
      }

      // ZIP scope — use the CivicMirror-API lookup endpoint.
      // The lookup endpoint returns full race detail (candidates + measure_options) for all active
      // elections in the state. We apply contestType filtering, time bounds, and pagination client-side.
      void civicElectionsApi
        .lookup(zip, electionId ?? undefined)
        .then((results) => {
          if (!isActive) return;
          setLookupElections(electionsFromLookup(results));
          setData(lookupResultsToLegacyPaged(results, page, contestType, timeBounds));
        })
        .catch((requestError: unknown) => {
          if (isActive) {
            setError(
              requestError instanceof Error
                ? requestError.message
                : 'We could not load races right now.',
            );
          }
        })
        .finally(() => {
          if (isActive) setLoading(false);
        });
    } else {
      // State / national / address scopes — CivicMirror-API
      setLookupElections(null);

      if (resolvedScope === 'address') {
        // Address geocoding is not yet available in the new API.
        setError('Address lookup is not yet available. Please enter a ZIP code to find your ballot.');
        setLoading(false);
      } else {
        const stateFilter = resolvedScope === 'state' ? (effectiveState ?? undefined) : undefined;
        const jurisdictionLevelFilter = resolvedScope === 'national' ? ('national' as const) : undefined;
        const RACE_TYPE_VALUES = new Set(['candidate', 'measure']);
        const raceTypeFilter =
          contestType && RACE_TYPE_VALUES.has(contestType) ? contestType : undefined;

        void Promise.all([
          civicElectionsApi.listRaces({
            state: stateFilter,
            race_status: timeBounds.race_status,
            election: electionId ?? undefined,
            race_type: raceTypeFilter,
            jurisdiction_level: jurisdictionLevelFilter,
            election_date__gte: timeBounds.election_date__gte,
            election_date__lte: timeBounds.election_date__lte,
            page,
          }),
          civicElectionsApi.listElections({
            state: stateFilter,
            jurisdiction_level: jurisdictionLevelFilter,
            election_date__gte: timeBounds.election_date__gte,
            election_date__lte: timeBounds.election_date__lte,
            page_size: 200,
          }),
        ])
          .then(([racesResponse, electionsResponse]) => {
            if (!isActive) return;
            const electionMap = new Map<number, Election>(
              electionsResponse.results.map((e) => [e.id, civicElectionToLegacy(e)]),
            );
            // Cross-filter races to only those belonging to elections in the
            // current time window. This ensures date bounds are enforced even
            // though /api/v1/races/ has no direct date filter.
            // Note: this client-side filter means pagination counts may be
            // slightly off when the server returns races outside the date range.
            const filteredRaceResults = racesResponse.results.filter((r) =>
              electionMap.has(r.election),
            );
            const legacyRaces: Race[] = filteredRaceResults.map((r) =>
              civicRaceBaseToLegacy(
                r,
                electionMap.get(r.election) ?? {
                  id: r.election,
                  name: '',
                  election_date: '',
                  jurisdiction_level: 'state',
                  status: 'active',
                },
              ),
            );
            setData({
              count: filteredRaceResults.length,
              next: null,
              previous: null,
              results: legacyRaces,
            });
          })
          .catch((requestError: unknown) => {
            if (isActive) {
              setError(
                requestError instanceof Error
                  ? requestError.message
                  : 'We could not load races right now.',
              );
            }
          })
          .finally(() => {
            if (isActive) setLoading(false);
          });
      }
    }

    return () => {
      isActive = false;
    };
  }, [address, contestType, effectiveState, electionId, hasIncompleteLocation, page, requestKey, resolvedScope, timeFilter, zip]);

  const elections = useMemo(() => {
    // For ZIP scope, elections come from the lookup response directly.
    // For other scopes they are derived from the race data returned by the embedded backend.
    if (lookupElections) return lookupElections;
    const byId = new Map<number, Election>();
    data?.results.forEach((race) => {
      byId.set(race.election.id, race.election);
    });
    return [...byId.values()].sort((left, right) =>
      left.election_date.localeCompare(right.election_date),
    );
  }, [data, lookupElections]);

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
            <Stack direction={{ xs: 'column', sm: 'row' }} alignItems={{ sm: 'center' }} gap={1.5} flexWrap="wrap">
              <Button component="a" href="#civicmirror-location-bar" variant="contained">
                Enter ZIP or address
              </Button>
              <Button color="primary" component={RouterLink} to="/register" variant="outlined">
                Register to save your profile
              </Button>
              <Link component={RouterLink} to="/coverage" variant="body2" sx={{ ml: { sm: 0.5 } }}>
                See which states have full data →
              </Link>
            </Stack>
            <Divider />
            <Stack direction="row" gap={4} flexWrap="wrap">
              <Box>
                <Typography fontWeight={700} variant="subtitle1">50</Typography>
                <Typography color="text.secondary" display="block" variant="caption">states covered</Typography>
              </Box>
              <Box>
                <Typography fontWeight={700} variant="subtitle1">{Object.values(COVERAGE).length}</Typography>
                <Typography color="text.secondary" display="block" variant="caption">live data adapters</Typography>
              </Box>
              {activeRaceCount !== null && (
                <Box>
                  <Typography fontWeight={700} variant="subtitle1">{activeRaceCount.toLocaleString()}</Typography>
                  <Typography color="text.secondary" display="block" variant="caption">active races</Typography>
                </Box>
              )}
              <Box>
                <Typography fontWeight={700} variant="subtitle1">Open</Typography>
                <Typography color="text.secondary" display="block" variant="caption">no eligibility required</Typography>
              </Box>
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
      ) : resolvedScope === 'zip' && timeFilter === 'historical' ? (
        <Paper sx={{ p: { xs: 3, md: 5 }, textAlign: 'center' }}>
          <Stack alignItems="center" spacing={2}>
            <Typography variant="h5">Historical data not available for ZIP lookups.</Typography>
            <Typography color="text.secondary" maxWidth={560}>
              The ZIP lookup service only returns active, upcoming elections. To browse historical
              races, switch to <strong>State</strong> or <strong>National</strong> view and select{' '}
              <strong>Historical</strong>.
            </Typography>
          </Stack>
        </Paper>
      ) : error ? (
        <ErrorMessage
          message={error}
          onRetry={() => {
            setError(null);
            setData(null);
            setRequestKey((current) => current + 1);
          }}
        />
      ) : resolvedScope === 'zip' && !loading && data !== null && data.count === 0 ? (
        <Paper sx={{ p: { xs: 3, md: 5 }, textAlign: 'center' }}>
          <Stack alignItems="center" spacing={2}>
            {lookupElections !== null && lookupElections.length > 0 ? (
              <>
                <Typography variant="h5">No race data available for this location.</Typography>
                <Typography color="text.secondary" maxWidth={560}>
                  An election was found for this area, but no contest information is available. This
                  state may have only submitted polling location data to the data source.
                </Typography>
              </>
            ) : (
              <>
                <Typography variant="h5">No upcoming elections found for this location.</Typography>
                <Typography color="text.secondary" maxWidth={560}>
                  There are no active elections in our system for this area right now. Check back
                  closer to an election date.
                </Typography>
              </>
            )}
          </Stack>
        </Paper>
      ) : (
        <RaceList data={data} loading={loading} onPageChange={setPage} page={page} />
      )}
      <HomeFAQ />
    </Stack>
  );
}

const HOME_SCHEMA = [
  {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'CivicMirror',
    url: 'https://civicmirror.app/',
    description: 'Open civic engagement platform for unrestricted mock voting on real U.S. elections',
    foundingDate: '2026',
    sameAs: [],
  },
  {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: 'What is CivicMirror?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'CivicMirror is an open civic engagement platform that imports real U.S. election data and allows anyone to cast a mock vote, regardless of age, citizenship, or country of residence. After official results are certified, the platform compares mock vote outcomes against real-world results.',
        },
      },
      {
        '@type': 'Question',
        name: 'Is CivicMirror an official voting platform?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'No. CivicMirror is not an official election authority and is not affiliated with any government agency or political organization. Mock votes on CivicMirror have no legal effect.',
        },
      },
      {
        '@type': 'Question',
        name: 'Who can participate in CivicMirror mock votes?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'Anyone worldwide can browse races and cast mock votes on CivicMirror. There are no eligibility restrictions based on age, citizenship, or location.',
        },
      },
      {
        '@type': 'Question',
        name: 'Where does CivicMirror get its election data?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'CivicMirror imports real election data from the Google Civic Information API, OpenFEC, Open States, OpenElections, and direct integrations with state Secretary of State offices. All 50 states are covered.',
        },
      },
    ],
  },
];

function HomeFAQ() {
  const faqs = HOME_SCHEMA[1].mainEntity as Array<{ '@type': string; name: string; acceptedAnswer: { '@type': string; text: string } }>;
  return (
    <Stack spacing={2} component="section" aria-label="Frequently asked questions">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(HOME_SCHEMA) }}
      />
      <Typography variant="h5" component="h2">Frequently Asked Questions</Typography>
      {faqs.map((faq) => (
        <Stack key={faq.name} spacing={0.5}>
          <Typography variant="subtitle1" fontWeight={700}>{faq.name}</Typography>
          <Typography color="text.secondary" variant="body2">{faq.acceptedAnswer.text}</Typography>
        </Stack>
      ))}
    </Stack>
  );
}

export { HomeFAQ };
export default HomePage;
