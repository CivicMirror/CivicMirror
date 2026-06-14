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
import { COVERAGE_TIER_META, getTier, type CoverageTier } from '../utils/coverage';
import { timeAgo } from '../utils/timeAgo';
import { US_STATES } from '../utils/usStates';

const TIER_ICON: Record<CoverageTier, React.ReactNode> = {
  full: <CheckCircleOutline fontSize="small" />,
  results: <WarningAmber fontSize="small" />,
  elections: <RadioButtonUnchecked fontSize="small" />,
};

const TIER_ORDER: CoverageTier[] = ['full', 'results', 'elections'];

function groupByTier(states: typeof US_STATES) {
  const result: Partial<Record<CoverageTier, typeof US_STATES>> = {};
  for (const s of states) {
    const tier = getTier(s.code);
    (result[tier] ??= []).push(s);
  }
  return result;
}

function CoveragePage() {
  const byTier = groupByTier(US_STATES);
  const syncStatus = useCoverageSyncStatus();

  const fullCount = (byTier['full'] ?? []).length;
  const resultsCount = (byTier['results'] ?? []).length;
  const electionsCount = (byTier['elections'] ?? []).length;

  const civicApiSync = syncStatus?.global.civic_api ?? null;

  return (
    <Stack spacing={4}>
      {/* Hero */}
      <Card>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={1.5}>
            <Typography gutterBottom variant="h1" sx={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.25rem)' }}>
              State Coverage
            </Typography>
            <Typography color="text.secondary" maxWidth={700} variant="h6">
              CivicMirror actively tracks{' '}
              <strong>{fullCount + resultsCount} states</strong> with dedicated data integrations.
              All 50 states have elections and races available via the national Civic data feed.
            </Typography>
            <Typography color="text.secondary" maxWidth={720} variant="body1">
              Seven states — West Virginia, Colorado, South Carolina, Massachusetts, Virginia,
              Arizona, and North Carolina — have full SOS integration with direct ingestion of
              elections, races, candidates, and live results. All remaining states have race and
              candidate data available via the national Civic Information feed.
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
  const canBrowse = tier === 'full' || tier === 'results';

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
