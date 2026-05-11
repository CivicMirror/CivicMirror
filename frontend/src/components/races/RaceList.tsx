import ArrowForward from '@mui/icons-material/ArrowForward';
import { Box, Button, Pagination, Paper, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import type { PaginatedResponse, Race } from '../../types';
import LoadingSpinner from '../common/LoadingSpinner';
import RaceCard from './RaceCard';

interface RaceListProps {
  data: PaginatedResponse<Race> | null;
  loading: boolean;
  page: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
}

function RaceList({ data, loading, page, onPageChange, pageSize = 25 }: RaceListProps) {
  if (loading && !data) {
    return <LoadingSpinner />;
  }

  if (!data || data.results.length === 0) {
    return (
      <Paper sx={{ p: { xs: 3, md: 5 }, textAlign: 'center' }}>
        <Stack alignItems="center" spacing={2}>
          <Typography variant="h5">No races found for this location yet.</Typography>
          <Typography color="text.secondary" maxWidth={560}>
            CivicMirror may not have imported this ballot. Help build the database!
          </Typography>
          <Button component={RouterLink} endIcon={<ArrowForward />} to="/races/submit" variant="contained">
            Add a Local Race →
          </Button>
        </Stack>
      </Paper>
    );
  }

  const pageCount = Math.max(1, Math.ceil(data.count / pageSize));

  return (
    <Stack spacing={3}>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            md: 'repeat(2, minmax(0, 1fr))',
          },
          gap: 3,
        }}
      >
        {data.results.map((race) => (
          <RaceCard key={race.id} race={race} />
        ))}
      </Box>

      {pageCount > 1 ? (
        <Stack alignItems="center">
          <Pagination
            color="primary"
            count={pageCount}
            onChange={(_, nextPage) => onPageChange(nextPage)}
            page={page}
          />
        </Stack>
      ) : null}
    </Stack>
  );
}

export default RaceList;
