import { Box, LinearProgress, Stack, Typography } from '@mui/material';
import type { MockTallyEntry } from '../../types';
import { formatPercent } from '../../utils/format';

interface TallyBarsProps {
  entries: MockTallyEntry[];
  compact?: boolean;
}

function TallyBars({ entries, compact = false }: TallyBarsProps) {
  if (!entries.length) {
    return (
      <Typography color="text.secondary" variant="body2">
        Mock tally data will appear here once people begin casting votes.
      </Typography>
    );
  }

  return (
    <Stack spacing={compact ? 1 : 1.5}>
      {entries.map((entry) => (
        <Stack key={entry.id} spacing={0.5}>
          <Stack alignItems="center" direction="row" justifyContent="space-between" spacing={1}>
            <Typography fontWeight={entry.is_leading ? 700 : 500} variant={compact ? 'body2' : 'body1'}>
              {entry.label}
              {entry.party ? (
                <Box component="span" sx={{ color: 'text.secondary', fontWeight: 400, ml: 0.75 }}>
                  {entry.party}
                </Box>
              ) : null}
            </Typography>
            <Typography color="text.secondary" variant="caption">
              {formatPercent(entry.percentage ?? 0)}
            </Typography>
          </Stack>
          <LinearProgress
            color={entry.is_leading ? 'primary' : 'secondary'}
            sx={{
              borderRadius: 999,
              height: compact ? 8 : 10,
              opacity: entry.is_leading ? 1 : 0.8,
            }}
            value={entry.percentage ?? 0}
            variant="determinate"
          />
        </Stack>
      ))}
    </Stack>
  );
}

export default TallyBars;
