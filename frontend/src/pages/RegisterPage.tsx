import { zodResolver } from '@hookform/resolvers/zod';
import ExpandMore from '@mui/icons-material/ExpandMore';
import PersonAdd from '@mui/icons-material/PersonAdd';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  Link,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { getApiErrorMessage, getApiFieldErrors } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { COUNTRIES } from '../utils/countries';
import { US_STATES } from '../utils/usStates';

const CURRENT_TERMS_VERSION = '2025-01';

const registerSchema = z
  .object({
    username: z.string().trim().max(50, 'Username must be 50 characters or fewer.').optional(),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters.')
      .regex(/[A-Z]/, 'Password must include an uppercase letter.')
      .regex(/[a-z]/, 'Password must include a lowercase letter.')
      .regex(/[0-9]/, 'Password must include a number.'),
    confirmPassword: z.string(),
    age_range: z.string().optional(),
    country: z.string().max(2).optional(),
    us_state: z.string().optional(),
    gender: z.string().trim().max(50, 'Gender must be 50 characters or fewer.').optional(),
    termsAccepted: z.boolean().refine((value) => value, {
      message: 'You must accept the terms to register.',
    }),
  })
  .refine((value) => value.password === value.confirmPassword, {
    message: 'Passwords do not match.',
    path: ['confirmPassword'],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

const ageRanges = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'];
const genderOptions = ['Woman', 'Man', 'Non-binary', 'Prefer not to say', 'Self-describe'];

function RegisterPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoading, register: registerUser } = useAuth();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      password: '',
      confirmPassword: '',
      age_range: '',
      country: '',
      us_state: '',
      gender: '',
      termsAccepted: false,
    },
  });

  const returnTo = (location.state as { returnTo?: string } | null)?.returnTo ?? '/profile';

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);

    try {
      await registerUser({
        username: values.username?.trim() || undefined,
        password: values.password,
        age_range: values.age_range || undefined,
        country: values.country?.trim() || undefined,
        us_state: values.us_state || undefined,
        gender: values.gender?.trim() || undefined,
        terms_version: CURRENT_TERMS_VERSION,
        terms_accepted: true,
      });
      navigate(returnTo, { replace: true });
    } catch (error) {
      const fieldErrors = getApiFieldErrors(error);
      const fieldMap: Record<string, keyof RegisterFormValues> = {
        username: 'username',
        password: 'password',
        age_range: 'age_range',
        country: 'country',
        us_state: 'us_state',
        gender: 'gender',
        terms_accepted: 'termsAccepted',
        terms_version: 'termsAccepted',
      };

      let mappedFieldCount = 0;
      Object.entries(fieldMap).forEach(([apiField, formField]) => {
        if (fieldErrors[apiField]) {
          setError(formField, { message: fieldErrors[apiField], type: 'server' });
          mappedFieldCount++;
        }
      });

      // If errors are shown inline on fields, the banner just says where to look.
      // If not, show the full API error so nothing is hidden.
      if (mappedFieldCount > 0) {
        setFormError('Please correct the errors highlighted below.');
      } else {
        setFormError(getApiErrorMessage(error, 'We could not complete registration right now.'));
      }
    }
  });

  return (
    <Box display="flex" justifyContent="center" py={{ xs: 2, md: 6 }}>
      <Card sx={{ maxWidth: 640, width: '100%' }}>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={3}>
            <Box>
              <Typography gutterBottom variant="h4">
                Create your CivicMirror account
              </Typography>
              <Typography color="text.secondary">
                Join as a registered user to track your profile and prepare for mock voting.
              </Typography>
            </Box>

            {formError ? <Alert severity="error">{formError}</Alert> : null}

            <Stack component="form" onSubmit={onSubmit} spacing={2.5}>
              <TextField
                error={Boolean(errors.username)}
                fullWidth
                helperText={errors.username?.message ?? 'Optional. Leave blank to get an auto-generated public handle.'}
                label="Username"
                {...register('username')}
              />

              <TextField
                autoComplete="new-password"
                error={Boolean(errors.password)}
                fullWidth
                helperText={errors.password?.message}
                label="Password"
                type="password"
                {...register('password')}
              />

              <TextField
                autoComplete="new-password"
                error={Boolean(errors.confirmPassword)}
                fullWidth
                helperText={errors.confirmPassword?.message}
                label="Confirm password"
                type="password"
                {...register('confirmPassword')}
              />

              <Accordion disableGutters>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box>
                    <Typography fontWeight={700}>Optional details</Typography>
                    <Typography color="text.secondary" variant="body2">
                      These fields are optional and help CivicMirror understand participation patterns in aggregate.
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={2}>
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
                  </Stack>
                </AccordionDetails>
              </Accordion>

              <FormControlLabel
                control={<Checkbox {...register('termsAccepted')} />}
                label="I accept the CivicMirror terms of use for this registered-user account."
              />
              {errors.termsAccepted ? <Typography color="error.main" variant="body2">{errors.termsAccepted.message}</Typography> : null}

              <Button
                disabled={isLoading}
                size="large"
                startIcon={<PersonAdd />}
                type="submit"
                variant="contained"
              >
                Create account
              </Button>
            </Stack>

            <Typography color="text.secondary" variant="body2">
              Already registered?{' '}
              <Link component={RouterLink} to="/login">
                Log in
              </Link>
              .
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}

export default RegisterPage;
