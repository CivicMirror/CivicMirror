import CheckCircle from '@mui/icons-material/CheckCircle';
import { Alert, Card, CardContent, Stack, Typography } from '@mui/material';
import type { VoteChoice } from '../../types';

interface AlreadyVotedPanelProps {
  choice?: VoteChoice | null;
}

function AlreadyVotedPanel({ choice }: AlreadyVotedPanelProps) {
  return (
    <Card variant="outlined">
      <CardContent sx={{ p: { xs: 3, md: 4 } }}>
        <Stack spacing={2.5}>
          <Stack alignItems="center" direction="row" gap={1}>
            <CheckCircle color="success" />
            <Typography variant="h5">You already voted</Typography>
          </Stack>

          <Alert severity="success">Your vote has been recorded and cannot be changed.</Alert>

          <Stack spacing={0.5}>
            <Typography color="text.secondary" variant="body2">
              Your recorded choice
            </Typography>
            <Typography fontWeight={700} variant="h4">
              {choice?.label ?? 'Recorded on your account'}
            </Typography>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default AlreadyVotedPanel;
