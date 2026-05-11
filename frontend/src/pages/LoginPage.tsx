import { zodResolver } from '@hookform/resolvers/zod';
import Login from '@mui/icons-material/Login';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Link,
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

const loginSchema = z.object({
  username: z.string().trim().min(1, 'Username is required.'),
  password: z.string().min(1, 'Password is required.'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoading, login } = useAuth();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  const returnTo = (location.state as { returnTo?: string } | null)?.returnTo ?? '/profile';

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);

    try {
      await login({ username: values.username.trim(), password: values.password });
      navigate(returnTo, { replace: true });
    } catch (error) {
      const fieldErrors = getApiFieldErrors(error);
      if (fieldErrors.username) {
        setError('username', { message: fieldErrors.username, type: 'server' });
      }
      if (fieldErrors.password) {
        setError('password', { message: fieldErrors.password, type: 'server' });
      }
      setFormError(getApiErrorMessage(error, 'We could not log you in right now.'));
    }
  });

  return (
    <Box display="flex" justifyContent="center" py={{ xs: 2, md: 6 }}>
      <Card sx={{ maxWidth: 520, width: '100%' }}>
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Stack spacing={3}>
            <Box>
              <Typography gutterBottom variant="h4">
                Welcome back
              </Typography>
              <Typography color="text.secondary">
                Log in to save your profile and cast mock votes as a registered user.
              </Typography>
            </Box>

            {formError ? <Alert severity="error">{formError}</Alert> : null}

            <Stack component="form" onSubmit={onSubmit} spacing={2.5}>
              <TextField
                autoComplete="username"
                error={Boolean(errors.username)}
                fullWidth
                helperText={errors.username?.message}
                label="Username"
                {...register('username')}
              />

              <TextField
                autoComplete="current-password"
                error={Boolean(errors.password)}
                fullWidth
                helperText={errors.password?.message}
                label="Password"
                type="password"
                {...register('password')}
              />

              <Button disabled={isLoading} size="large" startIcon={<Login />} type="submit" variant="contained">
                Log in
              </Button>
            </Stack>

            <Typography color="text.secondary" variant="body2">
              Need an account?{' '}
              <Link component={RouterLink} to="/register">
                Create one
              </Link>
              .
            </Typography>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}

export default LoginPage;
