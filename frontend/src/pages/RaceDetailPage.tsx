import ArrowBack from '@mui/icons-material/ArrowBack';
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
import { getApiErrorMessage } from '../api/client';
import { civicElectionsApi } from '../api/civicElections';
import { votingApi } from '../api/voting';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingSpinner from '../components/common/LoadingSpinner';
import AlreadyVotedPanel from '../components/races/AlreadyVotedPanel';
import BallotCard from '../components/races/BallotCard';
import CertificationBadge from '../components/races/CertificationBadge';
import OfficialResultsPanel from '../components/races/OfficialResultsPanel';
import StatusChip from '../components/races/StatusChip';
import TallyBars from '../components/races/TallyBars';
import { useAuth } from '../hooks/useAuth';
import type { CivicRaceDetail } from '../types/civicApi';
import type { Race, TallyResponse, VoteChoice, VotePayload, VoteResponse } from '../types';
import {
  buildRaceTallyResponse,
  formatCompactNumber,
  formatDate,
  formatRaceSource,
  getRaceDisplayStatus,
} from '../utils/format';
import { civicRaceDetailToLegacy } from '../utils/civicRaceAdapter';

function RaceDetailPage() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const [civicDetail, setCivicDetail] = useState<CivicRaceDetail | null>(null);
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

    void (async () => {
      try {
        // Phase 1: fetch race detail to get election FK
        const detail = await civicElectionsApi.getRaceDetail(raceId);
        if (!isActive) return;

        // Phase 2: fetch election and tally concurrently
        const [election, tallyResponse] = await Promise.all([
          civicElectionsApi.getElection(detail.election),
          votingApi.getRaceTallyByExternalId(raceId),
        ]);
        if (!isActive) return;

        setCivicDetail(detail);
        setRace(civicRaceDetailToLegacy(detail, election));
        if (tallyResponse) setTally(tallyResponse);
      } catch (requestError) {
        if (isActive) {
          setError(getApiErrorMessage(requestError, 'We could not load this race right now.'));
        }
      } finally {
        if (isActive) setLoading(false);
      }
    })();

    return () => {
      isActive = false;
    };
  }, [id]);

  if (loading) {
    return <LoadingSpinner message="Loading race details…" />;
  }

  if (error || !race || !civicDetail) {
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
          raceDisplayStatus === 'partial_results' ||
          raceDisplayStatus === 'archived'
        ? 'Voting is closed for this race, but the public tally remains visible.'
        : 'This race is not currently accepting votes.';

  const raceId = Number(id);

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
      .getRaceTallyByExternalId(raceId)
      .then((nextTally) => { if (nextTally) setTally(nextTally); })
      .catch(() => undefined);
  };

  const handleSubmitVote = (payload: VotePayload): Promise<VoteResponse> =>
    votingApi.postVoteByExternalId(raceId, payload);

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
                <StatusChip race_status={race.race_status} />
                {race.certification_status !== 'upcoming' ? (
                  <CertificationBadge status={race.certification_status} />
                ) : null}
              </Stack>
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} gap={2}>
              <Alert severity="info" sx={{ flex: 1 }}>
                {formatCompactNumber(tallySnapshot.total_votes)} mock votes cast so far.
              </Alert>
              <Alert severity={raceDisplayStatus === 'active' ? 'success' : 'warning'} sx={{ flex: 1 }}>
                {raceDisplayStatus === 'active'
                  ? 'This race is currently accepting mock votes.'
                  : 'This race is not currently accepting mock votes.'}
              </Alert>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {hasVoted ? (
        <AlreadyVotedPanel choice={recordedChoice ?? race.viewer_choice ?? null} />
      ) : canVote ? (
        <BallotCard
          onSubmitVote={handleSubmitVote}
          onVoteSuccess={handleVoteSuccess}
          race={race}
          tally={tallySnapshot}
        />
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

      {race.certification_status !== 'upcoming' ? (
        <Card>
          <CardContent sx={{ p: { xs: 3, md: 4 } }}>
            <Stack spacing={2.5}>
              <Divider />
              <Typography variant="h5">Official Results</Typography>
              <OfficialResultsPanel
                certificationStatus={race.certification_status}
                civicRaceDetail={civicDetail}
                raceId={raceId}
              />
            </Stack>
          </CardContent>
        </Card>
      ) : null}
    </Stack>
  );
}

export default RaceDetailPage;
