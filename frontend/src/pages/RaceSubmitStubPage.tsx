import ArrowBack from '@mui/icons-material/ArrowBack';
import { Button, Card, CardContent, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

function RaceSubmitStubPage() {
  return (
    <Card>
      <CardContent sx={{ p: { xs: 3, md: 5 } }}>
        <Stack spacing={2.5}>
          <Typography variant="h4">Add a local race</Typography>
          <Typography color="text.secondary">
            Phase 6 will open CivicMirror's local race submission flow. For now, keep browsing public
            contests and watch this space for community ballot-building tools.
          </Typography>
          <Button component={RouterLink} startIcon={<ArrowBack />} to="/" variant="contained">
            Back to the race browser
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default RaceSubmitStubPage;
