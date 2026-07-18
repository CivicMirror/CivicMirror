import CheckCircleOutline from '@mui/icons-material/CheckCircleOutline';
import OpenInNew from '@mui/icons-material/OpenInNew';
import RadioButtonUnchecked from '@mui/icons-material/RadioButtonUnchecked';
import Sync from '@mui/icons-material/Sync';
import WarningAmber from '@mui/icons-material/WarningAmber';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { latestStateSync, useCoverageSyncStatus } from '../hooks/useCoverageSyncStatus';
import { COVERAGE_TIER_META, getTier, type CoverageTier, type CoverageTierMap } from '../utils/coverage';
import { timeAgo } from '../utils/timeAgo';
import { US_STATES } from '../utils/usStates';

const TIER_ICON: Record<CoverageTier, React.ReactNode> = {
  full: <CheckCircleOutline fontSize="small" />,
  state: <Sync fontSize="small" />,
  results: <WarningAmber fontSize="small" />,
  elections: <RadioButtonUnchecked fontSize="small" />,
};

const TIER_ORDER: CoverageTier[] = ['full', 'state', 'results', 'elections'];

function groupByTier(
  states: typeof US_STATES,
  coverageTiers?: CoverageTierMap,
  adapterStates?: string[],
) {
  const result: Partial<Record<CoverageTier, typeof US_STATES>> = {};
  for (const s of states) {
    const tier = getTier(s.code, coverageTiers, adapterStates);
    (result[tier] ??= []).push(s);
  }
  return result;
}

