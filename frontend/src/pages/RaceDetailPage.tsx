import ArrowBack from '@mui/icons-material/ArrowBack';
import Ballot from '@mui/icons-material/Ballot';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Stack,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { raceApi } from '../api/elections';
import { getApiErrorMessage } from '../api/client';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingSpinner from '../components/common/LoadingSpinner';
import StatusChip from '../components/races/StatusChip';
import TallyBars from '../components/races/TallyBars';
import type { Race } from '../types';
import { buildRaceTallyEntries, formatCompactNumber, formatDate, formatDateTime, formatRaceSource } from '../utils/format';

function RaceDetailPage() {
  const { id } = useParams();
  const [race, setRace] = useState<Race | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const raceId = Number(id);
    if (!Number.isFinite(raceId)) {
      setError('This race could not be found.');
      setLoading(false);
      return;
    }

    let isActive = true;
    setLoading(true);
    setError(null);

    void raceApi
      .detail(raceId)
      .then((response) => {
        if (isActive) {
          setRace(response);
        }
      })
      .catch((requestError) => {
        if (isActive) {
          setError(getApiErrorMessage(requestError, 'We could not load this race right now.'));
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
  }, [id]);

  if (loading) {
    return <LoadingSpinner message="Loading race details…" />;
  }

  if (error || !race) {
    return (
      <ErrorMessage
        action={
          <Button color="inherit" component={RouterLink} startIcon={<ArrowBack />} to="/">
            Back
          </Button>
        }
        message={error ?? 'This race could not be found.'}
      />
    );
  }

  const tallyEntries = buildRaceTallyEntries(race);

  return (
    <Stack spacing={3}>
      <Button component={RouterLink} startIcon={<ArrowBack />} sx={{ alignSelf: 'flex-start' }} to="/">
        Back to races
      </Button>

      <Card>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={3}>
            <Stack direction={{ xs: 'column', md: 'row' }} gap={2} justifyContent="space-between">
              <Box>
                <Typography color="text.secondary" gutterBottom variant="body2">
                  {race.election.name} · {formatDate(race.election.election_date)}
                </Typography>
                <Typography gutterBottom variant="h3">
                  {race.office_title}
                </Typography>
                <Typography color="text.secondary" variant="body1">
                  {race.jurisdiction}
                </Typography>
              </Box>

              <Stack alignItems={{ xs: 'flex-start', md: 'flex-end' }} gap={1}>
                <Chip label={formatRaceSource(race.source)} variant="filled" />
                <StatusChip {...race} />
              </Stack>
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} gap={2}>
              <Alert severity="info" sx={{ flex: 1 }}>
                {formatCompactNumber(race.mock_vote_count)} mock votes cast so far.
              </Alert>
              <Alert severity="success" sx={{ flex: 1 }}>
                Voting window: {formatDateTime(race.voting_opens)} → {formatDateTime(race.voting_closes)}
              </Alert>
            </Stack>

            <Divider />

            <Stack spacing={2}>
              <Typography variant="h5">Mock tally snapshot</Typography>
              <TallyBars entries={tallyEntries} />
            </Stack>

            <Divider />

            <Stack spacing={2}>
              <Typography variant="h5">
                {race.race_type === 'candidate' ? 'Candidates' : 'Measure options'}
              </Typography>
              <Stack spacing={1.5}>
                {tallyEntries.map((entry) => (
                  <Card key={entry.id} variant="outlined">
                    <CardContent sx={{ py: 2.5 }}>
                      <Stack alignItems="center" direction="row" justifyContent="space-between" spacing={2}>
                        <Box>
                          <Typography fontWeight={700}>{entry.label}</Typography>
                          {entry.party ? (
                            <Typography color="text.secondary" variant="body2">
                              {entry.party}
                            </Typography>
                          ) : null}
                        </Box>
                        <Typography color="text.secondary" variant="body2">
                          {entry.votes} votes · {Math.round((entry.percentage ?? 0) * 10) / 10}%
                        </Typography>
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={2}>
            <Stack alignItems="center" direction="row" gap={1}>
              <Ballot color="primary" />
              <Typography variant="h5">Cast Your Mock Vote</Typography>
            </Stack>
            <Typography color="text.secondary">
              Phase 5 will hook the live mock-voting experience into this page. The results and race
              details above are already public and ready for comparison once voting launches.
            </Typography>
            <Button disabled variant="contained">
              Voting opens in Phase 5
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default RaceDetailPage;
