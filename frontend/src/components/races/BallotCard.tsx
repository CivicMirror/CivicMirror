import axios from 'axios';
import HowToVote from '@mui/icons-material/HowToVote';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { getApiErrorMessage } from '../../api/client';
import { votingApi } from '../../api/voting';
import type { Race, TallyResponse, VoteChoice, VoteErrorCode, VoteErrorResponse, VotePayload, VoteResponse } from '../../types';

interface BallotCardProps {
  race: Race;
  tally: TallyResponse;
  onVoteSuccess: (vote: VoteResponse, choice: VoteChoice) => void;
  /** Optional override for posting the vote. Defaults to votingApi.postVote(race.id). */
  onSubmitVote?: (payload: VotePayload) => Promise<VoteResponse>;
}

const FRIENDLY_VOTE_ERRORS: Partial<Record<VoteErrorCode, string>> = {
  not_authenticated: 'Please log in to cast a mock vote.',
  race_inactive: 'This race is not currently accepting votes.',
  voting_closed: 'Voting window has closed for this race.',
  invalid_option: 'That selection is no longer valid.',
  already_voted: "You've already voted in this race.",
};

const isWriteInCandidate = (candidateStatus?: string) => candidateStatus === 'write_in';

const getVoteErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error) && error.response?.data && typeof error.response.data === 'object') {
    const data = error.response.data as VoteErrorResponse;
    if (data.code && FRIENDLY_VOTE_ERRORS[data.code]) {
      return FRIENDLY_VOTE_ERRORS[data.code];
    }
  }

  return getApiErrorMessage(error, 'We could not record your vote right now.');
};

