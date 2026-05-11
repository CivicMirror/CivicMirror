import ArrowBack from '@mui/icons-material/ArrowBack';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { getApiErrorMessage } from '../api/client';
import { raceApi } from '../api/elections';
import { votingApi } from '../api/voting';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingSpinner from '../components/common/LoadingSpinner';
import AlreadyVotedPanel from '../components/races/AlreadyVotedPanel';
import BallotCard from '../components/races/BallotCard';
import StatusChip from '../components/races/StatusChip';
import TallyBars from '../components/races/TallyBars';
import { useAuth } from '../hooks/useAuth';
import type { Race, TallyResponse, VoteChoice, VoteResponse } from '../types';
import {
  buildRaceTallyResponse,
  formatCompactNumber,
  formatDate,
  formatDateTime,
  formatRaceSource,
  getRaceDisplayStatus,
} from '../utils/format';

function RaceDetailPage() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const [race, setRace] = useState<Race | null>(null);
  const [tally, setTally] = useState<TallyResponse | null>(null);
  const [recordedChoice, setRecordedChoice] = useState<VoteChoice | null>(null);
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

    void Promise.all([raceApi.detail(raceId), votingApi.getRaceTally(raceId)])
      .then(([raceResponse, tallyResponse]) => {
        if (!isActive) {
          return;
        }

        setRace(raceResponse);
        setTally(tallyResponse);
        setRecordedChoice(raceResponse.viewer_choice ?? null);

        if (isAuthenticated && raceResponse.viewer_has_voted && !raceResponse.viewer_choice) {
          void votingApi
            .getMyVotes()
            .then((votes) => {
              if (!isActive) {
                return;
              }

              const matchingVote = votes.find((vote) => vote.race_id === raceResponse.id);
              setRecordedChoice(matchingVote?.choice ?? null);
            })
            .catch(() => undefined);
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
  }, [id, isAuthenticated]);

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

  const tallySnapshot = tally ?? buildRaceTallyResponse(race);
  const raceDisplayStatus = getRaceDisplayStatus(race);
  const hasVoted = Boolean(race.viewer_has_voted || recordedChoice);
  const canVote = isAuthenticated && !hasVoted && raceDisplayStatus === 'active' && race.race_status === 'active';
  const votePrompt =
    !isAuthenticated
      ? null
      : raceDisplayStatus === 'results_pending' ||
          raceDisplayStatus === 'results_certified' ||
          raceDisplayStatus === 'archived'
        ? 'Voting is closed for this race, but the public tally remains visible.'
        : 'This race is not currently accepting votes.';

  const handleVoteSuccess = (_vote: VoteResponse, choice: VoteChoice) => {
    setRecordedChoice(choice);
    setRace((currentRace) =>
      currentRace
        ? {
            ...currentRace,
            viewer_has_voted: true,
            viewer_choice: choice,
            mock_vote_count: currentRace.mock_vote_count + 1,
          }
        : currentRace,
    );

    void votingApi
      .getRaceTally(race.id)
      .then((nextTally) => setTally(nextTally))
      .catch(() => undefined);
  };

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
                {formatCompactNumber(tallySnapshot.total_votes)} mock votes cast so far.
              </Alert>
              <Alert severity={raceDisplayStatus === 'active' ? 'success' : 'warning'} sx={{ flex: 1 }}>
                Voting window: {formatDateTime(race.voting_opens)} → {formatDateTime(race.voting_closes)}
              </Alert>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {hasVoted ? (
        <AlreadyVotedPanel choice={recordedChoice ?? race.viewer_choice ?? null} />
      ) : canVote ? (
        <BallotCard onVoteSuccess={handleVoteSuccess} race={race} tally={tallySnapshot} />
      ) : !isAuthenticated ? (
        <Card>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Stack spacing={2.5}>
              <Typography variant="h5">Cast a mock vote</Typography>
              <Alert severity="info">Register or log in to cast a mock vote.</Alert>
              <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5}>
                <Button component={RouterLink} to="/register" variant="contained">
                  Register
                </Button>
                <Button component={RouterLink} to="/login" variant="outlined">
                  Log in
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Alert severity="info">{votePrompt}</Alert>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={2}>
            <Typography variant="h5">Public mock tally</Typography>
            <TallyBars options={tallySnapshot.options} totalVotes={tallySnapshot.total_votes} />
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default RaceDetailPage;
