import {
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import type { Race } from '../../types';
import { formatDate } from '../../utils/format';

interface RaceCardProps {
  race: Race;
}

// Maps the five internal race_status values to the three concept-level buckets.
const STATUS_BUCKET: Record<Race['race_status'], { label: string; color: 'success' | 'warning' | 'default' }> = {
  active:         { label: 'Active',   color: 'success' },
  draft:          { label: 'Pending',  color: 'warning' },
  pending_review: { label: 'Pending',  color: 'warning' },
  cancelled:      { label: 'Closed',   color: 'default' },
  archived:       { label: 'Closed',   color: 'default' },
};

const RACE_TYPE_LABEL: Record<Race['race_type'], string> = {
  candidate: 'Race',
  measure:   'Measure',
};

function RaceCard({ race }: RaceCardProps) {
  const status = STATUS_BUCKET[race.race_status];
  const typeLabel = RACE_TYPE_LABEL[race.race_type] ?? 'Other';
  const dateLabel = formatDate(race.election.election_date);

  return (
    <Card sx={{ borderRadius: 1 }}>
      <CardActionArea component={RouterLink} to={`/races/${race.id}`}>
        <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" gap={1} sx={{ mb: 0.25 }}>
            <Typography
              variant="subtitle1"
              fontWeight={600}
              noWrap
              sx={{ flex: 1, minWidth: 0 }}
            >
              {race.office_title}
            </Typography>
            <Chip color={status.color} label={status.label} size="small" />
          </Stack>
          <Typography variant="caption" color="text.secondary" noWrap>
            {race.jurisdiction} &bull; {dateLabel} &bull; {typeLabel}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

export default RaceCard;