function BallotCard({ race, tally, onVoteSuccess, onSubmitVote }: BallotCardProps) {
  const [selectedValue, setSelectedValue] = useState('');
  const [writeInValue, setWriteInValue] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const tallyCountById = useMemo(
    () =>
      new Map(
        tally.options
          .filter((option) => option.type === (race.race_type === 'candidate' ? 'candidate' : 'measure_option'))
          .map((option) => [option.id, option.count]),
      ),
    [race.race_type, tally.options],
  );

  const sortedCandidates = useMemo(() => {
    return [...(race.candidates ?? [])]
      .filter((candidate) => !isWriteInCandidate(candidate.candidate_status))
      .sort((left, right) => {
        const countDifference = (tallyCountById.get(right.id) ?? 0) - (tallyCountById.get(left.id) ?? 0);
        if (countDifference !== 0) {
          return countDifference;
        }

        return left.name.localeCompare(right.name);
      });
  }, [race.candidates, tallyCountById]);

  const topCandidateIds = useMemo(() => new Set(sortedCandidates.slice(0, 2).map((candidate) => candidate.id)), [sortedCandidates]);

  const totalCandidateCount = race.candidates?.length ?? 0;
  const writeInCandidate = race.candidates?.find((candidate) => isWriteInCandidate(candidate.candidate_status));
  const canShowWriteIn = Boolean(writeInCandidate) && totalCandidateCount < 10;
  const displayCandidateLimit = canShowWriteIn ? 9 : 10;
  const displayCandidates = sortedCandidates.slice(0, displayCandidateLimit);
  const displayMeasureOptions = race.measure_options ?? [];
  const writeInSelected = Boolean(writeInCandidate) && selectedValue === `candidate-${writeInCandidate.id}`;

  const selectedChoice = useMemo<VoteChoice | null>(() => {
    if (race.race_type === 'candidate') {
      const selectedCandidateId = Number(selectedValue.replace('candidate-', ''));
      if (!Number.isFinite(selectedCandidateId)) {
        return null;
      }

      const selectedCandidate = race.candidates?.find((candidate) => candidate.id === selectedCandidateId);
      if (!selectedCandidate) {
        return null;
      }

      return {
        type: 'candidate',
        id: selectedCandidate.id,
        label: writeInSelected ? writeInValue.trim() || selectedCandidate.name : selectedCandidate.name,
      };
    }

    const selectedMeasureId = Number(selectedValue.replace('measure-', ''));
    if (!Number.isFinite(selectedMeasureId)) {
      return null;
    }

    const selectedMeasureOption = race.measure_options?.find((option) => option.id === selectedMeasureId);
    if (!selectedMeasureOption) {
      return null;
    }

    return {
      type: 'measure_option',
      id: selectedMeasureOption.id,
      label: selectedMeasureOption.option_label,
    };
  }, [race.candidates, race.measure_options, race.race_type, selectedValue, writeInSelected, writeInValue]);

  const canSubmit = Boolean(selectedChoice) && (!writeInSelected || Boolean(writeInValue.trim())) && !submitting;

  const handleConfirmVote = async () => {
    if (!selectedChoice) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const vote = await (onSubmitVote
        ? onSubmitVote(
            selectedChoice.type === 'candidate'
              ? { candidate_id: selectedChoice.id }
              : { measure_option_id: selectedChoice.id },
          )
        : votingApi.postVote(
            race.id,
            selectedChoice.type === 'candidate'
              ? { candidate_id: selectedChoice.id }
              : { measure_option_id: selectedChoice.id },
          ));
      onVoteSuccess(vote, selectedChoice);
      setDialogOpen(false);
    } catch (requestError) {
      setError(getVoteErrorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  };

  const helperMessage =
    race.race_type === 'candidate' && totalCandidateCount > 10
      ? 'Showing top 10 candidates'
      : race.race_type === 'candidate' && Boolean(writeInCandidate) && totalCandidateCount >= 10
        ? 'Write-in voting is unavailable because this race already has 10 candidates.'
        : null;

  return (
    <>
      <Card>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={2.5}>
            <Stack alignItems="center" direction="row" gap={1}>
              <HowToVote color="primary" />
              <Typography variant="h5">Cast your mock vote</Typography>
            </Stack>

            {error ? <Alert severity="error">{error}</Alert> : null}
            {helperMessage ? <Alert severity="info">{helperMessage}</Alert> : null}

            <FormControl error={Boolean(error)}>
              <RadioGroup
                name={`race-${race.id}-ballot`}
                onChange={(event) => {
                  setSelectedValue(event.target.value);
                  setError(null);
                }}
                value={selectedValue}
              >
                {race.race_type === 'candidate'
                  ? displayCandidates.map((candidate, index) => {
                      const isTopCandidate = topCandidateIds.has(candidate.id);
                      return (
                        <Box
                          key={candidate.id}
                          sx={{
                            border: '1px solid',
                            borderColor: isTopCandidate ? 'secondary.main' : 'divider',
                            borderRadius: 2,
                            mb: 1.25,
                            px: 1,
                          }}
                        >
                          <FormControlLabel
                            control={<Radio />}
                            value={`candidate-${candidate.id}`}
                            label={
                              <Stack direction="row" flexWrap="wrap" gap={1} sx={{ py: 1 }}>
                                <Typography color={isTopCandidate ? 'secondary.main' : 'text.primary'} fontWeight={isTopCandidate ? 700 : 500}>
                                  {candidate.name}
                                </Typography>
                                {candidate.party ? (
                                  <Typography color="text.secondary" variant="body2">
                                    {candidate.party}
                                  </Typography>
                                ) : null}
                                {isTopCandidate ? (
                                  <Chip color="secondary" label={index === 0 ? 'Top tally' : 'Top 2'} size="small" />
                                ) : null}
                              </Stack>
                            }
                            sx={{ alignItems: 'flex-start', m: 0, width: '100%' }}
                          />
                        </Box>
                      );
                    })
                  : displayMeasureOptions.map((option) => (
                      <Box key={option.id} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, mb: 1.25, px: 1 }}>
                        <FormControlLabel
                          control={<Radio />}
                          value={`measure-${option.id}`}
                          label={<Typography sx={{ py: 1 }}>{option.option_label}</Typography>}
                          sx={{ m: 0, width: '100%' }}
                        />
                      </Box>
                    ))}

                {race.race_type === 'candidate' && canShowWriteIn && writeInCandidate ? (
                  <Box sx={{ border: '1px solid', borderColor: writeInSelected ? 'secondary.main' : 'divider', borderRadius: 2, px: 1, py: 0.5 }}>
                    <FormControlLabel
                      control={<Radio />}
                      value={`candidate-${writeInCandidate.id}`}
                      label={
                        <Typography color={writeInSelected ? 'secondary.main' : 'text.primary'} fontWeight={writeInSelected ? 700 : 500} sx={{ py: 1 }}>
                          Write-in
                        </Typography>
                      }
                      sx={{ m: 0, width: '100%' }}
                    />
                    <Box sx={{ pb: 1.5, pl: 4.5, pr: 1 }}>
                      <TextField
                        disabled={!writeInSelected || submitting}
                        fullWidth
                        helperText={writeInSelected ? 'Enter the write-in name you want reflected in your confirmation.' : 'Select write-in to enter a name.'}
                        label="Write-in name"
                        onChange={(event) => setWriteInValue(event.target.value)}
                        value={writeInValue}
                      />
                    </Box>
                  </Box>
                ) : null}
              </RadioGroup>
              {writeInSelected && !writeInValue.trim() ? (
                <FormHelperText>Please enter a write-in name before submitting.</FormHelperText>
              ) : null}
            </FormControl>

            <Button
              disabled={!canSubmit}
              onClick={() => setDialogOpen(true)}
              variant="contained"
            >
              {submitting ? <CircularProgress color="inherit" size={18} sx={{ mr: 1 }} /> : null}
              Submit vote
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Dialog fullWidth maxWidth="xs" onClose={() => !submitting && setDialogOpen(false)} open={dialogOpen}>
        <DialogTitle>Confirm your vote</DialogTitle>
        <DialogContent>
          <Typography>Confirm your vote for {selectedChoice?.label ?? 'this choice'}?</Typography>
        </DialogContent>
        <DialogActions>
          <Button disabled={submitting} onClick={() => setDialogOpen(false)}>
            Cancel
          </Button>
          <Button disabled={!canSubmit} onClick={() => void handleConfirmVote()} variant="contained">
            {submitting ? <CircularProgress color="inherit" size={18} sx={{ mr: 1 }} /> : null}
            Confirm vote
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default BallotCard;
