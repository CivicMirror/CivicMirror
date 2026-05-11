import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingSpinnerProps {
  message?: string;
  minHeight?: number | string;
}

function LoadingSpinner({
  message = 'Loading the latest CivicMirror data…',
  minHeight = 240,
}: LoadingSpinnerProps) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      gap={2}
      minHeight={minHeight}
      width="100%"
    >
      <CircularProgress color="primary" />
      <Typography color="text.secondary" variant="body2">
        {message}
      </Typography>
    </Box>
  );
}

export default LoadingSpinner;
