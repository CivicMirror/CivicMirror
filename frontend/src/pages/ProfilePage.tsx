import { zodResolver } from '@hookform/resolvers/zod';
import Save from '@mui/icons-material/Save';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { authApi } from '../api/auth';
import { getApiErrorMessage, getApiFieldErrors } from '../api/client';
import { votingApi } from '../api/voting';
import ErrorMessage from '../components/common/ErrorMessage';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useAuth } from '../hooks/useAuth';
import type { MyVote } from '../types';
import { formatDate, formatDateTime } from '../utils/format';
import { COUNTRIES } from '../utils/countries';
import { US_STATES } from '../utils/usStates';

const profileSchema = z.object({
  age_range: z.string().optional(),
  country: z.string().max(2).optional(),
  us_state: z.string().optional(),
  gender: z.string().trim().max(50, 'Gender must be 50 characters or fewer.').optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

const ageRanges = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'];
const genderOptions = ['Woman', 'Man', 'Non-binary', 'Prefer not to say', 'Self-describe'];

function ProfilePage() {
  const { profile, setProfile } = useAuth();
  const [loading, setLoading] = useState(!profile);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [votes, setVotes] = useState<MyVote[]>([]);
  const [votesLoading, setVotesLoading] = useState(true);
  const [votesError, setVotesError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setError: setFieldError,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      age_range: profile?.age_range ?? '',
      country: profile?.country ?? '',
      us_state: profile?.us_state ?? '',
      gender: profile?.gender ?? '',
    },
  });

  useEffect(() => {
    if (profile) {
      reset({
        age_range: profile.age_range ?? '',
        country: profile.country ?? '',
        us_state: profile.us_state ?? '',
        gender: profile.gender ?? '',
      });
      setLoading(false);
      return;
    }

    setLoading(true);
    void authApi
      .getProfile()
      .then((nextProfile) => {
        setProfile(nextProfile);
        reset({
          age_range: nextProfile.age_range ?? '',
          country: nextProfile.country ?? '',
          us_state: nextProfile.us_state ?? '',
          gender: nextProfile.gender ?? '',
        });
        setError(null);
      })
      .catch((requestError) => {
        setError(getApiErrorMessage(requestError, 'We could not load your profile.'));
      })
      .finally(() => {
        setLoading(false);
      });
  }, [profile, reset, setProfile]);

  useEffect(() => {
    let isActive = true;
    setVotesLoading(true);
    setVotesError(null);

    void votingApi
      .getMyVotes()
      .then((response) => {
        if (isActive) {
          setVotes(response);
        }
      })
      .catch((requestError) => {
        if (isActive) {
          setVotesError(getApiErrorMessage(requestError, 'We could not load your mock vote history.'));
        }
      })
      .finally(() => {
        if (isActive) {
          setVotesLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    setSuccessMessage(null);

    try {
      const updatedProfile = await authApi.updateProfile({
        age_range: values.age_range || undefined,
        country: values.country?.trim() || undefined,
        us_state: values.us_state || undefined,
        gender: values.gender?.trim() || undefined,
      });
      setProfile(updatedProfile);
      setSuccessMessage('Your profile has been updated.');
    } catch (requestError) {
      const fieldErrors = getApiFieldErrors(requestError);
      (['age_range', 'country', 'us_state', 'gender'] as const).forEach((field) => {
        if (fieldErrors[field]) {
          setFieldError(field, { message: fieldErrors[field], type: 'server' });
        }
      });
      setError(getApiErrorMessage(requestError, 'We could not save your changes.'));
    }
  });

  if (loading) {
    return <LoadingSpinner message="Loading your registered-user profile…" />;
  }

  if (error && !profile) {
    return <ErrorMessage message={error} />;
  }

  return (
    <Stack spacing={3.5}>
      <Box>
        <Typography gutterBottom variant="h4">
          Your profile
        </Typography>
        <Typography color="text.secondary">
          Manage the optional details attached to your registered-user account. Saved ZIP codes are
          treated as private and are never shown publicly.
        </Typography>
      </Box>

      <Card>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={3}>
            <Stack direction={{ xs: 'column', sm: 'row' }} gap={2} justifyContent="space-between">
              <Box>
                <Typography gutterBottom variant="h5">
                  {profile?.username}
                </Typography>
                <Typography color="text.secondary" variant="body2">
                  Joined {formatDate(profile?.created_at)}
                </Typography>
              </Box>
              <Chip color="primary" label="Registered user" variant="filled" />
            </Stack>

            {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}
            {error ? <Alert severity="error">{error}</Alert> : null}

            <Stack component="form" onSubmit={onSubmit} spacing={2.5}>
              <TextField
                error={Boolean(errors.age_range)}
                fullWidth
                helperText={errors.age_range?.message}
                label="Age range"
                select
                {...register('age_range')}
              >
                <MenuItem value="">Prefer not to say</MenuItem>
                {ageRanges.map((ageRange) => (
                  <MenuItem key={ageRange} value={ageRange}>
                    {ageRange}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                error={Boolean(errors.country)}
                fullWidth
                helperText={errors.country?.message}
                label="Country"
                select
                {...register('country')}
              >
                <MenuItem value="">Prefer not to say</MenuItem>
                {COUNTRIES.map((c) => (
                  <MenuItem key={c.code} value={c.code}>
                    {c.name}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                error={Boolean(errors.us_state)}
                fullWidth
                helperText={errors.us_state?.message}
                label="U.S. state"
                select
                {...register('us_state')}
              >
                <MenuItem value="">No preference</MenuItem>
                {US_STATES.map((stateOption) => (
                  <MenuItem key={stateOption.code} value={stateOption.code}>
                    {stateOption.name}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                error={Boolean(errors.gender)}
                fullWidth
                helperText={errors.gender?.message}
                label="Gender"
                select
                {...register('gender')}
              >
                <MenuItem value="">Prefer not to say</MenuItem>
                {genderOptions.map((option) => (
                  <MenuItem key={option} value={option}>
                    {option}
                  </MenuItem>
                ))}
              </TextField>

              <Button disabled={isSubmitting} startIcon={<Save />} type="submit" variant="contained">
                Save profile
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={2.5}>
            <Box>
              <Typography gutterBottom variant="h5">
                My Votes
              </Typography>
              <Typography color="text.secondary">
                Review the mock votes you have already cast across CivicMirror races.
              </Typography>
            </Box>

            {votesError ? <Alert severity="error">{votesError}</Alert> : null}

            {votesLoading ? (
              <LoadingSpinner message="Loading your mock vote history…" />
            ) : votes.length === 0 ? (
              <Typography color="text.secondary">You haven't cast any mock votes yet.</Typography>
            ) : (
              <Stack divider={<Divider flexItem />} spacing={2}>
                {votes.map((vote) => (
                  <Stack key={vote.id} spacing={0.75}>
                    <Typography fontWeight={700} variant="h6">
                      {vote.office_title}
                    </Typography>
                    <Typography color="text.secondary" variant="body2">
                      {vote.election_name} · {vote.jurisdiction}
                    </Typography>
                    <Typography variant="body1">Your choice: {vote.choice.label}</Typography>
                    <Typography color="text.secondary" variant="body2">
                      Cast {formatDateTime(vote.cast_at)} · Race status: {vote.race_status}
                    </Typography>
                  </Stack>
                ))}
              </Stack>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default ProfilePage;