/** "West Virginia, Colorado, and South Carolina" style Oxford-comma join. */
function joinStateNames(states: typeof US_STATES): string {
  const names = states.map((s) => s.name);
  if (names.length === 0) return 'no states';
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names.slice(0, -1).join(', ')}, and ${names[names.length - 1]}`;
}

function buildCoverageFaqSchema(
  fullTierStateNames: string,
  fullCount: number,
  stateCount: number,
  resultsCount: number,
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: 'Which states does CivicMirror have full coverage for?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: `CivicMirror has full state integration for ${fullTierStateNames}. Full coverage means elections, races, candidates, and official results are ingested directly from the state source.`,
        },
      },
      {
        '@type': 'Question',
        name: "What does 'State Integration' mean on CivicMirror?",
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'A State Integration means CivicMirror ingests elections, races, and candidates from an official state source, but does not yet ingest official results for that state.',
        },
      },
      {
        '@type': 'Question',
        name: "What does 'Results Adapter' mean on CivicMirror?",
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'A Results Adapter means CivicMirror can display live election-night results for that state when configured per election. Elections and races for these states come from the national Civic data feed.',
        },
      },
      {
        '@type': 'Question',
        name: 'Does CivicMirror cover all 50 states?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: `Yes. All 50 states have elections and races available via the national Civic data feed. ${fullCount} states have full state integration with official results, ${stateCount} have state election/race/candidate integration, ${resultsCount} have a results adapter, and the remaining states have elections and candidate data only.`,
        },
      },
    ],
  };
}

function CoveragePage() {
  const syncStatus = useCoverageSyncStatus();
  const byTier = groupByTier(US_STATES, syncStatus?.coverage_tiers, syncStatus?.adapter_states);

  const fullCount = (byTier['full'] ?? []).length;
  const stateCount = (byTier['state'] ?? []).length;
  const resultsCount = (byTier['results'] ?? []).length;
  const electionsCount = (byTier['elections'] ?? []).length;
  const fullTierStateNames = joinStateNames(byTier['full'] ?? []);

  const civicApiSync = syncStatus?.global.civic_api ?? null;

  return (
    <Stack spacing={4}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildCoverageFaqSchema(fullTierStateNames, fullCount, stateCount, resultsCount)),
        }}
      />
      {/* Hero */}
      <Card>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={1.5}>
            <Typography gutterBottom variant="h1" sx={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.25rem)' }}>
              State Coverage
            </Typography>
            <Typography color="text.secondary" maxWidth={700} variant="h6">
              CivicMirror actively tracks{' '}
              <strong>{fullCount + stateCount + resultsCount} states</strong> with dedicated data integrations.
              All 50 states have elections and races available via the national Civic data feed.
            </Typography>
            <Typography color="text.secondary" maxWidth={720} variant="body1">
              {fullCount} states — {fullTierStateNames} — have full state integration with direct
              ingestion of elections, races, candidates, and official results. State Integration
              states use official state sources for elections, races, and candidates while results
              support is still being built.
            </Typography>
            <Stack direction="row" flexWrap="wrap" gap={1.5} pt={1}>
              <Chip
                color="success"
                icon={<CheckCircleOutline />}
                label={`${fullCount} Full Coverage`}
                variant="outlined"
              />
              <Chip
                color="warning"
                icon={<Sync />}
                label={`${stateCount} State Integration`}
                variant="outlined"
              />
              <Chip
                color="warning"
                icon={<WarningAmber />}
                label={`${resultsCount} Results Adapter`}
                variant="outlined"
              />
              <Chip
                color="default"
                icon={<RadioButtonUnchecked />}
                label={`${electionsCount} Elections Only`}
                variant="outlined"
              />
              {civicApiSync && (
                <Chip
                  icon={<Sync />}
                  label={`National feed synced ${timeAgo(civicApiSync.last_completed_at)}`}
                  size="small"
                  variant="outlined"
                />
              )}
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {/* Tier sections */}
      {TIER_ORDER.map((tier) => {
        const meta = COVERAGE_TIER_META[tier];
        const states = byTier[tier] ?? [];

        return (
          <Stack key={tier} spacing={2}>
            <Stack direction={{ xs: 'column', sm: 'row' }} alignItems={{ sm: 'center' }} gap={1.5}>
              <Box display="flex" alignItems="center" gap={1}>
                <Box color={
                  tier === 'full' ? 'success.main' :
                  tier === 'state' ? 'warning.main' :
                  tier === 'results' ? 'warning.main' :
                  'text.disabled'
                }>
                  {TIER_ICON[tier]}
                </Box>
                <Typography variant="h5">{meta.label}</Typography>
                <Chip label={states.length} size="small" color={meta.color} />
              </Box>
            </Stack>
            <Typography color="text.secondary" maxWidth={680}>
              {meta.description}
            </Typography>

            <Box
              display="grid"
              gap={1.5}
              gridTemplateColumns={{
                xs: 'repeat(2, 1fr)',
                sm: 'repeat(3, 1fr)',
                md: 'repeat(4, 1fr)',
                lg: 'repeat(5, 1fr)',
              }}
            >
              {states.map((state) => {
                const stateSync = syncStatus
                  ? latestStateSync(syncStatus.by_state, state.code)
                  : null;
                return (
                  <StateCard
                    key={state.code}
                    code={state.code}
                    name={state.name}
                    tier={tier}
                    lastSyncedAt={stateSync?.last_completed_at ?? null}
                  />
                );
              })}
            </Box>
          </Stack>
        );
      })}
    </Stack>
  );
}

interface StateCardProps {
  code: string;
  name: string;
  tier: CoverageTier;
  lastSyncedAt: string | null;
}

function StateCard({ code, name, tier, lastSyncedAt }: StateCardProps) {
  const meta = COVERAGE_TIER_META[tier];
  const canBrowse = tier === 'full' || tier === 'state' || tier === 'results';

  return (
    <Card
      sx={{
        height: '100%',
        opacity: tier === 'elections' ? 0.7 : 1,
        transition: 'opacity 0.15s',
        '&:hover': tier !== 'elections' ? { opacity: 1, boxShadow: 6 } : {},
      }}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Stack spacing={1} height="100%">
          <Stack direction="row" alignItems="flex-start" justifyContent="space-between" gap={0.5}>
            <Box>
              <Typography variant="subtitle2" fontWeight={700} lineHeight={1.2}>
                {code}
              </Typography>
              <Typography variant="caption" color="text.secondary" lineHeight={1.3}>
                {name}
              </Typography>
            </Box>
            {canBrowse ? (
              <Tooltip title={`Browse ${name} races`}>
                <Button
                  component={RouterLink}
                  to={`/?state=${code}`}
                  size="small"
                  sx={{ minWidth: 0, p: 0.5 }}
                >
                  <OpenInNew fontSize="inherit" />
                </Button>
              </Tooltip>
            ) : null}
          </Stack>
          <Chip color={meta.color} label={meta.label} size="small" sx={{ alignSelf: 'flex-start' }} />
          {lastSyncedAt && (
            <Typography variant="caption" color="text.disabled" lineHeight={1.3}>
              Synced {timeAgo(lastSyncedAt)}
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

export default CoveragePage;
