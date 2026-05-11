import ArrowForward from '@mui/icons-material/ArrowForward';
import HowToVote from '@mui/icons-material/HowToVote';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Divider,
  Stack,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import type { Race } from '../../types';
import { buildRaceTallyEntries, formatCompactNumber, formatRaceSource } from '../../utils/format';
import StatusChip from './StatusChip';
import TallyBars from './TallyBars';

interface RaceCardProps {
  race: Race;
}

function RaceCard({ race }: RaceCardProps) {
  const tallyEntries = buildRaceTallyEntries(race, 3);
  const previewEntries = tallyEntries.slice(0, 3);
  const hiddenCount = Math.max(0, buildRaceTallyEntries(race).length - previewEntries.length);

  return (
    <Card sx={{ height: '100%' }}>
      <CardActionArea component={RouterLink} sx={{ height: '100%' }} to={`/races/${race.id}`}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.25, height: '100%' }}>
          <Stack direction="row" flexWrap="wrap" gap={1} justifyContent="space-between">
            <Chip label={formatRaceSource(race.source)} size="small" variant="filled" />
            <StatusChip {...race} />
          </Stack>

          <Box>
            <Typography gutterBottom variant="h6">
              {race.office_title}
            </Typography>
            <Typography color="text.secondary" variant="body2">
              {race.jurisdiction}
            </Typography>
          </Box>

          <Stack direction="row" flexWrap="wrap" gap={1}>
            {previewEntries.map((entry) => (
              <Chip
                key={entry.id}
                icon={<HowToVote fontSize="small" />}
                label={entry.party ? `${entry.label} · ${entry.party}` : entry.label}
              />
            ))}
            {hiddenCount > 0 ? <Chip label={`+${hiddenCount} more`} /> : null}
          </Stack>

          <TallyBars compact entries={previewEntries} />

          <Divider />

          <Stack alignItems="center" direction="row" justifyContent="space-between" spacing={2}>
            <Typography color="text.secondary" variant="body2">
              {formatCompactNumber(race.mock_vote_count)} mock votes cast
            </Typography>
            <Stack alignItems="center" color="primary.main" direction="row" spacing={0.5}>
              <Typography color="primary.main" fontWeight={700} variant="body2">
                See details
              </Typography>
              <ArrowForward fontSize="small" />
            </Stack>
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

export default RaceCard;
