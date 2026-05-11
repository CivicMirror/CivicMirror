import type { ReactNode } from 'react';
import { Alert, Button, Stack } from '@mui/material';

interface ErrorMessageProps {
  message: string;
  title?: string;
  action?: ReactNode;
  onRetry?: () => void;
}

function ErrorMessage({ message, title = 'Something went wrong', action, onRetry }: ErrorMessageProps) {
  return (
    <Stack spacing={2}>
      <Alert
        severity="error"
        action={
          action ??
          (onRetry ? (
            <Button color="inherit" onClick={onRetry} size="small">
              Retry
            </Button>
          ) : undefined)
        }
      >
        <strong>{title}</strong>
        <br />
        {message}
      </Alert>
    </Stack>
  );
}

export default ErrorMessage;
